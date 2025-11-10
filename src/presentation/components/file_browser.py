"""File Browser Component

ファイル選択UIコンポーネント。
フォルダ選択とファイルアップロードの両方に対応。

設計原則:
- 単一責任の原則（SRP）: ファイル選択UIのみ
- 関心の分離: セキュリティ検証はfile_utilsに委譲
- テスト容易性: 純粋な表示関数
"""

import os
import tempfile
from pathlib import Path

import streamlit as st

from src.infrastructure.file_lifecycle_manager import get_file_lifecycle_manager

from src.presentation.file_utils import (
    ALLOWED_DATA_FOLDERS,
    resolve_with_project_root,
    validate_file_path,
)
from src.presentation.session_state_manager import SessionStateManager
from src.presentation.components.file_history import (
    add_to_recent_files,
    get_recent_files,
    render_recent_files_selector,
    add_bookmark,
    remove_bookmark,
    get_bookmarks,
)


def render_file_browser() -> str | None:
    """ファイル選択UIを表示
    
    2つのモードをサポート:
    1. フォルダ・ファイル選択モード（推奨）
    2. ファイルアップロードモード（フォールバック）
    
    Returns:
        選択されたファイルパス（サーバー側の実パス）
        
    設計判断:
    - UI非依存の戻り値（ファイルパスのみ）
    - セッション状態を直接操作（Streamlitパターン）
    - 一時ファイルのライフサイクル管理

    """
    st.subheader("📁 データ選択")

    file_manager = get_file_lifecycle_manager()
    session_id = st.session_state.get("session_id", "default")

    # データ入力モード選択
    input_mode = st.radio(
        "データ入力方式",
        ["フォルダ・ファイル選択", "ファイルアップロード"],
        index=0,
        help="フォルダ選択: サーバー上のファイルを選択\nアップロード: ローカルファイルをアップロード",
    )

    # モード切り替え時のクリーンアップ
    if "previous_input_mode" in st.session_state:
        if st.session_state.previous_input_mode != input_mode:
            _cleanup_temp_file(session_id=session_id)
            SessionStateManager.set_selected_file_path(None)
            SessionStateManager.clear_temp_file_path()
            SessionStateManager.clear_file_selection_metadata()
            st.session_state.original_filename = None

    st.session_state.previous_input_mode = input_mode

    selected_file_path: str | None = None

    if input_mode == "フォルダ・ファイル選択":
        selected_file_path = _render_folder_selection()
    else:
        selected_file_path = _render_file_upload(file_manager=file_manager, session_id=session_id)

    return selected_file_path


def _render_folder_selection() -> str | None:
    """フォルダ・ファイル選択モードのUI"""

    allowed_display = [str(Path(folder).resolve()) for folder in ALLOWED_DATA_FOLDERS]
    st.info(f"📂 許可されたフォルダ: {', '.join(allowed_display)}")

    # 最近使用したファイルから選択
    recent_files = get_recent_files()
    if recent_files:
        with st.expander("📋 最近使用したファイル", expanded=False):
            selected_recent = render_recent_files_selector()
            if selected_recent:
                SessionStateManager.set_selected_file_path(selected_recent)
                SessionStateManager.set_file_selection_metadata(
                    source="folder",
                    is_temporary=False,
                )
                SessionStateManager.clear_temp_file_path()
                st.session_state.original_filename = os.path.basename(selected_recent)
                st.success(f"✅ 履歴から選択: {os.path.basename(selected_recent)}")
                return selected_recent

    # ブックマーク管理
    bookmarks = get_bookmarks()
    if bookmarks:
        with st.expander("🔖 ブックマーク", expanded=False):
            for bookmark in bookmarks:
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.button(
                        f"📁 {bookmark['label']}",
                        key=f"bookmark_{bookmark['path']}",
                    ):
                        st.session_state.bookmark_folder_path = bookmark["path"]
                with col2:
                    if st.button(
                        "🗑️",
                        key=f"remove_bookmark_{bookmark['path']}",
                        help="削除",
                    ):
                        remove_bookmark(bookmark["path"])
                        st.rerun()

    default_folder = st.session_state.get(
        "bookmark_folder_path",
        ALLOWED_DATA_FOLDERS[0],
    )
    folder_path = st.text_input(
        "フォルダパス",
        value=default_folder,
        help="許可されたフォルダのパスを入力してください",
    )

    if not folder_path:
        return None

    resolved_folder: Path | None = None
    try:
        resolved_folder = resolve_with_project_root(folder_path)
    except ValueError:
        resolved_folder = None

    if not resolved_folder or not resolved_folder.exists():
        st.warning(f"⚠️ フォルダが見つかりません: {folder_path}")
        return None

    if not resolved_folder.is_dir():
        st.warning(f"⚠️ フォルダではありません: {folder_path}")
        return None

    allowed_roots = [Path(folder).resolve() for folder in ALLOWED_DATA_FOLDERS]
    if not any(resolved_folder.is_relative_to(root) for root in allowed_roots):
        st.error("❌ 許可されたフォルダ外です")
        return None

    _, add_col = st.columns([4, 1])
    with add_col:
        if st.button("🔖 追加", key="add_bookmark_btn"):
            label = resolved_folder.name or "ルート"
            add_bookmark(str(resolved_folder), label)
            st.success(f"✅ ブックマーク追加: {label}")

    try:
        all_files = os.listdir(str(resolved_folder))
    except PermissionError:
        st.error("❌ フォルダへのアクセス権限がありません")
        return None
    except OSError as exc:
        st.error(f"❌ エラー: {exc}")
        return None

    data_files = [
        f
        for f in all_files
        if f.lower().endswith((".csv", ".xlsx", ".xls", ".tsv"))
    ]

    if not data_files:
        st.warning("⚠️ データファイル（CSV/Excel/TSV）が見つかりません")
        return None

    stored_file = st.session_state.get("folder_selected_file")
    default_index = 0
    if stored_file in data_files:
        default_index = data_files.index(stored_file)

    selected_file = st.selectbox(
        "ファイル選択",
        data_files,
        index=default_index,
        key="folder_selected_file",
        help="分析するファイルを選択してください",
    )

    if not selected_file:
        return None

    file_path = str(resolved_folder / selected_file)

    if not validate_file_path(file_path):
        st.error("❌ セキュリティエラー: 許可されていないパスです")
        return None

    SessionStateManager.set_selected_file_path(file_path)
    SessionStateManager.set_file_selection_metadata(source="folder", is_temporary=False)
    SessionStateManager.clear_temp_file_path()
    st.session_state.original_filename = selected_file
    add_to_recent_files(file_path)
    st.success(f"✅ 選択: {selected_file}")
    return file_path


