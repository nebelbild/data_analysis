"""
Progress Display Component

TDD Green: テストを通す最小限の実装

進捗表示コンポーネント。
分析実行中の進捗状況を視覚的に表示。

設計原則:
- 単一責任の原則（SRP）: 進捗表示のみ
- 関心の分離: UI表示とビジネスロジックの分離
- テスト容易性: 純粋な表示関数
- Clean Architecture: UI層のみ、ビジネスロジックなし
"""

from typing import Any

import streamlit as st


def render_progress(status: dict[str, Any]) -> None:
    """
    進捗状況を表示
    
    TDD Green: 最小限の実装
    
    Args:
        status: 進捗状況を含む辞書
            - step: 現在のステップ番号
            - total: 総ステップ数
            - message: 進捗メッセージ
            
    設計判断:
    - UI非依存の入力（辞書のみ）
    - ゼロ除算エラーの防止
    - デフォルト値による堅牢性
    """
    # デフォルト値の設定
    step = status.get("step", 0)
    total = status.get("total", 1)
    message = status.get("message", "処理中...")
    
    # ゼロ除算エラーの防止
    if total <= 0:
        total = 1
    
    # 進捗率の計算（0.0 ~ 1.0）
    progress = step / total
    
    # 進捗率を0-1の範囲に制限
    progress = max(0.0, min(1.0, progress))
    
    # ステップ情報を含むメッセージの構築
    progress_text = f"{message} ({step}/{total})"
    
    # プログレスバーの表示
    st.progress(progress, text=progress_text)
