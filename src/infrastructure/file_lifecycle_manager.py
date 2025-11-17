"""ファイルライフサイクル管理インフラストラクチャ

Clean Architecture準拠のファイル管理サービス。
プレゼンテーション層とアプリケーション層の両方から使用可能。
"""

import time
from pathlib import Path
from typing import Set


class FileLifecycleManager:
    """ファイルライフサイクル管理サービス
    
    設計原則:
    - Clean Architecture: インフラストラクチャ層として独立
    - 単一責任: ファイルライフサイクル管理のみ
    - セキュリティ: 追跡されたファイルのみ削除許可
    - 依存性注入: 外部ライブラリへの依存なし
    """
    
    def __init__(self) -> None:
        """コンストラクタ."""
        # セッション毎の一時ファイル追跡
        self._temp_files_by_session: dict[str, Set[Path]] = {}
        
    def track_temp_file(self, session_id: str, file_path: str | Path) -> None:
        """一時ファイルを追跡対象に追加
        
        Args:
            session_id: セッションID
            file_path: 追跡するファイルパス
        """
        file_path = Path(file_path).resolve()
        
        if session_id not in self._temp_files_by_session:
            self._temp_files_by_session[session_id] = set()
            
        self._temp_files_by_session[session_id].add(file_path)
        
    def cleanup_session_files(self, session_id: str) -> None:
        """セッション関連の一時ファイルをクリーンアップ
        
        TDD Green: セキュリティ問題解決
        - 追跡されたファイルのみ削除
        - 既存データファイルは保護
        
        Args:
            session_id: クリーンアップ対象のセッションID
        """
        if session_id not in self._temp_files_by_session:
            return
            
        temp_files = self._temp_files_by_session[session_id]
        
        for file_path in temp_files.copy():
            try:
                if file_path.exists() and file_path.is_file():
                    file_path.unlink()
                    # 成功した場合は追跡から削除
                    temp_files.discard(file_path)
            except (OSError, PermissionError):
                # ファイル削除失敗は無視（ログなし）
                pass
                
        # セッション完了時に追跡データをクリア
        if not temp_files:  # 全ファイルが削除された場合
            del self._temp_files_by_session[session_id]
            
    def cleanup_all_temp_files(self) -> None:
        """すべての一時ファイルをクリーンアップ
        
        アプリケーション終了時などに使用
        """
        for session_id in list(self._temp_files_by_session.keys()):
            self.cleanup_session_files(session_id)

    def is_tracked_file(self, file_path: str | Path) -> bool:
        """現在追跡中の一時ファイルかどうかを判定

        Args:
            file_path: 判定対象のファイルパス

        Returns:
            bool: 追跡中の場合True
        """
        candidate = Path(file_path).resolve()

        for temp_files in self._temp_files_by_session.values():
            if candidate in temp_files:
                return True

        return False


# シングルトンインスタンス（アプリケーション全体で共有）
_global_file_manager = FileLifecycleManager()


def get_file_lifecycle_manager() -> FileLifecycleManager:
    """グローバルファイルライフサイクルマネージャを取得
    
    Returns:
        FileLifecycleManager: ファイルライフサイクル管理インスタンス
    """
    return _global_file_manager
