"""Streamlit Chat UI

基本的なチャットインターフェース。
TDD Green Phase: 最小限の動作するUI。

設計原則:
- 単一責任の原則（SRP）: UI表示のみ
- 関心の分離: ビジネスロジックはOrchestratorに委譲
- テスト容易性: セッション状態を明示的に管理
"""

from pathlib import Path

import streamlit as st

from src.infrastructure.di_container import DIContainer
from src.presentation.file_utils import validate_file_path
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


def save_uploaded_file_to_disk(uploaded_file) -> str | None:
    """アップロードファイルをディスクに保存
    
    設計判断:
    - セキュリティ: 安全なディレクトリに保存
    - 一時ファイル使用: 適切なクリーンアップ
    - 検証後保存: ファイルパス検証を実行後に保存
    
    Args:
        uploaded_file: Streamlitアップロードファイルオブジェクト
        
    Returns:
        str | None: 保存されたファイルパス、失敗時はNone

    """
    if uploaded_file is None:
        return None

    try:
        # データディレクトリの作成
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)

        # ファイル名の安全化（パストラバーサル攻撃対策）
        safe_filename = Path(uploaded_file.name).name
        file_path = data_dir / safe_filename

        # ファイルの保存
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        return str(file_path)

    except Exception:
        return None


def show_file_upload_ui() -> bool:
    """ファイルアップロードUIの表示

    TDD Blue Phase: クリーンアーキテクチャ・責務分離・型安全性

    設計判断:
    - 単一責任原則: UIコンポーネントの統合のみ
    - セキュリティファースト: ファイルを保存後に検証
    - 型安全性: 明示的boolean戻り値
    - 状態管理分離: SessionStateManager使用

    Returns:
        bool: ファイルがアップロードされた場合True

    Raises:
        なし - UI層ではエラーを投げない設計

    """
    from src.presentation.components.file_browser import render_file_browser

    uploaded_file = render_file_browser()

    if uploaded_file is not None:
        # ファイルをディスクに保存
        saved_file_path = save_uploaded_file_to_disk(uploaded_file)

        if saved_file_path and validate_file_path(saved_file_path):
            # 検証に成功した場合のみセッション状態を更新
            SessionStateManager.set_uploaded_file(uploaded_file)
            SessionStateManager.set_selected_file_path(saved_file_path)
            SessionStateManager.set_file_mode(True)
            return True
        # 検証に失敗した場合はファイルを削除
        if saved_file_path and Path(saved_file_path).exists():
            try:
                Path(saved_file_path).unlink()
            except Exception:
                pass  # クリーンアップの失敗は無視
        st.error("ファイルの検証に失敗しました。許可されたファイル形式を確認してください。")

    return False


def handle_file_uploaded() -> None:
    """ファイルアップロード後の処理

    TDD Blue Phase: エラーハンドリング・ユーザビリティ・責務分離

    設計判断:
    - 単一責任原則: ファイルアップロード成功時の通知のみ
    - エラーハンドリング: None チェックと安全な属性アクセス
    - ユーザビリティ: 成功メッセージの表示
    - 状態管理分離: SessionStateManager使用

    Raises:
        なし - UI層での例外は適切にハンドリング

    """
    uploaded_file = SessionStateManager.get_uploaded_file()
    file_path = SessionStateManager.get_selected_file_path()

    if uploaded_file is not None and file_path is not None:
        try:
            file_name = uploaded_file.name
            st.success(f"✅ ファイル '{file_name}' がアップロードされ、検証されました")

            # ファイルプレビューの表示（オプション）
            from src.presentation.file_utils import safe_preview_file
            try:
                preview_data = safe_preview_file(file_path)
                if preview_data is not None:
                    st.subheader("📊 ファイルプレビュー")
                    # preview_dataがDataFrameの場合のみhead()とemptyを使用
                    import pandas as pd
                    if isinstance(preview_data, pd.DataFrame) and not preview_data.empty:
                        st.dataframe(preview_data.head(10))  # 最初の10行のみ表示
            except Exception:
                pass  # プレビューの失敗は無視

        except AttributeError:
            # ファイルオブジェクトに name 属性がない場合のフォールバック
            st.error("ファイルの処理中にエラーが発生しました")
            SessionStateManager.set_uploaded_file(None)
            SessionStateManager.set_selected_file_path(None)
            SessionStateManager.set_file_mode(False)


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

    col1, col2 = st.columns([1, 5])

    with col1:
        submit_button = st.button(
            "🚀 分析開始",
            disabled=st.session_state.job_running or not user_input,
            use_container_width=True,
        )

    with col2:
        if st.session_state.job_running:
            st.info("⏳ 分析実行中...")

    # 分析開始処理
    if submit_button and user_input:
        # ファイルパスを取得してオーケストレーターに渡す
        selected_file_path = SessionStateManager.get_selected_file_path()
        result = orchestrator.process_user_message_async(user_input, session_id, selected_file_path)

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
            # 進捗表示
            progress = status.get("step", 0) / status.get("total", 1)
            st.progress(progress, text=status.get("message", "処理中..."))

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
            st.rerun()

        elif status["status"] == "error":
            # エラー
            st.session_state.job_running = False
            error_msg = status.get("error", "不明なエラー")
            st.session_state.assistant_messages.append(f"エラー: {error_msg}")
            st.error(f"❌ エラー: {error_msg}")

    # メッセージ履歴表示
    if st.session_state.user_messages or st.session_state.assistant_messages:
        st.markdown("---")
        st.subheader("📝 履歴")

        # メッセージを交互に表示
        max_len = max(
            len(st.session_state.user_messages),
            len(st.session_state.assistant_messages),
        )

        for i in range(max_len):
            if i < len(st.session_state.user_messages):
                with st.chat_message("user"):
                    st.write(st.session_state.user_messages[i])

            if i < len(st.session_state.assistant_messages):
                with st.chat_message("assistant"):
                    st.write(st.session_state.assistant_messages[i])

    # 結果表示
    if st.session_state.analysis_result:
        st.markdown("---")
        st.subheader("📊 分析結果")
        st.json(st.session_state.analysis_result)

    # サイドバー: セッション情報
    with st.sidebar:
        st.header("ℹ️ セッション情報")
        st.text(f"Session ID: {session_id[:8]}...")
        st.text(f"実行中: {'はい' if st.session_state.job_running else 'いいえ'}")

        # アップロードされたファイル情報
        uploaded_file = SessionStateManager.get_uploaded_file()
        file_path = SessionStateManager.get_selected_file_path()

        if uploaded_file is not None and file_path is not None:
            st.markdown("---")
            st.subheader("📄 アップロードファイル")
            st.text(f"ファイル名: {uploaded_file.name}")
            st.text(f"パス: {Path(file_path).name}")

        if st.button("🔄 セッションリセット"):
            # セッション状態をクリア
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


if __name__ == "__main__":
    main()
