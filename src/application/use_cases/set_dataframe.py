"""データフレーム設定ユースケース"""

import io
from typing import Dict, Any
from src.domain.repositories.sandbox_repository import SandboxRepository


class SetDataframeUseCase:
    """データフレーム設定ユースケース
    
    CSVファイルをサンドボックス環境にアップロードし、
    pandasのDataFrameとして読み込むコードを実行する
    """

    def __init__(self, sandbox_repository: SandboxRepository):
        """初期化
        
        Args:
            sandbox_repository: サンドボックスリポジトリ
        """
        self.sandbox_repository = sandbox_repository

    def execute(
        self,
        file_object: io.BytesIO,
        timeout: int = 1200,
        remote_data_path: str = "/home/data.csv",
    ) -> Dict[str, Any]:
        """データフレーム設定の実行
        
        Args:
            file_object: CSVファイルのバイトストリーム
            timeout: コード実行のタイムアウト（秒）
            remote_data_path: サンドボックス内のファイルパス
            
        Returns:
            Dict[str, Any]: コード実行結果
        """
        # CSVファイルをサンドボックスにアップロード
        file_content = file_object.getvalue()
        self.sandbox_repository.upload_file(remote_data_path, file_content)
        
        # pandasでDataFrameを読み込むコードを実行
        code = f"import pandas as pd; df = pd.read_csv('{remote_data_path}')"
        return self.sandbox_repository.execute_code(code, timeout=timeout)