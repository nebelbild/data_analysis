"""Streamlit Chat UI

基本的なチャットインターフェース。
"""

from pathlib import Path

import streamlit as st

from src.infrastructure.di_container import DIContainer
from src.presentation.session_state_manager import SessionStateManager
from src.presentation.workflow_orchestrator import StreamlitWorkflowOrchestrator


@st.cache_resource
def get_orchestrator() -> StreamlitWorkflowOrchestrator:
    """オーケストレータの永続化

    設計判断:
    - @st.cache_resourceでアプリ全体で共有
    - Streamlit再実行時も永続化

    Returns:
        StreamlitWorkflowOrchestrator: 永続化されたインスタンス

    """
    di_container = DIContainer()
    return StreamlitWorkflowOrchestrator(di_container)


def initialize_session_state() -> None:
    """セッション状態の初期化

    TDD Blue Phase: セッション状態管理の責務分離

    設計判断:
    - 依存性逆転: SessionStateManager に委譲
    - 単一責任原則: 初期化の統括のみ
    - 保守性: 状態管理ロジックの一元化
    """
    from src.presentation.session_state_manager import initialize_all_session_states

    initialize_all_session_states()  # False: チャット, True: ファイル


def _cleanup_upload_if_needed() -> None:
    """現在のセッションでアップロードした一時ファイルを削除"""
    if not SessionStateManager.is_selected_file_temporary():
        return

    from src.infrastructure.file_lifecycle_manager import get_file_lifecycle_manager

    session_id = st.session_state.get("session_id", "default")
    file_manager = get_file_lifecycle_manager()
    file_manager.cleanup_session_files(session_id)

    SessionStateManager.set_selected_file_path(None)
    SessionStateManager.clear_file_selection_metadata()
    SessionStateManager.clear_temp_file_path()

    for attr in ["selected_file_name", "original_filename"]:
        if hasattr(st.session_state, attr):
            delattr(st.session_state, attr)


def cleanup_temp_file_after_processing(file_path: str | None) -> None:
    """処理後の一時ファイルクリーンアップ
    
    TDD Green: セキュリティ問題修正
    
    設計判断:
    - セキュリティ修正: 任意のファイル削除を禁止
    - Clean Architecture: インフラストラクチャ層のサービス使用
    - 後方互換性: 既存のインターフェースを維持
    
    Args:
        file_path: 削除対象ファイルパス（セキュリティ上、無視される）
        
    Note:
        この関数は後方互換性のために残されています。
        実際のクリーンアップはFileLifecycleManagerが管理します。
        既存のデータファイルを誤って削除する問題を修正済みです。
    """
    # TDD Green: セキュリティ修正
    # 任意のファイル削除を禁止し、追跡されたファイルのみ削除するように変更
    # file_pathパラメータは後方互換性のために残すが、実際には使用しない
    _cleanup_upload_if_needed()


def show_file_upload_ui() -> bool:
    """ファイルアップロードUIの表示

    TDD Blue Phase: クリーンアーキテクチャ・責務分離・型安全性

    設計判断:
    - 単一責任原則: UIコンポーネントの統合のみ
    - 責務分離: ファイル処理はfile_browserコンポーネントに委譲
    - 型安全性: 明示的boolean戻り値
    - 状態管理分離: SessionStateManager使用

    Returns:
        bool: ファイルが選択された場合True

    Raises:
        なし - UI層ではエラーを投げない設計

    """
    from src.presentation.components.file_browser import render_file_browser

    # render_file_browser() はファイルパス（str）を返し、内部で保存・検証を実行
    selected_file_path = render_file_browser()

    if selected_file_path is not None:
        # file_browserが既に検証済みのため、セッション状態のみ更新
        SessionStateManager.set_selected_file_path(selected_file_path)
        SessionStateManager.set_file_mode(True)

        # ファイル名情報をセッション状態から取得（file_browserが設定済み）
        if hasattr(st.session_state, "original_filename"):
            st.session_state.selected_file_name = st.session_state.original_filename
        else:
            file_name = Path(selected_file_path).name
            st.session_state.selected_file_name = file_name

        return True

    return False


