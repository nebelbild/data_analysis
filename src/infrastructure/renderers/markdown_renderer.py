"""Markdownレンダラー

Markdown コンテンツをそのまま出力
"""

from pathlib import Path
from .renderer_interface import ReportRenderer


class MarkdownRenderer(ReportRenderer):
    """Markdownレンダラー具象クラス

    Markdownコンテンツをそのまま.mdファイルとして出力
    既存機能の維持を目的とした実装
    """

    def render(self, content: str, output_dir: str) -> None:
        """MarkdownコンテンツをMarkdownファイルとして出力

        Args:
            content: Markdownコンテンツ
            output_dir: 出力先ディレクトリパス

        Raises:
            OSError: ファイル操作でエラーが発生した場合

        """
        # 出力ディレクトリの作成
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Markdownファイル出力
        md_file = output_path / "report.md"
        md_file.write_text(content, encoding="utf-8")
