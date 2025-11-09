"""
Data Preview Component

TDD Green: テストを通す最小限の実装

データプレビュー表示コンポーネント。
safe_preview_file関数を活用してファイル内容を安全に表示。

設計原則:
- 単一責任の原則（SRP）: データプレビュー表示のみ
- 関心の分離: ファイル処理はfile_utilsに委譲
- テスト容易性: 純粋な表示関数
- Clean Architecture: UI層のみ、ビジネスロジックなし
"""

import os
from typing import Optional

import pandas as pd
import streamlit as st

from src.presentation.file_utils import safe_preview_file


def render_data_preview(file_path: Optional[str]) -> None:
    """
    データプレビューを表示
    
    TDD Green: 最小限の実装
    
    Args:
        file_path: プレビューするファイルパス
        
    設計判断:
    - UI非依存の入力（ファイルパスのみ）
    - エラーハンドリングをUI層で実装
    - 情報表示の責務分離（警告/情報/データ）
    """
    if not file_path:
        return
    
    st.subheader("👀 データプレビュー")
    
    # ファイルプレビュー実行
    with st.spinner("ファイルを読み込み中..."):
        preview_result = safe_preview_file(file_path)
    
    # 結果の表示
    _render_preview_messages(preview_result)
    
    if preview_result["success"]:
        _render_preview_data(preview_result, file_path)
    else:
        st.error("❌ ファイルプレビューに失敗しました")


def _render_preview_messages(preview_result: dict) -> None:
    """
    プレビュー結果のメッセージを表示
    
    TDD Green: 最小限の実装
    
    Args:
        preview_result: safe_preview_fileの結果
        
    設計判断:
    - メッセージ種別による表示分離
    - ユーザーフィードバックの一元化
    """
    # 警告メッセージ表示
    for warning in preview_result.get("warnings", []):
        st.warning(f"⚠️ {warning}")
    
    # 情報メッセージ表示
    for info in preview_result.get("info", []):
        st.info(f"ℹ️ {info}")


def _render_preview_data(preview_result: dict, file_path: str) -> None:
    """
    プレビューデータを表示
    
    TDD Green: 最小限の実装
    
    Args:
        preview_result: safe_preview_fileの結果
        file_path: ファイルパス（表示用）
        
    設計判断:
    - データフレーム表示の最適化
    - ファイル情報の構造化表示
    - 制限事項の明示
    """
    dataframe = preview_result.get("dataframe")
    if dataframe is None:
        return
    
    # ファイル情報表示
    _render_file_info(preview_result, file_path)
    
    # データフレーム表示
    st.dataframe(
        dataframe,
        use_container_width=True,
        height=400,  # 固定高さで見やすく
    )
    
    # データ統計情報
    _render_data_statistics(dataframe)
    
    # 制限事項の表示
    st.caption("📝 最大1000行まで表示されます。完全なデータは分析時に使用されます。")


def _render_file_info(preview_result: dict, file_path: str) -> None:
    """
    ファイル情報を表示
    
    TDD Green: 最小限の実装
    
    Args:
        preview_result: safe_preview_fileの結果
        file_path: ファイルパス
        
    設計判断:
    - 構造化された情報表示
    - ファイル名の表示最適化（セッション状態考慮）
    """
    # 表示用ファイル名の決定
    display_name = _get_display_filename(file_path)
    
    # ファイル情報をカラムで表示
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📄 ファイル名", display_name)
    
    with col2:
        file_size = preview_result.get("file_size", 0)
        size_mb = file_size / (1024 * 1024) if file_size > 0 else 0
        st.metric("📊 ファイルサイズ", f"{size_mb:.2f} MB")
    
    with col3:
        encoding = preview_result.get("encoding", "不明")
        if encoding:
            st.metric("🔤 エンコーディング", encoding)


def _render_data_statistics(dataframe: Optional[pd.DataFrame]) -> None:
    """
    データ統計情報を表示
    
    TDD Green: 最小限の実装
    
    Args:
        dataframe: pandas DataFrame
        
    設計判断:
    - 基本統計のみ表示（詳細は分析結果で）
    - 視覚的に分かりやすい表示
    """
    if dataframe is None or dataframe.empty:
        return
    
    st.markdown("**📈 データ概要**")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("行数", f"{len(dataframe):,}")
    
    with col2:
        st.metric("列数", f"{len(dataframe.columns):,}")
    
    with col3:
        # 数値列の数
        numeric_cols = dataframe.select_dtypes(include=["number"]).columns
        st.metric("数値列", f"{len(numeric_cols)}")
    
    with col4:
        # 欠損値の数
        missing_count = dataframe.isnull().sum().sum()
        st.metric("欠損値", f"{missing_count:,}")
    
    # 列情報の表示（展開可能）
    with st.expander("📋 列情報"):
        column_info = []
        for col in dataframe.columns:
            dtype = str(dataframe[col].dtype)
            non_null = dataframe[col].count()
            null_count = len(dataframe) - non_null
            
            column_info.append({
                "列名": col,
                "データ型": dtype,
                "非NULL数": non_null,
                "NULL数": null_count,
            })
        
        info_df = pd.DataFrame(column_info)
        st.dataframe(info_df, use_container_width=True)


def _get_display_filename(file_path: str) -> str:
    """
    表示用ファイル名を取得
    
    TDD Green: 最小限の実装
    
    Args:
        file_path: ファイルパス
        
    Returns:
        表示用ファイル名
        
    設計判断:
    - セッション状態の元ファイル名を優先
    - フォールバック: パスからファイル名抽出
    """
    # セッション状態から元のファイル名を取得
    if hasattr(st.session_state, "original_filename") and st.session_state.original_filename:
        return st.session_state.original_filename
    
    # フォールバック: パスからファイル名を抽出
    return os.path.basename(file_path)
