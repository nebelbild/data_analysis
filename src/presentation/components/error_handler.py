"""Error Handler Component.

エラー処理を統一的に行うコンポーネント

設計原則:
- 単一責任の原則: エラー処理のみ
- 関心の分離: エラー分類、表示、ログ記録を分離
- テスト容易性: 純粋な関数
"""

from typing import Literal

import streamlit as st
from loguru import logger


ErrorType = Literal["user_error", "system_error", "critical_error"]


def classify_error(error_msg: str) -> ErrorType:
    """エラーメッセージを分類する.

    Args:
        error_msg: エラーメッセージ

    Returns:
        ErrorType: エラータイプ

    """
    error_msg_lower = error_msg.lower()

    # ユーザーエラーのパターン
    user_error_patterns = [
        "ファイルが見つかりません",
        "file not found",
        "ファイルが存在しません",
        "無効なファイル",
        "invalid file",
        "パスが無効",
        "invalid path",
    ]

    # 致命的エラーのパターン
    critical_error_patterns = [
        "メモリ不足",
        "memory",
        "out of memory",
        "disk full",
        "ディスク容量不足",
    ]

    # ユーザーエラーチェック
    for pattern in user_error_patterns:
        if pattern in error_msg_lower:
            return "user_error"

    # 致命的エラーチェック
    for pattern in critical_error_patterns:
        if pattern in error_msg_lower:
            return "critical_error"

    # デフォルトはシステムエラー
    return "system_error"


def display_error(error_msg: str, error_type: ErrorType) -> None:
    """エラーを表示する.

    Args:
        error_msg: エラーメッセージ
        error_type: エラータイプ

    """
    if error_type == "user_error":
        st.warning(f"⚠️ {error_msg}")
    elif error_type == "system_error":
        st.error(f"❌ {error_msg}")
    elif error_type == "critical_error":
        st.error(f"🚨 致命的エラー: {error_msg}")
        with st.expander("詳細情報"):
            st.markdown(
                """
                システムリソースが不足しています。
                以下の対処を試してください：
                - アプリケーションを再起動
                - 不要なプロセスを終了
                - システム管理者に連絡
                """,
            )


def show_recovery_guidance(error_type: ErrorType, _error_msg: str) -> None:
    """復旧手順を表示する.

    Args:
        error_type: エラータイプ
        _error_msg: エラーメッセージ（将来の拡張用）

    """
    if error_type == "user_error":
        st.info(
            """
            📋 **確認事項**
            - ファイルパスが正しいか確認してください
            - ファイルが存在するか確認してください
            - ファイル形式が対応しているか確認してください（CSV, Excel, TSV）
            """,
        )
    elif error_type == "system_error":
        st.info(
            """
            🔄 **復旧手順**
            - しばらく待ってから再試行してください
            - ネットワーク接続を確認してください
            - 問題が続く場合は管理者に連絡してください
            """,
        )
    elif error_type == "critical_error":
        st.info(
            """
            🚨 **緊急対応**
            - アプリケーションを再起動してください
            - システムリソースを確認してください
            - システム管理者に連絡してください
            """,
        )
    else:
        st.info(
            """
            ℹ️ **一般的な対処**
            - エラーメッセージを確認してください
            - 再試行してください
            - 問題が続く場合はサポートに連絡してください
            """,
        )


def log_error(error_msg: str, error_type: ErrorType, session_id: str | None = None) -> None:
    """エラーをログに記録する.

    Args:
        error_msg: エラーメッセージ
        error_type: エラータイプ
        session_id: セッションID（オプション）

    """
    log_context = f"[Session: {session_id}] " if session_id else ""
    full_message = f"{log_context}{error_msg}"

    if error_type == "user_error":
        logger.warning(full_message)
    elif error_type == "system_error":
        logger.error(full_message)
    elif error_type == "critical_error":
        logger.critical(full_message)


def handle_error(error_msg: str, session_id: str | None = None) -> None:
    """エラーを統一的に処理する.

    Args:
        error_msg: エラーメッセージ
        session_id: セッションID（オプション）

    """
    # エラー分類
    error_type = classify_error(error_msg)

    # エラー表示
    display_error(error_msg, error_type)

    # 復旧手順表示
    show_recovery_guidance(error_type, error_msg)

    # ログ記録
    log_error(error_msg, error_type, session_id)
