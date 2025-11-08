"""TDD Green Phase: GeneratePlanUseCase 実装

設計関心事:
- 単一責任の原則: 計画生成のみを責務とする
- 依存性逆転の原則: LLMRepositoryインターフェースに依存
- テスト容易性: 外部依存を注入で受け取る
- 関心の分離: ビジネスロジックと外部サービスを分離
"""

from src.domain.entities import Plan
from src.domain.repositories.llm_repository import LLMRepository
from src.llms.load_template import load_template


class GeneratePlanUseCase:
    """計画生成ユースケース

    データ情報とユーザー要求を基に、分析計画を生成する。
    Clean Architectureの原則に従い、外部依存（LLM）はリポジトリを通じて抽象化。

    設計原則:
    - 単一責任: 計画生成のビジネスロジックのみ
    - 依存性逆転: 具象LLM実装ではなくインターフェースに依存
    - テスト容易性: モック可能なリポジトリ注入
    """

    def __init__(self, llm_repository: LLMRepository) -> None:
        """依存性注入によるLLMRepositoryの設定

        Args:
            llm_repository: LLM操作を抽象化したリポジトリ

        """
        self._llm_repository = llm_repository

    def execute(
        self,
        data_info: str,
        user_request: str,
        model: str = "gpt-4o-mini-2024-07-18",
        template_file: str = "src/prompts/generate_plan.jinja",
    ) -> Plan:
        """計画生成を実行

        Args:
            data_info: データの説明（CSV構造など）
            user_request: ユーザーの分析要求
            model: 使用するLLMモデル名
            template_file: プロンプトテンプレートのパス

        Returns:
            Plan: 生成された分析計画

        Raises:
            Exception: LLM呼び出しが失敗した場合

        設計判断:
        - テンプレート処理はユースケース内で実行（YAGNI原則）
        - モデル名はパラメータ化（設定可能性）
        - エラーハンドリングは呼び出し元に委譲（関心の分離）

        """
        # 1. プロンプトテンプレートの読み込みと展開
        messages = self._build_messages(data_info, user_request, template_file)

        # 2. LLMを通じた計画生成
        response = self._llm_repository.generate(
            messages=messages,
            model=model,
            response_format=Plan,
        )

        # 3. LLMResponseからPlanエンティティを抽出
        if hasattr(response, "content") and isinstance(response.content, Plan):
            return response.content
        # フォールバック: responseがPlanの場合はそのまま返す
        return response if isinstance(response, Plan) else response

    def _build_messages(
        self,
        data_info: str,
        user_request: str,
        template_file: str,
    ) -> list[dict[str, str]]:
        """LLM用のメッセージを構築

        Args:
            data_info: データ情報
            user_request: ユーザー要求
            template_file: テンプレートファイルパス

        Returns:
            List[Dict[str, str]]: LLM用メッセージリスト

        命名根拠:
        - _build_messages: メッセージ構築の意図が明確
        - プライベートメソッド: 外部から呼び出し不要

        """
        # テンプレート読み込み（既存実装を踏襲）
        template = load_template(template_file)
        system_message = template.render(data_info=data_info)

        # メッセージ構築（OpenAI Chat API形式）
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"タスク要求: {user_request}"},
        ]
