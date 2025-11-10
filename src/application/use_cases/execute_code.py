"""TDD Green Phase: ExecuteCodeUseCase 実装

設計関心事:
- 単一責任の原則: コード実行のみを責務とする
- 依存性逆転の原則: SandboxRepositoryインターフェースに依存
- テスト容易性: 外部依存を注入で受け取る
- 関心の分離: ビジネスロジックと外部サービス（E2B）を分離
- データ変換: Sandbox結果からドメインエンティティへの変換
"""

from typing import Any

from src.domain.entities import DataThread
from src.domain.repositories.sandbox_repository import SandboxRepository


class ExecuteCodeUseCase:
    """コード実行ユースケース

    Pythonコードをサンドボックス環境で実行し、結果をDataThreadエンティティとして返す。
    実行結果、エラー情報、出力ログを含む完全な実行コンテキストを提供。

    設計原則:
    - 単一責任: コード実行のビジネスロジックのみ
    - 依存性逆転: 具象Sandbox実装ではなくインターフェースに依存
    - テスト容易性: モック可能なリポジトリ注入
    - データ変換: 外部形式からドメインモデルへの変換責務
    """

    def __init__(self, sandbox_repository: SandboxRepository) -> None:
        """依存性注入によるSandboxRepositoryの設定

        Args:
            sandbox_repository: サンドボックス操作を抽象化したリポジトリ

        """
        self._sandbox_repository = sandbox_repository

    def execute(
        self,
        process_id: str,
        thread_id: int,
        code: str,
        user_request: str | None = None,
        timeout: int = 1200,
    ) -> DataThread:
        """コード実行を実行

        Args:
            process_id: プロセス識別子
            thread_id: スレッド識別子
            code: 実行するPythonコード
            user_request: ユーザーの要求（省略可）
            timeout: 実行タイムアウト（秒）

        Returns:
            DataThread: 実行結果を含むデータスレッド

        Raises:
            Exception: サンドボックス実行が失敗した場合

        ビジネスルール:
        - コード実行はサンドボックス環境で安全に実行
        - 実行結果（画像、テキスト）を適切な形式で変換
        - エラー情報、標準出力、標準エラーを全て記録
        - 実行カウントをDataThreadのIDとして使用

        """
        # 0. サンドボックスが作成されていない場合は作成
        # Note: _sandbox_idへのアクセスは実装の詳細だが、サンドボックスの状態確認に必要
        if not hasattr(self._sandbox_repository, '_sandbox_id') or self._sandbox_repository._sandbox_id is None:  # noqa: SLF001
            print("[DEBUG] サンドボックスを作成中...")
            self._sandbox_repository.create(timeout=60)
            print("[DEBUG] サンドボックス作成完了")
        
        # 1. サンドボックスでコード実行
        execution_result = self._sandbox_repository.execute_code(
            code=code,
            timeout=timeout,
        )

        # 2. 実行結果をドメインエンティティに変換
        return self._convert_to_data_thread(
            execution_result=execution_result,
            process_id=process_id,
            thread_id=thread_id,
            code=code,
            user_request=user_request,
        )

    def _convert_to_data_thread(
        self,
        execution_result: Any,
        process_id: str,
        thread_id: int,
        code: str,
        user_request: str | None,
    ) -> DataThread:
        """サンドボックス実行結果をDataThreadエンティティに変換

        Args:
            execution_result: サンドボックスの実行結果
            process_id: プロセス識別子
            thread_id: スレッド識別子
            code: 実行されたコード
            user_request: ユーザー要求

        Returns:
            DataThread: 変換されたデータスレッド

        変換ルール:
        1. execution_countをDataThread.idとして使用
        2. 結果配列の各要素をタイプ別に変換（PNG/テキスト）
        3. エラー情報のtracebackを抽出
        4. stdout/stderrリストを文字列に結合

        命名根拠:
        - _convert_to_data_thread: データ変換の意図が明確
        - プライベートメソッド: 内部データ変換処理

        """
        # 実行結果の変換（PNG画像とテキスト出力）
        results = self._convert_execution_results(execution_result["results"])

        # エラー情報の抽出
        error_info = None
        if execution_result.get("error"):
            error_info = execution_result["error"].get("traceback")

        # 標準出力/エラーの結合
        stdout = "".join(execution_result["logs"]["stdout"]).strip()
        stderr = "".join(execution_result["logs"]["stderr"]).strip()

        return DataThread(
            id=execution_result["execution_count"],
            process_id=process_id,
            thread_id=thread_id,
            user_request=user_request,
            code=code,
            error=error_info,
            stderr=stderr,
            stdout=stdout,
            results=results,
        )

    def _convert_execution_results(
        self,
        raw_results: list[Any],
    ) -> list[dict[str, str]]:
        """実行結果を標準形式に変換

        Args:
            raw_results: サンドボックスからの生の実行結果

        Returns:
            List[Dict[str, str]]: 変換された結果リスト

        変換ルール:
        - PNG画像: {"type": "png", "content": "base64_data"}
        - テキスト: {"type": "raw", "content": "text_content"}

        命名根拠:
        - _convert_execution_results: 結果変換の意図が明確
        - raw_results: サンドボックスの生データを表現

        """
        converted_results = []

        for result in raw_results:
            # Jupyter sandboxは既に辞書形式で返す
            if isinstance(result, dict):
                # そのまま追加（type と content キーを持つ辞書）
                # ただし、typeフィールドを統一（"png" → "image", "raw" → "text"）
                result_type = result.get("type")
                if result_type == "png":
                    converted_results.append(
                        {
                            "type": "image",
                            "data": result.get("content", ""),
                        },
                    )
                elif result_type == "raw":
                    converted_results.append(
                        {
                            "type": "text",
                            "data": result.get("content", ""),
                        },
                    )
            elif hasattr(result, "png") and result.png:
                # オブジェクト形式の場合（E2B形式）
                converted_results.append(
                    {
                        "type": "image",
                        "data": result.png,
                    },
                )
            elif hasattr(result, "text"):
                # テキスト結果
                converted_results.append(
                    {
                        "type": "text",
                        "data": result.text,
                    },
                )

        return converted_results