def _render_file_upload(*, file_manager, session_id: str) -> str | None:
    """ファイルアップロードモードのUI
    
    Returns:
        一時ファイルのパス
        
    設計判断:
    - 一時ファイル作成（tempfile）
    - セッション状態に保存（復旧用）
    - 元の拡張子を保持

    """
    st.info("📤 ローカルファイルをアップロードしてください")

    uploaded_file = st.file_uploader(
        "CSVファイルをアップロード",
        type=["csv", "xlsx", "xls", "tsv"],
        help="最大200MB",
    )

    if uploaded_file:
        # 既存の一時ファイルをクリーンアップ
        _cleanup_temp_file(session_id=session_id)

        # 元の拡張子を保持
        original_extension = os.path.splitext(uploaded_file.name)[1] or ".csv"

        # アップロードファイルのバイトデータを保持（セッション復旧用）
        uploaded_bytes = uploaded_file.read()
        st.session_state.uploaded_file_bytes = uploaded_bytes
        st.session_state.original_filename = uploaded_file.name
        st.session_state.original_extension = original_extension

        # 一時ファイル作成
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=original_extension,
        ) as tmp_file:
            tmp_file.write(uploaded_bytes)
            temp_path = tmp_file.name

        SessionStateManager.set_temp_file_path(temp_path)
        SessionStateManager.set_selected_file_path(temp_path)
        SessionStateManager.set_file_selection_metadata(source="upload", is_temporary=True)
        file_manager.track_temp_file(session_id, temp_path)

        st.success(f"✅ アップロード完了: {uploaded_file.name}")
        return SessionStateManager.get_temp_file_path()

    return None


def _cleanup_temp_file(*, session_id: str | None = None) -> None:
    """一時ファイルのクリーンアップ
    
    TDD Green: Clean Architecture統合
    
    設計判断:
    - インフラストラクチャ層委譲: FileLifecycleManagerが安全性を保証
    - セッション状態のクリア: プレゼンテーション層の責任
    """
    # TDD Green: インフラストラクチャ層の安全なクリーンアップ
    file_manager = get_file_lifecycle_manager()
    active_session = session_id or st.session_state.get("session_id", "default")
    file_manager.cleanup_session_files(active_session)

    # セッション状態をクリア
    was_temporary = SessionStateManager.is_selected_file_temporary()
    SessionStateManager.clear_temp_file_path()
    SessionStateManager.clear_file_selection_metadata()

    if was_temporary:
        SessionStateManager.set_selected_file_path(None)

    for key in ["uploaded_file_bytes", "original_extension"]:
        if key in st.session_state:
            del st.session_state[key]


def cleanup_temp_file_after_processing() -> None:
    """分析処理完了後の一時ファイルクリーンアップ
    
    公開API: chat_ui.pyから呼び出される
    
    TDD Green: セキュリティ修正統合
    
    設計判断:
    - 完全なセッション状態クリア
    - インフラストラクチャ層委譲: 安全性の保証
    """
    was_temporary = SessionStateManager.is_selected_file_temporary()
    _cleanup_temp_file()

    if was_temporary:
        for key in ["selected_file_path", "original_filename", "selected_file_name"]:
            if key in st.session_state:
                del st.session_state[key]
