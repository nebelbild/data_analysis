"""Result Viewer Component

分析結果を表示するコンポーネント

設計原則:
- 単一責任の原則: 結果表示のみ
- 関心の分離: UI表示とファイル処理の分離
- テスト容易性: 純粋な表示関数
"""

from pathlib import Path
from typing import Any

import streamlit as st


def render_result(result: dict[str, Any]) -> None:
    """分析結果を表示する

    Args:
        result: 分析結果辞書
            - status: 実行ステータス
            - message: 完了メッセージ（オプション）
            - result: ネストされた結果（plan, execution, report）
            - output_dir: 出力ディレクトリパス（オプション）

    """
    if not result:
        print("[DEBUG] render_result: 結果がNone")
        return

    print(f"[DEBUG] render_result: keys={list(result.keys())}")

    # 完了メッセージ表示
    _render_completion_message(result)

    # 出力ディレクトリを探す（複数の場所を確認）
    output_dir = result.get("output_dir")
    
    # ネストされた結果構造の場合
    if not output_dir and "result" in result:
        nested_result = result["result"]
        print(f"[DEBUG] render_result: nested result keys={list(nested_result.keys())}")
        
        # reportからoutput_dirを取得
        if "report" in nested_result:
            report = nested_result["report"]
            print(f"[DEBUG] render_result: report type={type(report)}")
            if hasattr(report, "output_dir"):
                output_dir = report.output_dir
            elif isinstance(report, dict):
                output_dir = report.get("output_dir")
    
    print(f"[DEBUG] render_result: output_dir={output_dir}")
    
    if output_dir:
        output_path = Path(output_dir)
        if output_path.exists():
            print(f"[DEBUG] render_result: output_path exists: {output_path}")
            _render_images(output_path)
            _render_html_report(output_path)
        else:
            print(f"[DEBUG] render_result: output_path does not exist: {output_path}")
            st.warning(f"⚠️ 出力ディレクトリが見つかりません: {output_path}")
    else:
        st.info("ℹ️ 出力ファイルが生成されませんでした")


def _render_completion_message(result: dict[str, Any]) -> None:
    """完了メッセージを表示"""
    message = result.get("message", "分析が完了しました")
    st.success(f"✅ {message}")


def _render_images(output_path: Path) -> None:
    """生成された画像を表示"""
    image_files = list(output_path.glob("*.png"))

    if not image_files:
        return

    st.subheader("📊 生成されたグラフ")

    for image_file in image_files:
        st.image(str(image_file), caption=image_file.name, width="stretch")


def _render_html_report(output_path: Path) -> None:
    """HTMLレポートを表示"""
    html_file = output_path / "report.html"

    if not html_file.exists():
        return

    st.subheader("📄 分析レポート")

    # HTMLファイルを読み込んで表示
    html_content = html_file.read_text(encoding="utf-8")
    st.components.v1.html(html_content, height=600, scrolling=True)

    # ダウンロードボタン
    st.download_button(
        label="📥 レポートをダウンロード",
        data=html_file.read_bytes(),
        file_name="analysis_report.html",
        mime="text/html",
    )
