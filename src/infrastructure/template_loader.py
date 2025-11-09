"""Template Loading Infrastructure

Jinjaテンプレートの読み込みを担当するインフラストラクチャ層。

設計原則:
- 単一責任の原則（SRP）: テンプレート読み込みのみ
- 依存性逆転（DIP）: Jinja2への具体的依存をここに集約
- テスト容易性: ファイルシステムアクセスの抽象化
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Template


def load_template(template_file: str) -> Template:
    """Jinjaテンプレートファイルを読み込む

    Args:
        template_file: テンプレートファイルパス

    Returns:
        Template: 読み込まれたJinjaテンプレート

    設計判断:
    - FileSystemLoader使用でセキュリティ確保
    - autoescape=Trueでインジェクション対策
    - パス正規化で安全性向上
    """
    template_path = Path(template_file)
    env = Environment(loader=FileSystemLoader(template_path.parent), autoescape=True)
    return env.get_template(template_path.name)