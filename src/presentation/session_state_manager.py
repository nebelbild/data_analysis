"""セッション状態管理モジュール.

TDD Blue Phase: クリーンアーキテクチャによる状態管理の分離

設計原則:
- 単一責任原則 (SRP): セッション状態の管理のみ
- 依存性逆転 (DIP): Streamlitの詳細に依存しない抽象化
- 型安全性: Ultracite基準での明示的型定義
- テスト容易性: 状態管理ロジックの分離
"""

from typing import Any
from uuid import uuid4

import streamlit as st


# Ultracite基準: 型エイリアス定義
SessionStateKey = str
SessionStateValue = Any
UploadedFile = Any


class SessionStateManager:
    """セッション状態管理クラス

    設計判断:
    - カプセル化: セッション状態操作を一箇所に集約
    - 型安全性: メソッドごとに適切な型ヒント
    - テスト容易性: Streamlit依存を抽象化
    - 保守性: 状態管理ロジックの一元化
    """

    @staticmethod
    def initialize_core_states() -> None:
        """コアセッション状態の初期化

        責務:
        - 基本的なセッション状態の設定
        - アプリケーション全体で共通の状態管理
        """
        if "session_id" not in st.session_state:
            st.session_state["session_id"] = str(uuid4())

        if "job_running" not in st.session_state:
            st.session_state["job_running"] = False

        if "selected_file_path" not in st.session_state:
            st.session_state["selected_file_path"] = None

        if "analysis_result" not in st.session_state:
            st.session_state["analysis_result"] = None

    @staticmethod
    def initialize_message_states() -> None:
        """メッセージ履歴状態の初期化

        責務:
        - チャット機能に関連する状態管理
        - ユーザーとアシスタントのメッセージ履歴
        """
        if "user_messages" not in st.session_state:
            st.session_state["user_messages"] = []

        if "assistant_messages" not in st.session_state:
            st.session_state["assistant_messages"] = []

    @staticmethod
    def initialize_file_states() -> None:
        """ファイル関連状態の初期化

        責務:
        - ファイルアップロード機能の状態管理
        - ファイルモード切り替え状態
        """
        if "uploaded_file" not in st.session_state:
            st.session_state["uploaded_file"] = None

        if "uploaded_file_name" not in st.session_state:
            st.session_state["uploaded_file_name"] = None

        if "file_mode" not in st.session_state:
            st.session_state["file_mode"] = False

    @staticmethod
    def get_uploaded_file() -> UploadedFile | None:
        """アップロード済みファイルの取得

        Returns:
            Optional[UploadedFile]: アップロード済みファイル、未設定の場合None

        """
        return st.session_state.get("uploaded_file", None)

    @staticmethod
    def set_uploaded_file(uploaded_file: UploadedFile | None) -> None:
        """アップロードファイルの設定

        Args:
            uploaded_file: 設定するファイルオブジェクト

        """
        st.session_state["uploaded_file"] = uploaded_file

    @staticmethod
    def get_file_mode() -> bool:
        """ファイルモード状態の取得

        Returns:
            bool: ファイルモードの場合True

        """
        return st.session_state.get("file_mode", False)

    @staticmethod
    def set_file_mode(file_mode: bool) -> None:
        """ファイルモード状態の設定

        Args:
            file_mode: 設定するファイルモード状態

        """
        st.session_state["file_mode"] = file_mode

    @staticmethod
    def get_selected_file_path() -> str | None:
        """選択済みファイルパスの取得

        Returns:
            Optional[str]: 選択済みファイルパス

        """
        return st.session_state.get("selected_file_path", None)

    @staticmethod
    def set_selected_file_path(file_path: str | None) -> None:
        """選択済みファイルパスの設定

        Args:
            file_path: 設定するファイルパス

        """
        st.session_state["selected_file_path"] = file_path


def initialize_all_session_states() -> None:
    """全セッション状態の初期化

    TDD Blue Phase: 責務分離による保守性向上

    設計判断:
    - ファサードパターン: 複数の初期化処理を統合
    - 単一エントリーポイント: 全状態初期化の一元化
    - 拡張性: 新しい状態カテゴリの追加が容易
    """
    SessionStateManager.initialize_core_states()
    SessionStateManager.initialize_message_states()
    SessionStateManager.initialize_file_states()
