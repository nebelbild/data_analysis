"""
TDD Green Phase: LLMRepository インターフェース実装

設計関心事:
- 依存性逆転の原則（DIP）: LLM実装の詳細から分離
- テスト容易性: モック化可能なインターフェース
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generator, List


class LLMRepository(ABC):
    """
    LLM（大規模言語モデル）の抽象リポジトリ
    
    このインターフェースは、LLMプロバイダ（OpenAI, Anthropic, etc.）の
    具体的な実装から分離し、ビジネスロジックが実装詳細に依存しないようにする。
    
    設計原則:
    - 単一責任の原則（SRP）: LLM操作のみを責務とする
    - 開放閉鎖の原則（OCP）: 新しいLLMプロバイダを追加可能
    """

    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        response_format: type | None = None,
    ) -> Any:
        """
        LLMから応答を生成
        
        Args:
            messages: メッセージのリスト（役割とコンテンツ）
            model: 使用するモデル名
            temperature: ランダム性（0.0-2.0）
            max_tokens: 最大トークン数（省略可）
            response_format: 応答フォーマット（Pydanticモデル、省略可）
            
        Returns:
            Any: LLM応答（LLMResponse型を推奨）
            
        命名根拠:
        - generate: 応答生成の意図が明確
        - messages: チャット履歴を含むメッセージリスト
        - response_format: 構造化出力のための型指定
        """
        pass

    @abstractmethod
    def stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> Generator[str, None, None]:
        """
        LLMからストリーミング応答を生成
        
        Args:
            messages: メッセージのリスト
            model: 使用するモデル名
            temperature: ランダム性
            max_tokens: 最大トークン数
            
        Yields:
            str: 応答のチャンク（逐次的に生成される）
            
        命名根拠:
        - stream: ストリーミング応答の意図が明確
        - Generator: チャンクごとに yield する
        """
        ...
