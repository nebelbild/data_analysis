"""File History Component

ファイル履歴管理コンポーネント。
最近使用したファイルとブックマークの管理。

TDD Green: 最小限の実装

設計原則:
- 単一責任の原則（SRP）: ファイル履歴管理のみ
- 関心の分離: UI表示とデータ管理を分離
- テスト容易性: 純粋な関数、UI非依存
- YAGNI: 必要な機能のみ実装
"""

import streamlit as st


# 最大履歴数
MAX_RECENT_FILES = 10


def add_to_recent_files(file_path: str) -> None:
    """最近使用したファイルに追加
    
    Args:
        file_path: ファイルパス
        
    設計判断:
    - 重複は最新に移動
    - 最大10件まで保持
    - セッション状態に保存
    """
    if "recent_files" not in st.session_state:
        st.session_state.recent_files = []
    
    recent = st.session_state.recent_files
    
    # 重複を削除
    if file_path in recent:
        recent.remove(file_path)
    
    # 先頭に追加
    recent.insert(0, file_path)
    
    # 最大件数を超えたら削除
    if len(recent) > MAX_RECENT_FILES:
        st.session_state.recent_files = recent[:MAX_RECENT_FILES]


def get_recent_files() -> list[str]:
    """最近使用したファイルを取得
    
    Returns:
        ファイルパスのリスト（新しい順）
    """
    if "recent_files" not in st.session_state:
        return []
    
    return st.session_state.recent_files


def clear_recent_files() -> None:
    """履歴をクリア"""
    if "recent_files" in st.session_state:
        st.session_state.recent_files = []


def add_bookmark(folder_path: str, label: str) -> None:
    """ブックマークを追加
    
    Args:
        folder_path: フォルダパス
        label: ブックマークのラベル
        
    設計判断:
    - 重複は追加しない
    - セッション状態に保存
    """
    if "bookmarks" not in st.session_state:
        st.session_state.bookmarks = []
    
    bookmarks = st.session_state.bookmarks
    
    # 重複チェック
    for bookmark in bookmarks:
        if bookmark["path"] == folder_path:
            return  # 既に存在する場合は追加しない
    
    # 追加
    bookmarks.append({"path": folder_path, "label": label})


def remove_bookmark(folder_path: str) -> None:
    """ブックマークを削除
    
    Args:
        folder_path: フォルダパス
    """
    if "bookmarks" not in st.session_state:
        return
    
    bookmarks = st.session_state.bookmarks
    st.session_state.bookmarks = [
        b for b in bookmarks if b["path"] != folder_path
    ]


def get_bookmarks() -> list[dict[str, str]]:
    """ブックマークを取得
    
    Returns:
        ブックマークのリスト [{"path": str, "label": str}, ...]
    """
    if "bookmarks" not in st.session_state:
        return []
    
    return st.session_state.bookmarks


def render_recent_files_selector() -> str | None:
    """最近使用したファイルのセレクタを表示

    Returns:
        ボタン操作で確定されたファイルパス

    TDD Green: UI統合
    """
    recent = get_recent_files()

    if not recent:
        st.info("📋 履歴がありません")
        return None

    selected = st.selectbox(
        "最近使用したファイル",
        recent,
        key="recent_files_select",
        help="最近使用したファイルから選択",
    )

    if st.button("このファイルを使用", key="use_recent_file_button"):
        return selected

    return None


def render_bookmarks_manager() -> None:
    """ブックマーク管理UIを表示
    
    TDD Green: UI統合
    """
    st.subheader("🔖 ブックマーク")
    
    # ブックマーク追加
    col1, col2 = st.columns([3, 1])
    with col1:
        folder_path = st.text_input("フォルダパス", key="bookmark_folder")
        label = st.text_input("ラベル", key="bookmark_label")
    with col2:
        st.write("")  # スペース調整
        st.write("")  # スペース調整
        if st.button("追加", key="add_bookmark"):
            if folder_path and label:
                add_bookmark(folder_path, label)
                st.success(f"✅ ブックマーク追加: {label}")
    
    # ブックマーク一覧
    bookmarks = get_bookmarks()
    if bookmarks:
        st.write("**登録済みブックマーク:**")
        for bookmark in bookmarks:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"📁 {bookmark['label']}: `{bookmark['path']}`")
            with col2:
                if st.button("削除", key=f"remove_{bookmark['path']}"):
                    remove_bookmark(bookmark["path"])
                    st.rerun()
    else:
        st.info("ブックマークがありません")
