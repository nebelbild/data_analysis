"""
TDD Green Phase: GenerateReviewUseCase 実装

設計関心事:
- 単一責任の原則: レビュー生成のみを責務とする
- 依存性逆転の原則: LLMRepositoryインターフェースに依存
- テスト容易性: 外部依存を注入で受け取る
- 関心の分離: ビジネスロジックと外部サービスを分離
- 複雑なビジネスルール: 実行結果の形式変換（PNG→image_url、テキスト→text）
- 条件分岐: has_resultsによるメッセージ構築の変更
"""

from typing import Any, Dict, List

from src.domain.entities import DataThread, Review
from src.domain.repositories.llm_repository import LLMRepository
from src.llms.load_template import load_template


class GenerateReviewUseCase:
    """
    レビュー生成ユースケース
    
    コード実行結果を基に、実行の成功/失敗、問題点、改善提案を含むレビューを生成する。
    実行結果の形式（画像、テキスト）に応じて適切にLLMに情報を渡す。
    
    設計原則:
    - 単一責任: レビュー生成のビジネスロジックのみ
    - 依存性逆転: 具象LLM実装ではなくインターフェースに依存
    - テスト容易性: モック可能なリポジトリ注入
    - 複雑な変換ルール: 実行結果の形式変換とメッセージ構築
    """

    def __init__(self, llm_repository: LLMRepository) -> None:
        """
        依存性注入によるLLMRepositoryの設定
        
        Args:
            llm_repository: LLM操作を抽象化したリポジトリ
        """
        self._llm_repository = llm_repository

    def execute(
        self,
        data_info: str,
        user_request: str,
        data_thread: DataThread,
        has_results: bool = False,
        remote_save_dir: str = "outputs/process_id/id",
        model: str = "gpt-4o-mini-2024-07-18",
        template_file: str = "src/prompts/generate_review.jinja",
    ) -> Review:
        """
        レビュー生成を実行
        
        Args:
            data_info: データの説明（CSV構造など）
            user_request: ユーザーのレビュー要求
            data_thread: 実行済みのデータスレッド（コード、結果を含む）
            has_results: 実行結果（画像、テキスト）が存在するか
            remote_save_dir: リモート保存ディレクトリ
            model: 使用するLLMモデル名
            template_file: プロンプトテンプレートのパス
            
        Returns:
            Review: 生成されたレビュー（観測結果、完了判定）
            
        Raises:
            Exception: LLM呼び出しが失敗した場合
            
        ビジネスルール:
        - 実行結果がある場合は、PNG画像とテキストを適切な形式で変換
        - コード、stdout、stderr、実行結果を全てレビュー対象として含める
        - フィードバック要求メッセージを最後に追加
        """
        # 1. メッセージ構築
        messages = self._build_review_messages(
            data_info=data_info,
            user_request=user_request,
            data_thread=data_thread,
            has_results=has_results,
            remote_save_dir=remote_save_dir,
            template_file=template_file,
        )

        # 3. LLMを通じたレビュー生成
        response = self._llm_repository.generate(
            messages=messages,
            model=model,
            response_format=Review,
        )

        # 4. LLMResponseからReviewエンティティを抽出
        if hasattr(response, 'content') and isinstance(response.content, Review):
            return response.content
        else:
            # フォールバック: responseがReviewの場合はそのまま返す
            return response if isinstance(response, Review) else response

    def _build_review_messages(
        self,
        data_info: str,
        user_request: str,
        data_thread: DataThread,
        has_results: bool,
        remote_save_dir: str,
        template_file: str,
    ) -> List[Dict[str, Any]]:
        """
        レビュー用のメッセージを構築
        
        Args:
            data_info: データ情報
            user_request: ユーザー要求
            data_thread: 実行済みデータスレッド
            has_results: 結果の有無
            remote_save_dir: 保存ディレクトリ
            template_file: テンプレートファイルパス
            
        Returns:
            List[Dict[str, Any]]: レビュー用メッセージリスト
            
        メッセージ構造:
        1. システム指示（テンプレートから生成）
        2. ユーザー要求
        3. 生成されたコード（assistantとして）
        4. 実行結果（has_resultsがTrueの場合のみ）
        5. 標準出力
        6. 標準エラー出力
        7. フィードバック要求
        """
        # テンプレート読み込み
        template = load_template(template_file)
        system_instruction = template.render(
            data_info=data_info,
            remote_save_dir=remote_save_dir,
        )

        # 基本メッセージの構築
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_request},
            {"role": "assistant", "content": data_thread.code or ""},
        ]

        # 実行結果の追加（条件付き）
        if has_results and data_thread.results:
            results_content = self._convert_results_for_llm(data_thread.results)
            # resultsをJSON文字列として追加（LLM互換形式）
            import json
            messages.append({"role": "system", "content": json.dumps(results_content)})

        # 実行ログの追加
        messages.extend([
            {"role": "system", "content": f"stdout: {data_thread.stdout or ''}"},
            {"role": "system", "content": f"stderr: {data_thread.stderr or ''}"},
        ])

        # フィードバック要求
        messages.append({
            "role": "user",
            "content": "実行結果に対するフィードバックを提供してください。",
        })

        return messages

    def _convert_results_for_llm(self, results: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        実行結果をLLM用の形式に変換
        
        Args:
            results: データスレッドの実行結果
            
        Returns:
            List[Dict[str, Any]]: LLM用に変換された結果
            
        変換ルール:
        - PNG画像: image_url形式（base64データURLとして）
        - テキスト: text形式（そのまま）
        
        命名根拠:
        - _convert_results_for_llm: LLM特有の形式変換の意図が明確
        - for_llm: LLM用の変換であることを明示
        """
        converted_results = []
        
        for result in results:
            if result.get("type") == "image":
                # PNG画像をimage_url形式に変換
                converted_results.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{result.get('data', '')}"
                    },
                })
            elif result.get("type") == "text":
                # テキスト結果
                converted_results.append({
                    "type": "text",
                    "text": result.get("data", ""),
                })
        
        return converted_results