def handle_file_uploaded() -> None:
    """ファイルアップロード後の処理

    TDD Green: data_preview.pyコンポーネント統合

    設計判断:
    - 単一責任原則: ファイルアップロード成功時の通知とプレビュー表示
    - 関心の分離: プレビュー表示はdata_preview.pyに委譲
    - エラーハンドリング: None チェックと安全な属性アクセス
    - ユーザビリティ: 成功メッセージの表示
    - 状態管理分離: SessionStateManager使用

    Raises:
        なし - UI層での例外は適切にハンドリング
    """
    file_path = SessionStateManager.get_selected_file_path()

    if file_path is not None:
        try:
            # ファイル名の取得（パスから、またはセッション状態から）
            file_name = getattr(st.session_state, "selected_file_name", Path(file_path).name)
            st.success(f"✅ ファイル '{file_name}' がアップロードされ、検証されました")

            # TDD Green: data_preview.pyコンポーネントを使用
            from src.presentation.components.data_preview import render_data_preview

            try:
                render_data_preview(file_path)
            except Exception:
                # プレビュー表示のエラーは無視（分析は継続可能）
                pass

        except (AttributeError, OSError):
            # ファイル処理中のエラー
            st.error("ファイルの処理中にエラーが発生しました")
            SessionStateManager.set_selected_file_path(None)
            SessionStateManager.set_file_mode(False)
            if hasattr(st.session_state, "selected_file_name"):
                delattr(st.session_state, "selected_file_name")


def reset_session() -> None:
    """セッションをリセットする

    TDD Green: Task 2.4のセッションリセット機能

    設計判断:
    - 実行中はリセットしない（安全性）
    - セッションIDは保持（継続性）
    - 一時ファイルをクリーンアップ
    - セッション状態をクリア

    """
    # 実行中はリセットしない
    if st.session_state.get("job_running", False):
        return

    # 一時ファイルクリーンアップ
    _cleanup_upload_if_needed()

    # セッション状態をクリア（セッションIDは保持）
    st.session_state["user_messages"] = []
    st.session_state["assistant_messages"] = []
    st.session_state["analysis_result"] = None
    st.session_state["selected_file_path"] = None

    # UIをリフレッシュ（この後のコードは実行されない）
    st.rerun()


