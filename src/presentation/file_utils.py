"""File Utils

ファイル処理ユーティリティ。
セキュリティ、パフォーマンス、エラーハンドリングを重視。

TDD Green Phase: テストを通す最小限の実装。

設計原則:
- 単一責任の原則（SRP）: 各関数は1つの責務のみ
- 関心の分離: セキュリティ検証とファイル読み込みを分離
- テスト容易性: 外部依存（ファイルシステム）を最小化
"""

import os
from pathlib import Path
import threading
from typing import Any

import chardet
import pandas as pd

from src.infrastructure.file_lifecycle_manager import get_file_lifecycle_manager


# 許可されたデータフォルダ（セキュリティ対策）
ALLOWED_DATA_FOLDERS = [
    "./data/",
    "data/",
]


def validate_file_path(file_path: str) -> bool:
    """ファイルパスの安全性を検証

    セキュリティ対策:
    - パス正規化（Path.resolve()）
    - シンボリックリンク拒否
    - 許可フォルダ範囲チェック
    - パストラバーサル防止

    Args:
        file_path: 検証するファイルパス

    Returns:
        True: 安全なパス, False: 危険なパス

    設計判断:
    - 存在しないファイルはFalse（セキュリティ優先）
    - シンボリックリンクは拒否（攻撃ベクトル削減）

    """
    try:
        # シンボリックリンク検出（修正: is_symlink()を使用）
        path_obj = Path(file_path)
        if path_obj.is_symlink():
            return False

        # パスの正規化（シンボリックリンク解決）
        real_path = path_obj.resolve()

        # ファイルが存在しない場合は拒否
        if not real_path.exists():
            return False

        # 許可フォルダ範囲内チェック
        for allowed_folder in ALLOWED_DATA_FOLDERS:
            allowed_real = Path(allowed_folder).resolve()
            try:
                real_path.relative_to(allowed_real)
                return True  # 許可範囲内
            except ValueError:
                continue
        # 追跡中の一時ファイルであれば許可する
        file_manager = get_file_lifecycle_manager()
        if file_manager.is_tracked_file(real_path):
            return True

        return False  # 許可範囲外

    except (OSError, ValueError):
        return False  # パス解決エラー  # パス解決エラー


def detect_file_format(file_path: str) -> str:
    """ファイル形式を拡張子から判定

    Args:
        file_path: ファイルパス

    Returns:
        "csv", "excel", "tsv"のいずれか

    Raises:
        ValueError: 未対応の形式

    設計判断:
    - 拡張子ベースの判定（シンプル、高速）
    - 大文字小文字を区別しない

    """
    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".csv":
        return "csv"
    if extension in [".xlsx", ".xls"]:
        return "excel"
    if extension == ".tsv":
        return "tsv"
    raise ValueError(f"未対応形式: {extension}")


def _select_excel_engine(file_path: str) -> str:
    """Excel ファイルの拡張子に基づいて適切なエンジンを選択

    設計原則:
    - 単一責任の原則: エンジン選択のみを担当
    - 拡張可能性: 新しい拡張子に対応しやすい
    - 明示性: どのエンジンが選択されたかを明確にする

    Args:
        file_path: Excel ファイルのパス

    Returns:
        使用するエンジン名: "calamine"

    設計判断:
    - .xls ファイルには明示的に calamine を指定（xlrd>=2 対応）
    - その他の形式でも calamine を使用（統一性とパフォーマンス）
    - 将来的にエンジン選択ロジックを変更する場合はここを修正

    """
    file_extension = Path(file_path).suffix.lower()

    if file_extension == ".xls":
        # .xls ファイル: xlrd>=2 では .xls サポートがないため calamine 必須
        return "calamine"
    # .xlsx, .xlsb 等: calamine で統一（高速・包括サポート）
    return "calamine"


def _get_excel_engine_info_message(file_path: str) -> str:
    """Excel エンジン選択の情報メッセージを生成

    Args:
        file_path: Excel ファイルのパス

    Returns:
        エンジン使用情報メッセージ

    """
    file_extension = Path(file_path).suffix.lower()

    if file_extension == ".xls":
        return "Excel読み込み: .xls ファイル専用 calamine エンジン使用"
    return "Excel読み込み: calamine エンジン使用"


