"""Chat History Component

チャット履歴を表示するコンポーネント

設計原則:
- 単一責任の原則: チャット履歴表示のみ
- 関心の分離: UI表示とデータ管理の分離
- テスト容易性: 純粋な表示関数
"""

from typing import Any

import streamlit as st


def render_chat_history(
    user_messages: list[str | dict[str, Any]],
    assistant_messages: list[str | dict[str, Any]],
) -> None:
    """チャット履歴を表示する

    TDD Green: Task 3.1のチャット履歴表示機能

    設計判断:
    - 後方互換性: 文字列と辞書の両方をサポート
    - タイムスタンプ表示: 辞書形式のメッセージにタイムスタンプを表示
    - 交互表示: ユーザーとアシスタントのメッセージを交互に表示

    Args:
        user_messages: ユーザーメッセージのリスト（文字列または辞書）
        assistant_messages: アシスタントメッセージのリスト（文字列または辞書）

    """
    # メッセージがない場合は何も表示しない
    if not user_messages and not assistant_messages:
        return

    # メッセージを交互に表示
    max_len = max(len(user_messages), len(assistant_messages))

    for i in range(max_len):
        # ユーザーメッセージ
        if i < len(user_messages):
            _render_message(user_messages[i], "user")

        # アシスタントメッセージ
        if i < len(assistant_messages):
            _render_message(assistant_messages[i], "assistant")


def _render_message(message: str | dict[str, Any], role: str) -> None:
    """単一のメッセージを表示する

    Args:
        message: メッセージ（文字列または辞書）
        role: ロール（"user" または "assistant"）

    """
    with st.chat_message(role):
        # 辞書形式の場合
        if isinstance(message, dict):
            content = message.get("content", "")
            timestamp = message.get("timestamp")

            # メッセージ内容を表示
            st.markdown(content)

            # タイムスタンプを表示
            if timestamp:
                st.caption(f"🕒 {timestamp}")
        else:
            # 文字列形式の場合（後方互換性）
            st.markdown(message)
