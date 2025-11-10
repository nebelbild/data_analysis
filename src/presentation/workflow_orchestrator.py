"""StreamlitWorkflowOrchestrator

セッション分離された非同期ワークフロー制御。
"""

import base64
import queue
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.domain.entities.data_thread import DataThread
from src.infrastructure.di_container import DIContainer
from src.infrastructure.renderers.html_renderer import HTMLRenderer


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
        self,
        message: str,
        session_id: str,
        file_path: str | None = None,
        *,
        is_temporary_file: bool = False,
    ) -> str:
        """セッション分離対応の非同期処理

        Args:
            message: ユーザーメッセージ
            session_id: セッションID
            file_path: アップロードされたファイルのパス（オプション）

        Returns:
            "STARTED" または エラーメッセージ

        """
        print(f"[DEBUG] process_user_message_async呼び出し: session_id={session_id}")
        
        # セッション毎のジョブ状態チェック
        current_job = self.session_jobs.get(session_id)
        if current_job and current_job.is_alive():
            print(f"[DEBUG] 既存ジョブ実行中: {session_id}")
            return "ERROR: このセッションで他の分析が実行中です"

        # セッション専用キューを初期化（古いメッセージをクリア）
        self.session_queues[session_id] = queue.Queue()
        print(f"[DEBUG] セッションキュー作成: {session_id}")

        # セッション結果をクリア
        self.session_results[session_id] = None

        # セッション毎のスレッドカウンターを初期化
        if session_id not in self.session_thread_counters:
            self.session_thread_counters[session_id] = 0
        self.session_thread_counters[session_id] += 1

        # バックグラウンドスレッドで実行
        job_thread = threading.Thread(
            target=self._run_analysis_job,
            args=(message, session_id, file_path, is_temporary_file),
            name=f"analysis_job_{session_id}",
            daemon=True,
        )
        job_thread.start()
        print(f"[DEBUG] ワークフロースレッド開始: {session_id}")

        # セッション毎にジョブを記録
        self.session_jobs[session_id] = job_thread

        return "STARTED"

    def _run_analysis_job(
        self,
        message: str,
        session_id: str,
        file_path: str | None = None,
        is_temporary_file: bool = False,
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
            # TDD Green: file_pathに基づくdata_infoの適切な設定
            if file_path:
                # ファイルパスの再検証（セキュリティ）
                from pathlib import Path
                from src.presentation.file_utils import validate_file_path
                import tempfile

                path_obj = Path(file_path)

                try:
                    real_path = path_obj.resolve()
                    path_exists = real_path.exists()
                except (OSError, RuntimeError):
                    path_exists = False
                    real_path = path_obj

                allowed_path = validate_file_path(str(real_path))

                if is_temporary_file:
                    try:
                        temp_root = Path(tempfile.gettempdir()).resolve()
                        allowed_path = allowed_path or real_path.is_relative_to(temp_root)
                    except Exception:
                        # フォールバック: 仮に許可されていない扱い
                        allowed_path = False

                if not path_exists or not allowed_path:
                    error_result = {
                        "status": "error",
                        "error": f"アップロードされたファイルが見つからないか、無効です: {file_path}",
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
                display_name = Path(file_path).name
                if is_temporary_file:
                    data_info = f"アップロードされたファイル: {display_name}"
                else:
                    data_info = f"指定ファイル: {file_path}"
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
            else:
                # TDD Green: file_path=Noneの場合の適切なdata_info設定
                data_info = "ファイルが指定されていません。"
                step_offset = 0
                total_steps = 4

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
            print(f"[DEBUG] セッション {session_id}: 計画生成開始")
            plan_use_case = self.di_container.get_generate_plan_use_case()
            plan_result = plan_use_case.execute(
                data_info=data_info,
                user_request=message,
                model="gpt-4o-mini",
            )
            print(f"[DEBUG] セッション {session_id}: 計画生成完了")

            session_queue.put(
                {
                    "status": "progress",
                    "message": "コード生成中...",
                    "step": 2 + step_offset,
                    "total": total_steps,
                },
            )

            print(f"[DEBUG] セッション {session_id}: コード生成開始")
            code_use_case = self.di_container.get_generate_code_use_case()
            code_result = code_use_case.execute(
                data_info=data_info,
                user_request=message,
                model="gpt-4o-mini",
            )
            print(f"[DEBUG] セッション {session_id}: コード生成完了")

            session_queue.put(
                {
                    "status": "progress",
                    "message": "コード実行中...",
                    "step": 3 + step_offset,
                    "total": total_steps,
                },
            )

            print(f"[DEBUG] セッション {session_id}: コード実行開始")
            execute_use_case = self.di_container.get_execute_code_use_case()
            execution_result = execute_use_case.execute(
                process_id=process_id,  # セッション固有ID使用
                thread_id=thread_id,  # セッション固有スレッドID使用
                code=code_result.code,
                user_request=message,
            )
            print(f"[DEBUG] セッション {session_id}: コード実行完了")
            print(f"[DEBUG] 実行結果: error={execution_result.error}, stderr={len(execution_result.stderr) if execution_result.stderr else 0}文字")

            output_dir = self._build_output_dir(session_id)
            saved_images = self._save_execution_artifacts(execution_result, output_dir)
            built_in_summary = None

            if (not saved_images) and file_path:
                built_in_summary = self._run_builtin_analysis(file_path, output_dir)

            session_queue.put(
                {
                    "status": "progress",
                    "message": "レポート生成中...",
                    "step": 4 + step_offset,
                    "total": total_steps,
                },
            )

            print(f"[DEBUG] セッション {session_id}: レポート生成開始 output_dir={output_dir}")

            if built_in_summary:
                report_content = self._build_builtin_report(built_in_summary, output_dir)
                HTMLRenderer().render(report_content, output_dir)
                report_result = {"content": report_content, "output_dir": output_dir}
                print(f"[DEBUG] セッション {session_id}: ビルトインレポートを生成")
            else:
                report_use_case = self.di_container.get_generate_report_use_case_with_renderer(
                    "html",
                )
                report_result = report_use_case.execute(
                    data_info=data_info,
                    user_request=message,
                    process_data_threads=[execution_result],
                    model="gpt-4o-mini",
                    output_dir=output_dir,
                )
                print(f"[DEBUG] セッション {session_id}: レポート生成完了")

            # 最終結果をセッション状態に保存
            print(f"[DEBUG] セッション {session_id}: 最終結果を作成中")
            
            final_result = {
                "status": "completed",
                "step": total_steps,
                "total": total_steps,
                "result": {
                    "plan": plan_result,
                    "execution": execution_result,
                    "report": report_result,
                },
                "output_dir": output_dir,  # UIで使用するために追加
            }
            
            # 完了メッセージを複数回キューに入れる（UIが確実に取得できるように）
            for _ in range(3):
                session_queue.put(final_result)
            
            self.session_results[session_id] = final_result
            print(f"[DEBUG] セッション {session_id}: ワークフロー完了！ output_dir={output_dir}")

        except Exception as e:
            # TDD Green: 幅広い例外をキャッチして適切に処理
            print(f"[DEBUG] セッション {session_id}: エラー発生 - {e}")
            import traceback
            traceback.print_exc()
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

    def _build_output_dir(self, session_id: str) -> str:
        """セッション専用の出力ディレクトリを生成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return str(Path("output") / session_id / timestamp)

    def _save_execution_artifacts(
        self,
        execution_result: DataThread,
        output_dir: str,
    ) -> list[str]:
        """コード実行結果のアーティファクトを永続化"""
        decoded_artifacts: list[tuple[Path, bytes]] = []

        for index, artifact in enumerate(execution_result.results):
            if not isinstance(artifact, dict):
                continue
            if artifact.get("type") != "image":
                continue

            image_data = artifact.get("data")
            if not image_data:
                continue

            if isinstance(image_data, str) and image_data.startswith("data:image"):
                image_data = image_data.split(",", 1)[1]

            try:
                if isinstance(image_data, bytes):
                    binary = image_data
                else:
                    binary = base64.b64decode(image_data)
            except (ValueError, TypeError):
                continue

            file_path = Path(output_dir) / f"{execution_result.process_id}_{execution_result.thread_id}_{index}.png"
            decoded_artifacts.append((file_path, binary))

        if not decoded_artifacts:
            return []

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        saved_files: list[str] = []
        for file_path, binary in decoded_artifacts:
            try:
                file_path.write_bytes(binary)
            except OSError:
                continue
            execution_result.pathes.setdefault("images", []).append(str(file_path))
            saved_files.append(str(file_path))

        return saved_files

    def _run_builtin_analysis(
        self,
        file_path: str,
        output_dir: str,
    ) -> dict[str, Any] | None:
        """ユーザー提供データに対するデフォルト分析を実行"""
        output_path = Path(output_dir)
        try:
            df = self._load_dataframe(file_path)
        except Exception as exc:  # noqa: BLE001
            print(f"[DEBUG] ビルトイン分析: データ読み込みに失敗 file={file_path}, error={exc}")
            return None

        if df.empty:
            return None

        summary = {
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "numeric_columns": df.select_dtypes(include=["number"]).columns.tolist(),
            "categorical_columns": df.select_dtypes(exclude=["number"]).columns.tolist(),
            "missing_values": int(df.isna().sum().sum()),
            "file_path": file_path,
        }

        try:
            self._create_quick_charts(df, output_path)
        except Exception as exc:  # noqa: BLE001
            print(f"[DEBUG] ビルトイン分析: 可視化作成に失敗 error={exc}")

        try:
            stats = df.describe(include="all").transpose().reset_index()
            summary["statistics"] = stats.to_dict(orient="records")
        except Exception:
            summary["statistics"] = []

        return summary

    def _load_dataframe(self, file_path: str) -> pd.DataFrame:
        """拡張子に応じてDataFrameを読み込む"""
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix in {".csv", ".txt", ".tsv"}:
            sep = "\t" if suffix == ".tsv" else ","
            return pd.read_csv(path, sep=sep)
        if suffix in {".xlsx", ".xls"}:
            return pd.read_excel(path)
        if suffix == ".parquet":
            return pd.read_parquet(path)
        if suffix == ".json":
            return pd.read_json(path)

        # フォールバック: pandasのauto-detect
        return pd.read_csv(path)

    def _create_quick_charts(self, df: pd.DataFrame, output_path: Path) -> None:
        """簡易的な可視化を生成"""
        output_path.mkdir(parents=True, exist_ok=True)
        plt.switch_backend("Agg")

        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

        if numeric_cols:
            target_col = numeric_cols[0]
            plt.figure(figsize=(8, 4))
            sns.histplot(df[target_col].dropna(), kde=True)
            plt.title(f"{target_col} の分布")
            hist_path = output_path / "distribution.png"
            plt.tight_layout()
            plt.savefig(hist_path)
            plt.close()

        if len(numeric_cols) >= 2:
            x_col, y_col = numeric_cols[:2]
            plt.figure(figsize=(6, 6))
            sns.scatterplot(x=df[x_col], y=df[y_col])
            plt.title(f"{x_col} vs {y_col}")
            scatter_path = output_path / "scatter.png"
            plt.tight_layout()
            plt.savefig(scatter_path)
            plt.close()

        if len(numeric_cols) >= 2:
            plt.figure(figsize=(6, 4))
            corr = df[numeric_cols].corr(numeric_only=True)
            sns.heatmap(corr, annot=True, fmt=".2f", cmap="Blues")
            heatmap_path = output_path / "correlation.png"
            plt.tight_layout()
            plt.savefig(heatmap_path)
            plt.close()

    def _build_builtin_report(self, summary: dict[str, Any], output_dir: str) -> str:
        """ビルトイン分析結果からMarkdownレポートを生成"""
        lines = [
            "# データ分析レポート",
            "",
            f"- 行数: {summary['rows']:,}",
            f"- 列数: {summary['columns']:,}",
            f"- 数値列: {', '.join(summary['numeric_columns']) or 'なし'}",
            f"- カテゴリ列: {', '.join(summary['categorical_columns']) or 'なし'}",
            f"- 欠損値総数: {summary['missing_values']:,}",
            "",
        ]

        stats = summary.get("statistics", [])
        if stats:
            lines.append("## 基本統計量")
            lines.append("")
            headers = ["列名", "count", "mean", "std", "min", "max"]
            lines.append("| 列名 | count | mean | std | min | max |")
            lines.append("| --- | --- | --- | --- | --- | --- |")
            for row in stats[:10]:
                lines.append(
                    "| {name} | {count} | {mean} | {std} | {min} | {max} |".format(
                        name=row.get("index", ""),
                        count=row.get("count", ""),
                        mean=row.get("mean", ""),
                        std=row.get("std", ""),
                        min=row.get("min", ""),
                        max=row.get("max", ""),
                    ),
                )
            lines.append("")

        lines.append("## 生成された可視化")
        lines.append("")

        for image in sorted(Path(output_dir).glob("*.png")):
            try:
                encoded = base64.b64encode(image.read_bytes()).decode("utf-8")
            except OSError:
                continue
            lines.append(f"![{image.name}](data:image/png;base64,{encoded})")
            lines.append("")

        lines.append("本レポートは DataAnalysisAgent のビルトイン分析機能で自動生成されました。")

        return "\n".join(lines)

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
            print(f"[DEBUG] get_job_status: セッションキューなし ({session_id})")
            return {"status": "idle"}

        try:
            msg = session_queue.get_nowait()
            print(f"[DEBUG] get_job_status: キューからメッセージ取得 - status={msg.get('status')}")
            return msg
        except queue.Empty:
            # キューが空の場合はスレッド状態を確認
            current_job = self.session_jobs.get(session_id)
            if current_job and current_job.is_alive():
                print(f"[DEBUG] get_job_status: ジョブ実行中")
                return {"status": "running"}
            if self.session_results.get(session_id):
                # 完了結果が保存されている場合
                print(f"[DEBUG] get_job_status: 完了結果を返す")
                return self.session_results[session_id]  # type: ignore[return-value]
            print(f"[DEBUG] get_job_status: idle状態")
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
                    "Session %s job did not complete within timeout",
                    session_id,
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
