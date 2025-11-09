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

import streamlit as st

from src.infrastructure.file_lifecycle_manager import get_file_lifecycle_manager
from src.presentation.file_utils import ALLOWED_DATA_FOLDERS, validate_file_path
from src.presentation.session_state_manager import SessionStateManager


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
    """フォルダ・ファイル選択モードのUI
    
    Returns:
        選択されたファイルパス
        
    設計判断:
    - 許可フォルダのみ表示
    - セキュリティ検証（validate_file_path）

    """
    st.info(f"📂 許可されたフォルダ: {', '.join(ALLOWED_DATA_FOLDERS)}")

    # フォルダパス入力
    folder_path = st.text_input(
        "フォルダパス",
        value="./data/",
        help="許可されたフォルダのパスを入力してください",
    )

    if not folder_path:
        return None

    # フォルダの存在確認
    if not os.path.exists(folder_path):
        st.warning(f"⚠️ フォルダが見つかりません: {folder_path}")
        return None

    if not os.path.isdir(folder_path):
        st.warning(f"⚠️ フォルダではありません: {folder_path}")
        return None

    # ファイル一覧取得
    try:
        all_files = os.listdir(folder_path)
        data_files = [
            f
            for f in all_files
            if f.lower().endswith((".csv", ".xlsx", ".xls", ".tsv"))
        ]

        if not data_files:
            st.warning("⚠️ データファイル（CSV/Excel/TSV）が見つかりません")
            return None

        # ファイル選択
        selected_file = st.selectbox(
            "ファイル選択",
            data_files,
            help="分析するファイルを選択してください",
        )

        if selected_file:
            file_path = os.path.join(folder_path, selected_file)

            # セキュリティ検証
            if validate_file_path(file_path):
                SessionStateManager.set_selected_file_path(file_path)
                SessionStateManager.set_file_selection_metadata(source="folder", is_temporary=False)
                SessionStateManager.clear_temp_file_path()
                st.session_state.original_filename = selected_file
                st.success(f"✅ 選択: {selected_file}")
                return file_path
            st.error("❌ セキュリティエラー: 許可されていないパスです")
            return None

    except PermissionError:
        st.error("❌ フォルダへのアクセス権限がありません")
        return None
    except (OSError, ValueError) as e:
        st.error(f"❌ エラー: {e}")
        return None

    return None


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
