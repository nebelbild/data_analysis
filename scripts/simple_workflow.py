"""
Simple Data Analysis Workflow

実際のPythonコード実行とグラフ生成を行うシンプルなワークフロー
途中経過を表示するUI付き
"""

import pandas as pd
import sys
import os
import io
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.di_container import DIContainer


class SimpleWorkflowUI:
    """途中経過表示UI"""
    
    def __init__(self):
        self.step_count = 0
        
    def show_step(self, title, description=""):
        """ステップ表示"""
        self.step_count += 1
        print(f"\n{'='*60}")
        print(f"Step {self.step_count}: {title}")
        if description:
            print(f"Description: {description}")
        print(f"{'='*60}")
        
    def show_progress(self, message):
        """進行状況表示"""
        print(f"[PROGRESS] {message}")
        
    def show_result(self, title, content):
        """結果表示"""
        print(f"\n[RESULT] {title}:")
        print("-" * 40)
        try:
            print(content)
        except UnicodeEncodeError:
            safe_text = content.encode("cp932", errors="replace").decode("cp932", errors="replace")
            print(safe_text)
        print("-" * 40)
        
    def show_error(self, error_message):
        """エラー表示"""
        print(f"\n[ERROR] {error_message}")


def main():
    """メインワークフロー"""
    ui = SimpleWorkflowUI()
    
    # 環境変数の読み込み確認（デバッグ用）
    api_key = os.environ.get('AZURE_OPENAI_API_KEY')
    endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')
    print(f"[DEBUG] AZURE_OPENAI_API_KEY: {'設定済み' if api_key else '未設定'}")
    print(f"[DEBUG] AZURE_OPENAI_ENDPOINT: {endpoint if endpoint else '未設定'}")
    
    # セッションIDを生成（タイムスタンプベース）
    from datetime import datetime
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # データファイルパス
    data_file = project_root / "data" / "sample.csv"
    
    if not data_file.exists():
        ui.show_error(f"データファイルが見つかりません: {data_file}")
        return
    
    # セッション用の出力ディレクトリ作成
    session_output_dir = project_root / "output" / session_id
    session_output_dir.mkdir(parents=True, exist_ok=True)
    ui.show_progress(f"セッション出力ディレクトリ: {session_output_dir}")
    
    # DIコンテナ初期化
    container = DIContainer()
    
    # サンドボックス初期化
    sandbox_repo = container.get_sandbox_repository()
    sandbox_repo.create()  # Jupyter kernelを起動
    
    try:
        # Step 1: データフレーム読み込み
        ui.show_step("データフレーム読み込み", "CSVファイルからデータを読み込みます")
        ui.show_progress("CSVファイルを読み込み中...")
        
        df = pd.read_csv(data_file)
        ui.show_result("データフレーム情報", f"Shape: {df.shape}\nColumns: {list(df.columns)}")
        
        # データフレームをJupyterカーネルに注入
        ui.show_progress("データフレームをJupyterカーネルに注入中...")
        df_csv = df.to_csv(index=False)
        inject_code = f"""
import pandas as pd
import io

# CSVデータをデータフレームとして読み込む
csv_data = '''{df_csv}'''
df = pd.read_csv(io.StringIO(csv_data))
print(f"データフレーム注入完了: {{df.shape}}")
"""
        inject_result = sandbox_repo.execute_code(inject_code)
        print(f"[DEBUG] 注入結果の全体構造: {inject_result}")
        print(f"[DEBUG] stdout: {inject_result.get('logs', {}).get('stdout', [])}")
        print(f"[DEBUG] stderr: {inject_result.get('logs', {}).get('stderr', [])}")
        
        # Step 2: データフレーム概要取得
        ui.show_step("データフレーム分析", "データの概要と統計情報を取得します")
        ui.show_progress("データフレームを分析中...")
        
        # CSVファイルをバイトストリームに変換してDescribeDataframeUseCaseで処理
        csv_buffer = io.BytesIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        describe_use_case = container.get_describe_dataframe_use_case()
        description_result = describe_use_case.execute(csv_buffer)
        
        ui.show_result("データ分析結果", description_result)
        
        # Step 3: 分析計画生成（複数タスクに分解）
        ui.show_step("分析計画生成", "ユーザーリクエストを複数の分析タスクに分解します")
        ui.show_progress("AIが分析計画を生成中...")
        
        user_request = "データを詳しく分析して、散布図、相関行列、統計分析を含む複数のグラフを生成してください。購入金額、クリック数、コンバージョン率、チャネル別の分析を含めてください。"
        
        generate_plan_use_case = container.get_generate_plan_use_case()
        plan = generate_plan_use_case.execute(
            data_info=description_result,
            user_request=user_request,
            model="gpt-4o-mini"
        )
        
        ui.show_result("生成された計画", f"{len(plan.tasks)}個のタスクを実行します")
        for idx, task in enumerate(plan.tasks):
            print(f"  タスク{idx+1}: {task.hypothesis}")
        
        # Step 4: 各タスクを順次実行
        all_execution_results = []
        all_images = []
        
        generate_code_use_case = container.get_generate_code_use_case()
        execute_use_case = container.get_execute_code_use_case()
        
        for idx, task in enumerate(plan.tasks):
            ui.show_step(f"タスク{idx+1}実行", task.hypothesis)
            ui.show_progress(f"タスク{idx+1}のコードを生成中...")
            
            code_result = generate_code_use_case.execute(
                description_result, 
                task.hypothesis,
                model="gpt-4o-mini"
            )
            
            def _decode_generated_code(code: str | None) -> str:
                if not code:
                    return ""
                if "\\u" in code:
                    try:
                        return code.encode().decode('unicode_escape')
                    except UnicodeDecodeError:
                        return code
                return code
            
            # エスケープシーケンスが含まれる場合のみ変換
            actual_code = _decode_generated_code(code_result.code)
            ui.show_result(f"タスク{idx+1}のコード", actual_code)
            
            # コード構文を自動修正
            corrected_code = actual_code.replace(
                'df.groupby("channel_id")[\n        "purchase_amount", "click_count", "conversion_rate"\n    ].agg',
                'df.groupby("channel_id")[["purchase_amount", "click_count", "conversion_rate"]].agg'
            )
            
            ui.show_progress(f"タスク{idx+1}のコードを実行中...")
            
            # dfの存在確認とshow_plot関数の定義を前置
            check_df_code = """
if 'df' not in globals():
    raise NameError("df is not defined. Please inject dataframe first.")
print(f"df exists with shape: {df.shape}")

# show_plot関数を定義（毎回定義して確実に利用可能にする）
import io
from IPython.display import display, Image
import matplotlib.pyplot as plt

def show_plot():
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    display(Image(buffer.getvalue()))
    buffer.close()
    plt.close()
"""
            final_code = check_df_code + "\n" + corrected_code
            
            execution_result = execute_use_case.execute(
                process_id=f"simple_workflow_{idx}",
                thread_id=1,
                code=final_code,
                user_request=task.hypothesis
            )
            
            ui.show_result(f"タスク{idx+1}の実行結果", execution_result.stdout or "実行完了")
            
            # resultsから画像データを抽出して保存
            task_images = []
            for i, result in enumerate(execution_result.results):
                if result.get("type") == "image" and result.get("data"):
                    import base64
                    from PIL import Image
                    from io import BytesIO
                    
                    image_data = result["data"]
                    image = Image.open(BytesIO(base64.b64decode(image_data)))
                    image_filename = f"{execution_result.process_id}_{execution_result.thread_id}_{i}.png"
                    image_path = session_output_dir / image_filename
                    image.save(image_path)
                    task_images.append(image_filename)
                    ui.show_progress(f"画像を保存しました: {image_filename}")
            
            if task_images:
                ui.show_result(f"タスク{idx+1}の画像", f"{len(task_images)}個の画像が生成されました")
            
            all_execution_results.append(execution_result)
            all_images.extend(task_images)
        
        ui.show_result("全タスクの画像", f"合計{len(all_images)}個の画像が生成・保存されました")
        
        # Step 5: レビュー生成（最後のタスクに対して）
        ui.show_step("結果レビュー", "実行結果の分析とレビューを生成します")
        ui.show_progress("AIがレビューを作成中...")
        
        review_use_case = container.get_generate_review_use_case()
        review_result = review_use_case.execute(
            data_info=description_result,
            user_request=user_request,
            data_thread=all_execution_results[-1],
            has_results=len(all_images) > 0,
            model="gpt-4o-mini"
        )
        
        ui.show_result("レビュー結果", review_result.observation)
        
        # Step 6: 最終レポート生成
        ui.show_step("レポート生成", "全体の分析レポートを作成します")
        ui.show_progress("最終レポートを生成中...")
        
        # HTMLレンダラー付きのレポートユースケースを使用
        report_use_case = container.get_generate_report_use_case_with_renderer(output_format="html")
        
        report_response = report_use_case.execute(
            data_info=description_result,
            user_request=user_request,
            process_data_threads=all_execution_results,
            model="gpt-4o-mini",
            output_dir=str(session_output_dir)
        )
        
        # executeメソッドは文字列を直接返す
        report_result = report_response
        ui.show_result("最終レポート", report_result)
        
        # レポートをマークダウンファイルにも保存
        report_file = session_output_dir / "analysis_report.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(f"# データ分析レポート\n\n")
            f.write(f"## データ概要\n\n{description_result}\n\n")
            f.write(f"## 実行タスク数\n\n{len(all_execution_results)}個のタスクを実行しました\n\n")
            for idx, result in enumerate(all_execution_results):
                f.write(f"### タスク{idx+1}\n\n")
                f.write(f"**実行結果:**\n\n{result.stdout}\n\n")
                if result.stderr:
                    f.write(f"**エラー:**\n\n```\n{result.stderr}\n```\n\n")
            f.write(f"## レビュー\n\n{review_result.observation}\n\n")
            f.write(f"## 最終レポート\n\n{report_result}\n\n")
        
        ui.show_progress(f"マークダウンレポートを保存しました: {report_file}")
        ui.show_progress(f"HTMLレポートが生成されました: {session_output_dir}/report.html")
        
        # 完了メッセージ
        print("\n" + "="*60)
        print("ワークフロー完了！")
        print(f"セッションID: {session_id}")
        print(f"HTMLレポート: {session_output_dir}/report.html")
        print(f"Markdownレポート: {report_file}")
        print(f"画像ファイル: {len(all_images)}個")
        print("="*60)
        
    except Exception as e:
        ui.show_error(f"ワークフロー実行中にエラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
