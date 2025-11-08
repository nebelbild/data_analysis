"""レンダラーインターフェース

レポート出力形式の抽象化
"""

from abc import ABC, abstractmethod


class ReportRenderer(ABC):
    """レポートレンダラーの抽象基底クラス
    
    異なる出力形式（HTML、Markdown等）に対応するための
    共通インターフェースを定義
    """

    @abstractmethod
    def render(self, content: str, output_dir: str) -> None:
        """レポートをレンダリングして出力
        
        Args:
            content: レンダリング対象のコンテンツ
            output_dir: 出力先ディレクトリパス
        """
        raise NotImplementedError