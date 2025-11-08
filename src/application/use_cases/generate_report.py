"""レポート生成ユースケース"""

from typing import List, Dict, Any, Optional
from src.domain.repositories.llm_repository import LLMRepository
from src.domain.entities.data_thread import DataThread
from src.llms.llm_response import LLMResponse
from src.llms.load_template import load_template
from src.infrastructure.renderers.renderer_interface import ReportRenderer


class GenerateReportUseCase:
    """レポート生成ユースケース
    
    データ情報とユーザーリクエスト、実行済みDataThreadを基に
    分析レポートを生成する
    """

    def __init__(self, llm_repository: LLMRepository, renderer: Optional[ReportRenderer] = None):
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
        process_data_threads: Optional[List[DataThread]] = None,
        model: str = "gpt-4o-mini-2024-07-18",
        template_file: str = "src/prompts/generate_report.jinja",
        output_dir: Optional[str] = None,
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
        system_message = template.render(data_info=data_info)

        # 基本メッセージの構築
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"タスク要求: {user_request}"},
        ]

        # DataThreadの処理とメッセージ追加
        for data_thread in process_data_threads:
            thread_messages = self._build_thread_messages(data_thread)
            # thread_messagesを文字列形式に変換してメッセージに追加
            content_text = self._convert_thread_messages_to_text(thread_messages)
            messages.append({"role": "user", "content": content_text})

        # レポート生成
        response = self.llm_repository.generate(messages, model=model)
        
        # Markdownコードブロックを削除（```markdown ... ``` の除去）
        cleaned_response = response
        # レスポンスから実際のコンテンツを抽出
        response_content = response.content if hasattr(response, 'content') else str(response)
        
        if isinstance(response_content, str):
            # markdownコードブロックのみを削除（先頭と末尾のペアで削除）
            # ただし他のコードブロック（```python など）は保持
            import re
            if response_content.strip().startswith('```markdown') and response_content.strip().endswith('```'):
                # 先頭の```markdownと末尾の```を削除
                cleaned_response = re.sub(r'^```markdown\s*\n', '', response_content)
                cleaned_response = re.sub(r'\n```\s*$', '', cleaned_response)
            else:
                cleaned_response = response_content
        else:
            cleaned_response = str(response_content)
        
        # レンダラーが指定されており、出力ディレクトリが指定されている場合はレンダリング
        if self.renderer is not None and output_dir is not None:
            self.renderer.render(cleaned_response, output_dir)
        
        return response

    def _build_thread_messages(self, data_thread: DataThread) -> List[Dict[str, Any]]:
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
                image_filename = f"{data_thread.process_id}_{data_thread.thread_id}_{i}.png"
                user_contents.extend([
                    {
                        "type": "input_text",
                        "text": f'画像ファイル名: "{image_filename}" (レポートでは ![グラフ]({image_filename}) と記載してください)',
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{result.get('data', '')}",
                    },
                ])
            elif result.get("type") == "text":
                # テキスト結果の処理
                user_contents.append({
                    "type": "text",
                    "text": f"実行結果: {result.get('data', '')}",
                })

        return user_contents

    def _convert_thread_messages_to_text(self, thread_messages: List[Dict[str, Any]]) -> str:
        """DataThreadメッセージをテキスト形式に変換
        
        Args:
            thread_messages: DataThreadから構築されたメッセージリスト
            
        Returns:
            str: テキスト形式のメッセージ
        """
        text_parts = []
        for message in thread_messages:
            if message.get("type") == "input_text":
                text_parts.append(message["text"])
            elif message.get("type") == "text":
                text_parts.append(message["text"])
            elif message.get("type") == "input_image":
                # 画像URLを完全な形式でテキストに含める（テスト要件に合わせる）
                text_parts.append(f"[画像: {message['image_url']}]")
        
        return "\n".join(text_parts)