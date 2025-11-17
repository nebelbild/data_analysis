"""レポート生成ユースケース"""

from pathlib import Path
from typing import Any
from src.domain.repositories.llm_repository import LLMRepository
from src.domain.entities.data_thread import DataThread
from src.domain.entities.llm_response import LLMResponse
from src.infrastructure.template_loader import load_template
from src.infrastructure.renderers.renderer_interface import ReportRenderer


class GenerateReportUseCase:
    """レポート生成ユースケース

    データ情報とユーザーリクエスト、実行済みDataThreadを基に
    分析レポートを生成する
    """

    def __init__(
        self,
        llm_repository: LLMRepository,
        renderer: ReportRenderer | None = None,
    ):
        """初期化

        Args:
            llm_repository: LLMリポジトリ
            renderer: レポートレンダラー（オプション）

        """
        self.llm_repository = llm_repository
        self.renderer = renderer

    def execute(
        self,
        data_info: str,
        user_request: str,
        process_data_threads: list[DataThread] | None = None,
        model: str = "gpt-4o-mini-2024-07-18",
        template_file: str = "src/prompts/generate_report.jinja",
        output_dir: str | None = None,
    ) -> LLMResponse:
        """レポート生成の実行

        Args:
            data_info: データ情報
            user_request: ユーザーリクエスト
            process_data_threads: 実行済みDataThreadリスト
            model: 使用するLLMモデル
            template_file: テンプレートファイルパス
            output_dir: 出力ディレクトリパス（レンダラー使用時）

        Returns:
            LLMResponse: 生成されたレポート

        """
        if process_data_threads is None:
            process_data_threads = []

        # テンプレートの読み込み
        template = load_template(template_file)

        # data_infoを制限（長すぎる場合は要約）
        max_data_info_length = 10000
        if len(data_info) > max_data_info_length:
            data_info = data_info[:max_data_info_length] + "...(省略)"

        system_message = template.render(data_info=data_info)

        # 基本メッセージの構築
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"タスク要求: {user_request}"},
        ]

        # DataThreadの処理とメッセージ追加（最大5スレッドまで制限）
        max_threads = 5
        for i, data_thread in enumerate(process_data_threads[:max_threads]):
            thread_messages = self._build_thread_messages(data_thread)
            # thread_messagesを文字列形式に変換してメッセージに追加
            content_text = self._convert_thread_messages_to_text(thread_messages)
            if content_text.strip():  # 空でない場合のみ追加
                messages.append(
                    {"role": "user", "content": f"実行結果 {i + 1}:\n{content_text}"},
                )

        # レポート生成
        response = self.llm_repository.generate(messages, model=model)

        # Markdownコードブロックを削除（```markdown ... ``` の除去）
        cleaned_response = response
        # レスポンスから実際のコンテンツを抽出
        response_content = (
            response.content if hasattr(response, "content") else str(response)
        )

        if isinstance(response_content, str):
            # markdownコードブロックのみを削除（先頭と末尾のペアで削除）
            # ただし他のコードブロック（```python など）は保持
            import re

            if response_content.strip().startswith(
                "```markdown",
            ) and response_content.strip().endswith("```"):
                # 先頭の```markdownと末尾の```を削除
                cleaned_response = re.sub(
                    r"^```markdown\s*\n",
                    "",
                    response_content,
                )
                cleaned_response = re.sub(
                    r"\n```\s*$",
                    "",
                    cleaned_response,
                )
            else:
                cleaned_response = response_content
        else:
            cleaned_response = str(response_content)

        # 生成済みの画像をMarkdownに追加して漏れを防ぐ
        enriched_markdown = self._append_missing_images(
            cleaned_response,
            process_data_threads,
        )

        # レンダラーが指定されており、出力ディレクトリが指定されている場合はレンダリング
        if self.renderer is not None and output_dir is not None:
            self.renderer.render(enriched_markdown, output_dir)

        if output_dir is not None:
            self._write_markdown(enriched_markdown, output_dir)

        return response

    def _build_thread_messages(self, data_thread: DataThread) -> list[dict[str, Any]]:
        """DataThreadからメッセージ構築

        Args:
            data_thread: 処理済みDataThread

        Returns:
            List[Dict]: LLM用メッセージリスト

        """
        user_contents = [
            {"type": "input_text", "text": f"instruction: {data_thread.user_request}"},
            {"type": "input_text", "text": f"stdout: {data_thread.stdout}"},
            {"type": "input_text", "text": f"observation: {data_thread.observation}"},
        ]

        # 実行結果の処理
        for i, result in enumerate(data_thread.results):
            if result.get("type") == "image":
                # PNG画像の処理
                image_filename = (
                    f"{data_thread.process_id}_{data_thread.thread_id}_{i}.png"
                )
                image_data = result.get("data", "")
                user_contents.extend(
                    [
                        {
                            "type": "input_text",
                            "text": (
                                f'画像ファイル名: "{image_filename}" '
                                f'(レポートでは ![グラフ]({image_filename}) '
                                "と記載してください)"
                            ),
                        },
                        {
                            "type": "input_image",
                            "image_url": f"data:image/png;base64,{image_data}",
                        },
                    ],
                )
            elif result.get("type") == "text":
                # テキスト結果の処理
                user_contents.append(
                    {
                        "type": "text",
                        "text": f"実行結果: {result.get('data', '')}",
                    },
                )

        return user_contents

    def _convert_thread_messages_to_text(
        self,
        thread_messages: list[dict[str, Any]],
    ) -> str:
        """DataThreadメッセージをテキスト形式に変換

        Args:
            thread_messages: DataThreadから構築されたメッセージリスト

        Returns:
            str: テキスト形式のメッセージ

        """
        text_parts = []
        total_length = 0
        max_length = 8000  # 各スレッドのメッセージを制限（コンテキスト制限対策）

        for message in thread_messages:
            if message.get("type") == "input_text" or message.get("type") == "text":
                text = message["text"]
                # 長さ制限チェック
                if total_length + len(text) > max_length:
                    remaining_space = max_length - total_length
                    if remaining_space > 100:  # 最低限のスペースがある場合のみ追加
                        text = text[:remaining_space] + "...(省略)"
                        text_parts.append(text)
                    break
                text_parts.append(text)
                total_length += len(text)
            elif message.get("type") == "input_image":
                # 画像URLを完全な形式でテキストに含める（テスト要件に合わせる）
                image_text = f"[画像: {message['image_url']}]"
                if total_length + len(image_text) > max_length:
                    break
                text_parts.append(image_text)
                total_length += len(image_text)

        return "\n".join(text_parts)

    def _append_missing_images(
        self,
        markdown_text: str,
        process_data_threads: list[DataThread],
    ) -> str:
        """Markdownに含まれていない画像を追記する"""

        if not markdown_text:
            markdown_text = ""

        import re

        existing_references = {
            Path(match).name
            for match in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", markdown_text)
        }

        additional_lines: list[str] = []
        for data_thread in process_data_threads:
            image_paths = data_thread.pathes.get("images", [])
            for image_path in image_paths:
                image_name = Path(image_path).name
                if image_name in existing_references:
                    continue
                if not Path(image_path).exists():
                    continue
                if not additional_lines:
                    additional_lines.append("## 生成された可視化一覧\n")
                additional_lines.append(f"![{image_name}]({image_name})\n")
                existing_references.add(image_name)

        if additional_lines:
            if markdown_text and not markdown_text.endswith("\n"):
                markdown_text += "\n"
            markdown_text += "\n".join(additional_lines)

        return markdown_text

    def _write_markdown(self, markdown_text: str, output_dir: str) -> None:
        """生成したMarkdownをファイル出力する"""

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        target = output_path / "report.md"
        target.write_text(markdown_text, encoding="utf-8")
