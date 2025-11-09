"""ファイルブラウザーコンポーネント.

TDD Blue Phase: クリーンアーキテクチャ・Ultracite・型安全性準拠

設計原則:
- 単一責任原則 (SRP): UIレンダリングのみを担当
- 開放閉鎖原則 (OCP): 新しいファイル形式に拡張可能
- 依存性逆転 (DIP): ドメイン層のバリデーションに依存
- 明示的型安全性: Ultracite基準での型ヒント徹底
"""

from typing import Any

import streamlit as st


# Ultracite基準: 型エイリアスでStreamlitファイル型を明示
UploadedFile = Any  # streamlit.UploadedFile の型エイリアス

# Ultracite基準: 定数は明示的に定義
SUPPORTED_FILE_TYPES: list[str] = ["csv", "xlsx", "xls", "tsv"]
UPLOADER_LABEL: str = "データファイルを選択してください"
UPLOADER_HELP: str = (
    "分析するデータファイル（CSV、Excel、TSV）をアップロードしてください"
)
UPLOADER_KEY: str = "data_file_uploader"


def render_file_browser() -> UploadedFile | None:
    """ファイルブラウザーUIコンポーネントをレンダリング

    設計判断:
    - プレゼンテーション層: Streamlit UI コンポーネント
    - 責務分離: UIレンダリングのみ、バリデーションは外部委譲
    - 型安全性: 明示的な戻り値型（Ultracite基準）
    - エラーハンドリング: ドメイン層での検証

    Returns:
        Optional[UploadedFile]: アップロードされたファイルオブジェクト

    Raises:
        なし - UI層ではエラーを投げない設計

    クリーンアーキテクチャ:
    - プレゼンテーション層: Streamlit UIコンポーネント
    - ドメイン層: validate_file_path による検証
    - インフラ層: Streamlit file_uploader

    """
    uploaded_file = st.file_uploader(
        label=UPLOADER_LABEL,
        type=SUPPORTED_FILE_TYPES,
        help=UPLOADER_HELP,
        key=UPLOADER_KEY,
        on_change=None,
    )

    return uploaded_file


def get_file_display_name(uploaded_file: UploadedFile | None) -> str | None:
    """アップロードファイルの表示名を取得

    設計判断:
    - 単一責任原則: 表示名取得のみ
    - 型安全性: 明示的なNone処理
    - テスト容易性: 純粋関数として設計

    Args:
        uploaded_file: Streamlitのアップロードファイルオブジェクト

    Returns:
        Optional[str]: ファイル名、存在しない場合はNone

    """
    return uploaded_file.name if uploaded_file is not None else None
