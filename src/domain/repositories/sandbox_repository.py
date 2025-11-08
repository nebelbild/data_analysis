"""
TDD Green Phase: SandboxRepository インターフェース実装

t-wadaさんのTDD原則: テストが通る最小限の実装

設計関心事:
- 依存性逆転の原則（DIP）: 抽象に依存し、具象に依存しない
- インターフェース分離の原則（ISP）: クライアント固有の小さなインターフェース
- リスコフの置換原則（LSP）: サブタイプは基本型と置換可能
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class SandboxRepository(ABC):
    """
    サンドボックス実行環境の抽象リポジトリ
    
    このインターフェースは、コード実行環境（E2B, Docker, etc.）の
    具体的な実装から分離し、ビジネスロジックが実装詳細に依存しないようにする。
    
    設計原則:
    - 単一責任の原則（SRP）: サンドボックス操作のみを責務とする
    - 開放閉鎖の原則（OCP）: 新しいサンドボックス実装を追加可能（拡張に開いている）
    """

    @abstractmethod
    def create(self, timeout: int = 600) -> str:
        """
        新しいサンドボックスを作成
        
        Args:
            timeout: タイムアウト時間（秒）
            
        Returns:
            str: 作成されたサンドボックスのID
            
        命名根拠:
        - create: サンドボックスの生成を明確に表現
        - 戻り値はstr型のID: 参照用の一意識別子
        """
        ...

    @abstractmethod
    def connect(self, sandbox_id: str) -> None:
        """
        既存のサンドボックスに接続
        
        Args:
            sandbox_id: 接続先サンドボックスのID
            
        命名根拠:
        - connect: 既存リソースへの接続を明確に表現
        - sandbox_id: サンドボックスの一意識別子
        """
        ...

    @abstractmethod
    def execute_code(self, code: str, timeout: int = 1200) -> Dict[str, Any]:
        """
        サンドボックス内でPythonコードを実行
        
        Args:
            code: 実行するPythonコード
            timeout: 実行タイムアウト（秒、デフォルト: 1200秒）
            
        Returns:
            Dict[str, Any]: 実行結果
                - stdout: 標準出力
                - stderr: 標準エラー出力
                - exit_code: 終了コード
                - error: エラー情報（あれば）
                
        命名根拠:
        - execute_code: コード実行の意図が明確
        - timeout: 実行時間制限を明示
        - 戻り値は辞書: 実行結果の構造化データ
        """
        ...

    @abstractmethod
    def upload_file(self, file_path: str, content: bytes) -> None:
        """
        サンドボックスにファイルをアップロード
        
        Args:
            file_path: アップロード先のパス
            content: ファイルの内容（バイト列）
            
        命名根拠:
        - upload_file: ファイルアップロードの意図が明確
        - content: bytes型でバイナリデータをサポート
        """
        ...

    @abstractmethod
    def kill(self) -> None:
        """
        サンドボックスを停止・削除
        
        リソース管理:
        - 明示的なクリーンアップメソッド
        - 使用後は必ず呼び出すべき
        
        命名根拠:
        - kill: プロセス停止の一般的な用語
        - 戻り値なし: 副作用のみを持つ
        """
        ...