def safe_preview_file(file_path: str) -> dict[str, Any]:
    """大容量ファイル対応プレビュー（セキュリティ検証付き）

    セキュリティ対策:
    - validate_file_path による事前検証（必須）
    - 許可されたディレクトリ範囲のみアクセス
    - パストラバーサル攻撃防止

    パフォーマンス対策:
    - 1000行制限
    - エンコーディング検出（3秒タイムアウト）
    - 複数形式対応（CSV/Excel/TSV）
    - エラー行スキップ

    Args:
        file_path: ファイルパス

    Returns:
        結果辞書:
        - success: bool
        - dataframe: Optional[pd.DataFrame]
        - warnings: List[str]
        - info: List[str]
        - encoding: Optional[str]
        - file_size: int

    設計判断:
    - セキュリティファースト（validate_file_path必須）
    - UI非依存（結果辞書を返すのみ）
    - エラーは例外ではなく結果辞書で返す
    - 部分的な成功を許容（エラー行スキップ）

    """
    result: dict[str, Any] = {
        "success": False,
        "dataframe": None,
        "warnings": [],
        "info": [],
        "encoding": None,
        "file_size": 0,
    }

    # セキュリティ検証（最優先）
    if not validate_file_path(file_path):
        result["warnings"].append("セキュリティエラー: 許可されていないパスです")
        return result

    try:
        # 1. ファイルサイズチェック
        file_size = os.path.getsize(file_path)
        result["file_size"] = file_size

        if file_size > 100 * 1024 * 1024:  # 100MB
            result["warnings"].append("大容量ファイル: プレビューのみ表示")

        # 2. ファイル形式判定
        file_format = detect_file_format(file_path)

        # 3. エンコーディング検出（CSVのみ、3秒タイムアウト）
        encoding = "utf-8"  # デフォルト
        if file_format == "csv":
            encoding = _detect_encoding_with_timeout(file_path, timeout=3.0)
            result["encoding"] = encoding

        # 4. 安全なプレビュー読み込み
        df: pd.DataFrame | None = None

        if file_format == "csv":
            df = pd.read_csv(
                file_path,
                nrows=1000,  # 行数制限
                encoding=encoding,
                on_bad_lines="skip",  # エラー行スキップ
            )
        elif file_format == "excel":
            # Excel エンジン選択（リファクタリング済み）
            excel_engine = _select_excel_engine(file_path)
            info_message = _get_excel_engine_info_message(file_path)

            try:
                df = pd.read_excel(
                    file_path,
                    nrows=1000,  # 行数制限
                    engine=excel_engine,
                )
                result["info"].append(info_message)
            except Exception as e:
                # エラーハンドリング: 詳細なエラー情報を提供
                result["warnings"].append(
                    f"Excel読み込みエラー ({Path(file_path).suffix}): {e!s}",
                )

        elif file_format == "tsv":
            df = pd.read_csv(
                file_path,
                sep="\t",  # タブ区切り
                nrows=1000,
                encoding=encoding,
                on_bad_lines="skip",
            )

        if df is not None:
            result["dataframe"] = df
            result["success"] = True

    except UnicodeDecodeError:
        # UTF-8フォールバック（CSVのみ）
        try:
            df = pd.read_csv(
                file_path,
                nrows=1000,
                encoding="utf-8",
                errors="ignore",  # エンコーディングエラーを無視
            )
            result["dataframe"] = df
            result["success"] = True
            result["info"].append("エンコーディングエラー: UTF-8フォールバックを使用")
        except Exception as e:
            result["warnings"].append(f"ファイル読み込みエラー: {e!s}")
    except ValueError as e:
        result["warnings"].append(f"ファイル形式エラー: {e!s}")
    except FileNotFoundError:
        result["warnings"].append("ファイルが見つかりません")
    except Exception as e:
        result["warnings"].append(f"ファイル読み込みエラー: {e!s}")

    return result


def _detect_encoding_with_timeout(
    file_path: str,
    timeout: float = 3.0,
) -> str:
    """エンコーディング検出（タイムアウト付き）

    Windows対応:
    - signal.alarm()は使用不可
    - threading.Threadでタイムアウト実装

    Args:
        file_path: ファイルパス
        timeout: タイムアウト秒数

    Returns:
        検出されたエンコーディング（デフォルト: utf-8）

    設計判断:
    - 先頭32KBのみ読み込み（パフォーマンス）
    - タイムアウト時はUTF-8フォールバック

    """
    detected_encoding = ["utf-8"]  # リストで共有（スレッド間）

    def detect_task() -> None:
        try:
            with open(file_path, "rb") as f:
                sample = f.read(32 * 1024)  # 32KB制限

            detected = chardet.detect(sample)
            detected_encoding[0] = detected.get("encoding", "utf-8") or "utf-8"
        except Exception:
            detected_encoding[0] = "utf-8"

    # threading.Threadで3秒タイムアウト
    detect_thread = threading.Thread(target=detect_task, daemon=True)
    detect_thread.start()
    detect_thread.join(timeout=timeout)  # タイムアウト待機

    if detect_thread.is_alive():
        # タイムアウト時はUTF-8フォールバック
        return "utf-8"

    return detected_encoding[0]
