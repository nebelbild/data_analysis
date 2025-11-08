"""HTMLレンダラー

Markdown コンテンツをHTMLに変換して出力
"""

import shutil
from pathlib import Path
from .renderer_interface import ReportRenderer

try:
    import markdown
except ImportError:
    markdown = None


class HTMLRenderer(ReportRenderer):
    """HTMLレンダラー具象クラス
    
    MarkdownコンテンツをHTMLに変換し、
    CSSスタイルと共に出力する
    """

    def render(self, content: str, output_dir: str) -> None:
        """MarkdownコンテンツをHTMLに変換して出力
        
        Args:
            content: Markdownコンテンツ
            output_dir: 出力先ディレクトリパス
            
        Raises:
            ImportError: markdownライブラリがインストールされていない場合
            OSError: ファイル操作でエラーが発生した場合
        """
        if markdown is None:
            raise ImportError("markdown library is required for HTML rendering")
        
        # 出力ディレクトリの作成
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # シンプルなコードブロック処理
        import re
        import html
        
        # コードブロックを<pre><code>に変換
        def replace_code_block(match):
            language = match.group(1) if match.group(1) else "python"
            code_content = match.group(2)
            escaped_code = html.escape(code_content.strip())
            return f'<pre><code class="language-{language}">{escaped_code}</code></pre>'
        
        # コードブロック処理
        processed_content = re.sub(
            r'```(\w*)\n(.*?)\n```', 
            replace_code_block, 
            content, 
            flags=re.DOTALL
        )
        
        # MarkdownをHTMLに変換
        html_content = markdown.markdown(
            processed_content, 
            extensions=['tables']
        )
        
        # HTMLテンプレートの作成
        full_html = self._create_html_template(html_content)
        
        # HTMLファイル出力
        html_file = output_path / "report.html"
        html_file.write_text(full_html, encoding='utf-8')
        
        # CSSファイルのコピー
        self._copy_css_file(output_path)

    def _create_html_template(self, body_content: str) -> str:
        """HTMLテンプレートの作成
        
        Args:
            body_content: ボディに挿入するHTMLコンテンツ
            
        Returns:
            str: 完全なHTMLドキュメント
        """
        from datetime import datetime
        
        # 現在の日時を取得
        current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        
        return f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="generator" content="DataAnalysisAgent">
    <title>分析レポート</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>データ分析レポート</h1>
            <p class="report-info">生成日時: {current_time}</p>
        </header>
        <main>
            {body_content}
        </main>
        <footer>
            <hr>
            <p class="footer-text">このレポートは DataAnalysisAgent により自動生成されました。</p>
        </footer>
    </div>
</body>
</html>"""

    def _copy_css_file(self, output_path: Path) -> None:
        """CSSファイルをコピー
        
        Args:
            output_path: 出力先ディレクトリパス
        """
        # CSSソースファイルパス（現在は最小実装）
        css_source = Path(__file__).parent.parent.parent / "static" / "report_style.css"
        css_dest = output_path / "style.css"
        
        if css_source.exists():
            shutil.copy(css_source, css_dest)
        else:
            # CSSファイルが存在しない場合、基本的なCSSを作成
            basic_css = """
/* 基本的なレポートスタイル */
.container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
}

h1, h2, h3, h4, h5, h6 {
    color: #333;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
}

h1 {
    border-bottom: 2px solid #eee;
    padding-bottom: 0.3em;
}

pre {
    background: #f4f4f4;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 1em;
    overflow-x: auto;
}

code {
    background: #f4f4f4;
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-family: Consolas, Monaco, 'Courier New', monospace;
}

table {
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
}

th, td {
    border: 1px solid #ddd;
    padding: 0.5em;
    text-align: left;
}

th {
    background-color: #f2f2f2;
}

blockquote {
    border-left: 4px solid #ddd;
    margin: 0;
    padding-left: 1em;
    color: #666;
}
"""
            css_dest.write_text(basic_css, encoding='utf-8')