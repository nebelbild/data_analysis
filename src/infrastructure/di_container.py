"""TDD Green Phase: DIContainer 実装

t-wadaさんのTDD原則: テストが通る最小限の実装

設計関心事:
- 依存性注入（DI）: リポジトリインスタンスの一元管理
- 設定管理: 環境変数からの設定読み込み
- キャッシング: リソース効率のためのインスタンス再利用
- テスト容易性: リセット機能の提供
"""

import os
from dotenv import load_dotenv

from src.domain.repositories.sandbox_repository import SandboxRepository
from src.domain.repositories.llm_repository import LLMRepository
from src.infrastructure.repositories.jupyter_sandbox_repository import (
    JupyterSandboxRepository,
)

# .envファイルを読み込み
load_dotenv()


class DIContainer:
    """依存性注入コンテナ

    設計原則:
    - 単一責任の原則（SRP）: リポジトリのインスタンス化のみを責務とする
    - 開放閉鎖の原則（OCP）: 新しいリポジトリ実装を追加可能
    - 依存性逆転の原則（DIP）: インターフェースを返す

    使用方法:
        ```python
        container = DIContainer()
        sandbox_repo = container.get_sandbox_repository()
        llm_repo = container.get_llm_repository()
        ```

    テスト時:
        ```python
        container = DIContainer(use_mock=True)
        # テスト実行
        container.reset()  # 次のテストのためにクリーンアップ
        ```
    """

    def __init__(self):
        """コンストラクタ

        初期化時にはインスタンスを作成せず、
        最初のget_*呼び出し時に遅延初期化（Lazy Initialization）
        .envファイルから環境変数を自動読み込み
        """
        self._sandbox_repository: SandboxRepository | None = None
        self._llm_repository: LLMRepository | None = None

    def get_sandbox_repository(self, timeout: int | None = None) -> SandboxRepository:
        """SandboxRepositoryのインスタンスを取得

        Args:
            timeout: サンドボックスのタイムアウト時間（秒）
                    Noneの場合は環境変数SANDBOX_TIMEOUTまたはデフォルト600秒

        Returns:
            SandboxRepository: サンドボックスリポジトリのインスタンス

        実装詳細:
        - キャッシング: 同じインスタンスを再利用
        - 環境変数対応: SANDBOX_TIMEOUTから読み込み
        - デフォルト値: 600秒

        """
        if self._sandbox_repository is None:
            # タイムアウト値の決定: 引数 > 環境変数 > デフォルト
            if timeout is None:
                timeout = int(os.environ.get("SANDBOX_TIMEOUT", "600"))

            self._sandbox_repository = JupyterSandboxRepository()
            # 注意: create()はここでは呼ばない（使用側で呼ぶ）

        return self._sandbox_repository

    def get_llm_repository(
        self, api_key: str | None = None, endpoint: str | None = None
    ) -> LLMRepository:
        """LLMRepositoryのインスタンスを取得

        Args:
            api_key: Azure OpenAI APIキー
                    Noneの場合は環境変数AZURE_OPENAI_API_KEYから読み込み
            endpoint: Azure OpenAIエンドポイント
                     Noneの場合は環境変数AZURE_OPENAI_ENDPOINTから読み込み

        Returns:
            LLMRepository: LLMリポジトリのインスタンス

        Raises:
            ValueError: APIキーまたはエンドポイントが提供されず、環境変数も設定されていない場合

        実装詳細:
        - キャッシング: 同じインスタンスを再利用
        - 環境変数対応: AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINTから読み込み
        - Azure OpenAI対応: リソースグループrg-1のactivarch-test-genpptx使用
        - セキュリティ: APIキーのハードコードを避ける

        """
        if self._llm_repository is None:
            # Azure OpenAI実装を使用
            from src.infrastructure.repositories.openai_llm_repository import (
                OpenAILLMRepository,
            )

            self._llm_repository = OpenAILLMRepository(
                api_key=api_key, endpoint=endpoint
            )

        return self._llm_repository

    def get_describe_dataframe_use_case(self) -> "DescribeDataframeUseCase":
        """DescribeDataframeUseCaseのインスタンスを取得

        Returns:
            DescribeDataframeUseCase: データフレーム記述ユースケースのインスタンス

        """
        from src.application.use_cases.describe_dataframe import (
            DescribeDataframeUseCase,
        )

        return DescribeDataframeUseCase()

    def get_generate_plan_use_case(self) -> "GeneratePlanUseCase":
        """GeneratePlanUseCaseのインスタンスを取得

        Returns:
            GeneratePlanUseCase: プラン生成ユースケースのインスタンス

        Week 10-12実装: LangGraph脱却のためのユースケース統合

        """
        from src.application.use_cases.generate_plan import GeneratePlanUseCase

        return GeneratePlanUseCase(self.get_llm_repository())

    def get_generate_code_use_case(self) -> "GenerateCodeUseCase":
        """GenerateCodeUseCaseのインスタンスを取得

        Returns:
            GenerateCodeUseCase: コード生成ユースケースのインスタンス

        Week 10-12実装: LangGraph脱却のためのユースケース統合

        """
        from src.application.use_cases.generate_code import GenerateCodeUseCase

        llm_repository = self.get_llm_repository()
        return GenerateCodeUseCase(llm_repository)

    def get_generate_review_use_case(self) -> "GenerateReviewUseCase":
        """GenerateReviewUseCase のインスタンスを取得

        Returns:
            GenerateReviewUseCase: レビュー生成ユースケースのインスタンス

        Week 10-12実装: LangGraph脱却のためのユースケース統合

        """
        from src.application.use_cases.generate_review import GenerateReviewUseCase

        llm_repository = self.get_llm_repository()
        return GenerateReviewUseCase(llm_repository)

    def get_execute_code_use_case(self) -> "ExecuteCodeUseCase":
        """ExecuteCodeUseCase のインスタンスを取得

        Returns:
            ExecuteCodeUseCase: コード実行ユースケースのインスタンス

        Week 10-12実装: LangGraph脱却のためのユースケース統合

        """
        from src.application.use_cases.execute_code import ExecuteCodeUseCase

        sandbox_repository = self.get_sandbox_repository()
        return ExecuteCodeUseCase(sandbox_repository)

    def get_generate_report_use_case(self) -> "GenerateReportUseCase":
        """GenerateReportUseCaseインスタンスを取得

        Returns:
            GenerateReportUseCase: 設定済みのGenerateReportUseCaseインスタンス

        Week 10-12実装: LangGraph脱却のためのユースケース統合

        """
        from src.application.use_cases.generate_report import GenerateReportUseCase

        return GenerateReportUseCase(self.get_llm_repository())

    def get_report_renderer(self, output_format: str = "html") -> "ReportRenderer":
        """ReportRendererインスタンスを取得

        Args:
            output_format: 出力形式（"html" or "markdown"）

        Returns:
            ReportRenderer: 指定された形式のレンダラーインスタンス

        """
        from src.infrastructure.renderers.html_renderer import HTMLRenderer
        from src.infrastructure.renderers.markdown_renderer import MarkdownRenderer

        if output_format.lower() == "html":
            return HTMLRenderer()
        if output_format.lower() == "markdown" or output_format.lower() == "md":
            return MarkdownRenderer()
        raise ValueError(f"Unsupported output format: {output_format}")

    def get_generate_report_use_case_with_renderer(
        self,
        output_format: str = "html",
    ) -> "GenerateReportUseCase":
        """レンダラー付きGenerateReportUseCaseインスタンスを取得

        Args:
            output_format: 出力形式（"html" or "markdown"）

        Returns:
            GenerateReportUseCase: レンダラー設定済みのGenerateReportUseCaseインスタンス

        """
        from src.application.use_cases.generate_report import GenerateReportUseCase

        return GenerateReportUseCase(
            self.get_llm_repository(),
            self.get_report_renderer(output_format),
        )

    def reset(self) -> None:
        """キャッシュをリセット

        使用ケース:
        - テスト間でのクリーンアップ
        - 設定変更後の再初期化

        実装詳細:
        - すべてのキャッシュされたインスタンスをクリア
        - 次回のget_*呼び出し時に新しいインスタンスを生成
        """
        self._sandbox_repository = None
        self._llm_repository = None