def main() -> None:
    """メインUI関数

    設計判断:
    - 関数ベースの構成（Streamlitの推奨パターン）
    - トップダウンの読みやすい構造
    """
    # ページ設定
    st.set_page_config(
        page_title="DataAnalysisAgent",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # セッション状態初期化
    initialize_session_state()

    # オーケストレータ取得
    orchestrator = get_orchestrator()
    session_id = st.session_state.session_id

    # タイトル
    st.title("📊 DataAnalysisAgent")
    st.markdown("AIを活用したデータ分析自動化エージェント")

    # メインコンテンツ
    st.markdown("---")

    # ファイルアップロード
    st.subheader("📁 データファイル")

    # ファイルアップロードUIの表示と処理
    if show_file_upload_ui():
        handle_file_uploaded()

    # チャット入力エリア
    st.subheader("💬 分析要求")

    user_input = st.text_input(
        "分析したい内容を入力してください:",
        placeholder="例: データを詳しく分析して、散布図と相関行列を生成してください",
        disabled=st.session_state.job_running,
        key="user_input",
    )

    # Streamlitテスト環境での互換性確保
    columns = st.columns([1, 1, 4])
    if len(columns) >= 3:
        col1, col2, col3 = columns[0], columns[1], columns[2]
    else:
        col1, col2 = columns[0], columns[1]
        col3 = col2  # フォールバック

    with col1:
        submit_button = st.button(
            "🚀 分析開始",
            disabled=st.session_state.job_running or not user_input,
            use_container_width=True,
        )

    with col2:
        # Task 3.3: キャンセルボタン
        cancel_button = st.button(
            "⏹️ キャンセル",
            disabled=not st.session_state.job_running,
            use_container_width=True,
            help="実行中の分析をキャンセルします（制限あり）",
        )

    with col3:
        if st.session_state.job_running:
            st.info("⏳ 分析実行中...")
            st.caption("⚠️ Pythonスレッドの制限により、完全なキャンセルはできません")

    # Task 3.3: キャンセル処理
    if cancel_button and st.session_state.job_running:
        cancel_result = orchestrator.cancel_current_job(session_id)
        if cancel_result["success"]:
            st.info(f"ℹ️ {cancel_result['message']}")
        else:
            st.warning(f"⚠️ {cancel_result['message']}")
            if "reason" in cancel_result:
                st.caption(f"理由: {cancel_result['reason']}")

    # 分析開始処理
    if submit_button and user_input:
        # ファイルパスを取得してオーケストレーターに渡す
        selected_file_path = SessionStateManager.get_selected_file_path()
        is_temp_file = SessionStateManager.is_selected_file_temporary()
        result = orchestrator.process_user_message_async(
            user_input,
            session_id,
            selected_file_path,
            is_temporary_file=is_temp_file,
        )

        if result == "STARTED":
            st.session_state.job_running = True
            st.session_state.user_messages.append(user_input)
            st.success("✅ 分析を開始しました")
            st.rerun()
        else:
            st.error(f"❌ {result}")

    # 進捗確認
    if st.session_state.job_running:
        status = orchestrator.get_job_status(session_id)

        if status["status"] == "progress":
            # Task 3.4: ローディングアニメーション
            with st.spinner("分析を実行中..."):
                # TDD Green: progress_displayコンポーネントを使用
                from src.presentation.components.progress_display import render_progress

                render_progress(status)

                # 1秒後にリフレッシュ
                import time

                time.sleep(1)
            st.rerun()

        elif status["status"] == "completed":
            # 完了
            st.session_state.job_running = False
            st.session_state.analysis_result = status.get("result")
            st.session_state.assistant_messages.append("分析が完了しました")
            st.success("✅ 分析完了！")
            _cleanup_upload_if_needed()
            st.rerun()

        elif status["status"] == "error":
            # エラー処理（Task 2.3: エラーハンドリング強化）
            from src.presentation.components.error_handler import handle_error

            st.session_state.job_running = False
            error_msg = status.get("error", "不明なエラー")
            st.session_state.assistant_messages.append(f"エラー: {error_msg}")

            # 統一的なエラー処理
            handle_error(error_msg, session_id)

            _cleanup_upload_if_needed()

    # メッセージ履歴表示（Task 3.1: チャット履歴コンポーネント）
    if st.session_state.user_messages or st.session_state.assistant_messages:
        from src.presentation.components.chat_history import render_chat_history

        st.markdown("---")
        st.subheader("📝 履歴")

        render_chat_history(
            st.session_state.user_messages,
            st.session_state.assistant_messages,
        )

    # 結果表示
    if st.session_state.analysis_result:
        from src.presentation.components.result_viewer import render_result

        st.markdown("---")
        render_result(st.session_state.analysis_result)

    # サイドバー: セッション情報
    with st.sidebar:
        st.header("ℹ️ セッション情報")
        st.text(f"Session ID: {session_id[:8]}...")
        st.text(f"実行中: {'はい' if st.session_state.job_running else 'いいえ'}")

        # アップロードされたファイル情報
        file_path = SessionStateManager.get_selected_file_path()

        if file_path is not None:
            st.markdown("---")
            st.subheader("📄 選択ファイル")
            file_name = getattr(st.session_state, "selected_file_name", Path(file_path).name)
            st.text(f"ファイル名: {file_name}")
            st.text(f"パス: {Path(file_path).name}")

        # Task 2.4: セッションリセットボタン
        if st.button("🔄 セッションリセット", disabled=st.session_state.job_running):
            reset_session()


if __name__ == "__main__":
    main()
