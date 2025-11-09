"""StreamlitWorkflowOrchestrator

セッション分離された非同期ワークフロー制御。
"""

import queue
import threading
import time
from typing import Any

from src.infrastructure.di_container import DIContainer


class StreamlitWorkflowOrchestrator:
    """セッション毎の分析ジョブを管理

    責務:
    - スレッドベースの非同期実行
    - セッション間の状態分離
    - 進捗通知とエラーハンドリング

    設計原則:
    - 単一責任の原則（SRP）: ワークフロー制御のみ
    - 依存性注入（DI）: DIContainerを通じてUse Caseを取得
    - スレッドセーフ: セッション毎に独立した状態管理
    """

    def __init__(self, di_container: DIContainer) -> None:
        """コンストラクタ

        Args:
            di_container: 依存性注入コンテナ

        """
        self.di_container = di_container

        # セッション毎の状態管理
        self.session_jobs: dict[str, threading.Thread] = {}
        self.session_queues: dict[str, queue.Queue[dict[str, Any]]] = {}
        self.session_results: dict[str, dict[str, Any] | None] = {}
        self.session_thread_counters: dict[str, int] = {}  # スレッドID管理

        # TDD Green: エラーフォールバック通知用ログ
        self.error_fallback_log: list[dict[str, Any]] = []  # スレッドID管理

    def process_user_message_async(
        self, message: str, session_id: str, file_path: str | None = None,
    ) -> str:
        """セッション分離対応の非同期処理

        Args:
            message: ユーザーメッセージ
            session_id: セッションID
            file_path: アップロードされたファイルのパス（オプション）

        Returns:
            "STARTED" または エラーメッセージ

        """
        # セッション毎のジョブ状態チェック
        current_job = self.session_jobs.get(session_id)
        if current_job and current_job.is_alive():
            return "ERROR: このセッションで他の分析が実行中です"

        # セッション専用キューを初期化（古いメッセージをクリア）
        self.session_queues[session_id] = queue.Queue()

        # セッション結果をクリア
        self.session_results[session_id] = None

        # セッション毎のスレッドカウンターを初期化
        if session_id not in self.session_thread_counters:
            self.session_thread_counters[session_id] = 0
        self.session_thread_counters[session_id] += 1

        # バックグラウンドスレッドで実行
        job_thread = threading.Thread(
            target=self._run_analysis_job,
            args=(message, session_id, file_path),
            name=f"analysis_job_{session_id}",
            daemon=True,
        )
        job_thread.start()

        # セッション毎にジョブを記録
        self.session_jobs[session_id] = job_thread

        return "STARTED"

    def _run_analysis_job(
        self, message: str, session_id: str, file_path: str | None = None,
    ) -> None:
        """セッション分離されたバックグラウンド分析実行

        Args:
            message: ユーザーメッセージ
            session_id: セッションID
            file_path: アップロードされたファイルのパス（オプション）

        """
        # セッション専用キューの存在確認（cleanup_session対策）
        session_queue = self.session_queues.get(session_id)
        if not session_queue:
            # キューが削除されている場合は静かに終了
            return

        # セッション固有のIDを生成
        thread_id = self.session_thread_counters.get(session_id, 1)
        process_id = f"{session_id}_{thread_id}"

        try:
            # ファイルがアップロードされている場合は、データ情報を取得
            data_info = ""
            step_offset = 0
            total_steps = 4

            if file_path:
                # ファイルパスの再検証（セキュリティ）
                from pathlib import Path
                from src.presentation.file_utils import validate_file_path
                
                if not Path(file_path).exists() or not validate_file_path(file_path):
                    error_result = {
                        "status": "error", 
                        "error": f"アップロードされたファイルが見つからないか、無効です: {file_path}"
                    }
                    session_queue.put(error_result)
                    self.session_results[session_id] = error_result
                    return

                session_queue.put(
                    {
                        "status": "progress",
                        "message": "データファイル情報を取得中...",
                        "step": 1,
                        "total": 5,
                    },
                )

                # ファイル情報をdata_infoに含める
                data_info = f"アップロードされたファイル: {file_path}"
                step_offset = 1
                total_steps = 5

                session_queue.put(
                    {
                        "status": "progress",
                        "message": "データファイル情報を取得しました",
                        "step": 2,
                        "total": 5,
                    },
                )

            # 進捗をセッション専用キューに送信
            session_queue.put(
                {
                    "status": "progress",
                    "message": "計画生成中...",
                    "step": 1 + step_offset,
                    "total": total_steps,
                },
            )

            # 既存Use Caseの同期呼び出し
            plan_use_case = self.di_container.get_generate_plan_use_case()
            plan_result = plan_use_case.execute(
                data_info=data_info,
                user_request=message,
                model="gpt-4o-mini",
            )

            session_queue.put(
                {
                    "status": "progress",
                    "message": "コード生成中...",
                    "step": 2 + step_offset,
                    "total": total_steps,
                },
            )

            code_use_case = self.di_container.get_generate_code_use_case()
            code_result = code_use_case.execute(
                data_info=data_info,
                user_request=message,
                model="gpt-4o-mini",
            )

            session_queue.put(
                {
                    "status": "progress",
                    "message": "コード実行中...",
                    "step": 3 + step_offset,
                    "total": total_steps,
                },
            )

            execute_use_case = self.di_container.get_execute_code_use_case()
            execution_result = execute_use_case.execute(
                process_id=process_id,  # セッション固有ID使用
                thread_id=thread_id,  # セッション固有スレッドID使用
                code=code_result.code,
                user_request=message,
            )

            session_queue.put(
                {
                    "status": "progress",
                    "message": "レポート生成中...",
                    "step": 4 + step_offset,
                    "total": total_steps,
                },
            )

            report_use_case = self.di_container.get_generate_report_use_case()
            report_result = report_use_case.execute(
                data_info=data_info,
                user_request=message,
                process_data_threads=[execution_result],
                model="gpt-4o-mini",
                output_dir="./output",
            )

            # 最終結果をセッション状態に保存
            final_result = {
                "status": "completed",
                "step": total_steps,
                "total": total_steps,
                "result": {
                    "plan": plan_result,
                    "execution": execution_result,
                    "report": report_result,
                },
            }
            session_queue.put(final_result)
            self.session_results[session_id] = final_result

        except Exception as e:
            # TDD Green: 幅広い例外をキャッチして適切に処理
            error_result = {"status": "error", "error": str(e)}

            # TDD Green: 既にキャプチャしたキューオブジェクトを使用
            try:
                session_queue.put(error_result)
                # 辞書が残っている場合は結果も保存
                if session_id in self.session_results:
                    self.session_results[session_id] = error_result
            except Exception:
                # キューオブジェクトも使用不可能な場合のフォールバック
                if not hasattr(self, "error_fallback_log"):
                    self.error_fallback_log = []
                self.error_fallback_log.append(
                    {
                        "session_id": session_id,
                        "error": str(e),
                        "timestamp": time.time(),
                    },
                )

        finally:
            # ジョブ完了時にスレッド参照をクリア（遅延削除）
            # 注: すぐに削除すると、完了直後の重複チェックが機能しない
            time.sleep(0.1)  # 短い遅延を入れて、完了状態を確認可能にする
            if session_id in self.session_jobs:
                del self.session_jobs[session_id]

    def get_job_status(self, session_id: str) -> dict[str, Any]:
        """セッション毎のジョブ状態をポーリング取得

        Args:
            session_id: セッションID

        Returns:
            ジョブ状態辞書

        """
        # セッション専用キューから取得
        session_queue = self.session_queues.get(session_id)
        if not session_queue:
            return {"status": "idle"}

        try:
            return session_queue.get_nowait()
        except queue.Empty:
            # キューが空の場合はスレッド状態を確認
            current_job = self.session_jobs.get(session_id)
            if current_job and current_job.is_alive():
                return {"status": "running"}
            if self.session_results.get(session_id):
                # 完了結果が保存されている場合
                return self.session_results[session_id]  # type: ignore[return-value]
            return {"status": "idle"}

    def cancel_current_job(self, session_id: str) -> dict[str, Any]:
        """セッション毎のジョブキャンセル（制限あり）

        Args:
            session_id: セッションID

        Returns:
            キャンセル結果辞書

        """
        current_job = self.session_jobs.get(session_id)
        if current_job and current_job.is_alive():
            # Pythonスレッドは強制終了不可のため、協調的終了のみ
            return {
                "success": False,
                "message": f"セッション {session_id}: ジョブキャンセル要求（制限あり）",
                "reason": "Python threading limitations",
            }
        return {"success": True, "message": "キャンセル対象のジョブがありません"}

    def cleanup_session(self, session_id: str) -> None:
        """セッション終了時のクリーンアップ

        Args:
            session_id: セッションID

        """
        # 実行中ジョブがある場合は完了を待つ（タイムアウト付き）
        current_job = self.session_jobs.get(session_id)
        if current_job and current_job.is_alive():
            current_job.join(timeout=1.0)  # 1秒待機

            # TDD Green: タイムアウト後の強制終了処理を追加
            if current_job.is_alive():
                # スレッドは直接終了できないため、強制フラグを設定
                # 実際の実装では、WorkerThreadでstop_eventなどを使用
                import logging

                logging.warning(
                    f"Session {session_id} job did not complete within timeout",
                )
                # TDD Green: 生きているスレッドがある場合は状態を保持
                return  # 早期リターンで状態削除をスキップ

        # ジョブ、キュー、結果、カウンターをクリア（スレッドが停止した場合のみ）
        if session_id in self.session_jobs:
            del self.session_jobs[session_id]
        if session_id in self.session_queues:
            del self.session_queues[session_id]
        if session_id in self.session_results:
            del self.session_results[session_id]
        if session_id in self.session_thread_counters:
            del self.session_thread_counters[session_id]

    def get_error_fallback_log(self) -> list[dict[str, Any]]:
        """エラーフォールバックログをUI向けに取得

        Returns:
            エラーログのリスト

        """
        return self.error_fallback_log.copy()

    def clear_error_fallback_log(self) -> None:
        """エラーフォールバックログをクリア"""
        self.error_fallback_log.clear()
