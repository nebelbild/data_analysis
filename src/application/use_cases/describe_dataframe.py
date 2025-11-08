"""データフレーム記述ユースケース"""

import io
import pandas as pd
from src.llms.load_template import load_template


def _to_markdown_safe(frame: pd.DataFrame) -> str:
    """
    Convert a DataFrame to markdown, falling back to plain text when tabulate is unavailable.
    """
    try:
        return frame.to_markdown()
    except ImportError:
        return frame.to_string()


class DescribeDataframeUseCase:
    """データフレーム記述ユースケース
    
    CSVファイルからDataFrameを作成し、
    その構造と統計情報を記述したテキストを生成する
    """

    def __init__(self):
        """初期化"""
        pass

    def execute(
        self,
        file_object: io.BytesIO,
        template_file: str = "src/prompts/describe_dataframe.jinja",
    ) -> str:
        """データフレーム記述の実行
        
        Args:
            file_object: CSVファイルのバイトストリーム
            template_file: 使用するテンプレートファイルパス
            
        Returns:
            str: フォーマット済みのデータフレーム記述
        """
        # CSVファイルを読み込み、データフレームを作成
        df = pd.read_csv(file_object)
        
        # データフレームの概要情報を取得
        buf = io.StringIO()
        df.info(buf=buf)
        df_info = buf.getvalue()
        
        # テンプレートを読み込み、データフレーム情報を構築して返す
        template = load_template(template_file)
        if len(df) == 0:
            df_sample = df.head(0)
            df_description = pd.DataFrame({"detail": ["データが存在しません"]})
        else:
            df_sample = df.sample(min(len(df), 5))
            try:
                df_description = df.describe()
            except ValueError:
                df_description = pd.DataFrame({"detail": ["統計量を計算できません"]})

        return template.render(
            df_info=df_info,
            df_sample=_to_markdown_safe(df_sample),
            df_describe=_to_markdown_safe(df_description),
        )
