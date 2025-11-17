"""LLM Response Domain Entity

LLMからのレスポンスを表現するドメインエンティティ。

設計原則:
- 単一責任の原則（SRP）: LLMレスポンスの構造定義のみ  
- ドメイン中心設計: インフラ実装の詳細に依存しない
- テスト容易性: 純粋なデータクラス
"""

from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    """LLMからのレスポンス構造

    LLMのレスポンス情報を構造化して保持する。
    コスト計算やトークン数の追跡を含む。
    """

    messages: list
    content: str | BaseModel
    model: str
    created_at: int
    input_tokens: int
    output_tokens: int
    cost: float | None = Field(default=None, init=False)