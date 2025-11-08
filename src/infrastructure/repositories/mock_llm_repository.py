"""テスト用モックLLMリポジトリ

Azure OpenAI APIキーが不要なテスト用実装
"""

from src.domain.repositories.llm_repository import LLMRepository


class MockLLMRepository(LLMRepository):
    """テスト用のモックLLMリポジトリ"""

    def __init__(self):
        pass

    def generate_text(self, prompt: str, max_tokens: int = 1000) -> str:
        """テスト用の固定レスポンスを返す"""
        if "分析コード" in prompt or "matplotlib" in prompt or "seaborn" in prompt:
            return """```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# データの基本統計
print("=== データセット基本情報 ===")
print(f"データ数: {len(df)}")
print(f"カラム数: {len(df.columns)}")
print()

# 数値項目の分布を確認
numeric_cols = ['purchase_amount', 'click_count', 'conversion_rate', 'score']

# 購入金額の分布
plt.figure(figsize=(12, 8))

# 1. 購入金額の分布
plt.subplot(2, 2, 1)
plt.hist(df['purchase_amount'], bins=30, alpha=0.7)
plt.title('Purchase Amount Distribution')
plt.xlabel('Purchase Amount')
plt.ylabel('Frequency')

# 2. クリック数vs購入金額
plt.subplot(2, 2, 2)
plt.scatter(df['click_count'], df['purchase_amount'], alpha=0.6)
plt.title('Click Count vs Purchase Amount')
plt.xlabel('Click Count')
plt.ylabel('Purchase Amount')

# 3. コンバージョン率の分布
plt.subplot(2, 2, 3)
plt.hist(df['conversion_rate'], bins=20, alpha=0.7)
plt.title('Conversion Rate Distribution')
plt.xlabel('Conversion Rate (%)')
plt.ylabel('Frequency')

# 4. チャネル別の購入金額
plt.subplot(2, 2, 4)
sns.boxplot(data=df, x='channel_id', y='purchase_amount')
plt.xticks(rotation=45)
plt.title('Purchase Amount by Channel')

plt.tight_layout()
plt.show()

# キャンペーンタイプ別の成功率
campaign_success = df.groupby('campaign_type')['is_successful'].agg(['count', 'sum', 'mean']).round(3)
print("=== キャンペーンタイプ別成功率 ===")
print(campaign_success)
```"""

        if "レビュー" in prompt or "review" in prompt:
            return """## 分析結果レビュー

### 📊 データの概要
- 総レコード数: 500件のキャンペーンデータ
- 19項目の多様な指標を含む包括的なデータセット
- 欠損値なし、データ品質良好

### 📈 主要な発見
1. **購入金額の分布**: 幅広い範囲（0〜500円）に分散
2. **コンバージョン率**: 平均26.76%、最大100%
3. **チャネル効果**: Display Adsが最も多い
4. **成功率**: キャンペーンタイプごとに異なる傾向

### 🎯 ビジネス示唆
- チャネル別の効果測定が可能
- コンバージョン最適化の余地あり
- 時間軸での分析（曜日、時間帯）が有効

### ⚠️ 注意点
- サンプルサイズ（500件）は中規模
- 季節性やトレンドの考慮が必要
- 統計的有意性の検定推奨"""

        if "レポート" in prompt or "report" in prompt:
            return """# データ分析レポート

## エグゼクティブサマリー
本分析では、500件のマーケティングキャンペーンデータを対象に、各チャネルの効果とコンバージョン特性を詳細に分析しました。

## 分析結果ハイライト

### 1. チャネル別パフォーマンス
- **Display Ads**: 最も多くのキャンペーンで使用
- **Search Engine**: 高いコンバージョン率を示す傾向
- **Social Media**: バランスの取れた成果

### 2. コンバージョン分析
- 平均コンバージョン率: 26.76%
- 最適化の余地: 約73%の改善可能性
- 成功要因: クリック数との正の相関

### 3. 購入行動パターン
- 購入金額の分布: 二極化傾向（0円と高額購入）
- ピーク時間帯: 午後の活動が活発
- 曜日効果: 平日の成果が良好

## 戦略的提言

### 短期施策
1. Display Adsの最適化によるROI向上
2. コンバージョン率の低いセグメントの改善
3. 時間帯別の配信調整

### 中長期施策
1. チャネル横断的な統合分析
2. 顧客セグメント別の戦略立案
3. 予測モデルの構築

## 結論
現在のマーケティング活動は一定の成果を上げているが、データドリブンな最適化により更なる成長が期待できます。"""

        return "テスト用のモックレスポンスです。実際のAI分析結果ではありません。"
