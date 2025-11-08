"""
JupyterSandboxRepository依存性注入統合実装

TDD Refactor Phase: クリーンアーキテクチャ、SOLID原則、関心の分離強化
VisualizationServiceとKernelManagerを依存性注入で受け取る設計に改善
"""
from typing import Dict, Any, Optional, Protocol
import logging


logger = logging.getLogger(__name__)


class VisualizationServiceProtocol(Protocol):
    """VisualizationServiceのプロトコル定義（依存性逆転の原則）"""
    
    def enable_realtime_plotting(self) -> None:
        """リアルタイムプロッティングを有効化"""
    
    def capture_plot(self, plot_type: str, plot_data: Dict[str, Any]) -> str:
        """プロットをキャプチャして保存"""
    
    def capture_dataframe(self, dataframe_data: Dict[str, Any]) -> str:
        """データフレームをキャプチャして保存"""
    
    def get_visualization_summary(self) -> Dict[str, Any]:
        """可視化データのサマリーを取得"""


class KernelManagerProtocol(Protocol):
    """KernelManagerのプロトコル定義（依存性逆転の原則）"""
    
    def start_kernel(self, kernel_spec: str = "python3") -> str:
        """新しいKernelを起動"""
    
    def connect_to_kernel(self, kernel_id: str) -> None:
        """既存のKernelに接続"""
    
    def execute_code_async(self, code: str, timeout: int = 1200) -> Dict[str, Any]:
        """Kernelでコードを非同期実行"""
    
    def get_kernel_status(self) -> Any:
        """現在のKernel状態を取得"""
    
    def get_kernel_info(self) -> Dict[str, Any]:
        """Kernel情報を取得"""
    
    def shutdown_kernel(self) -> None:
        """Kernelを終了"""


class JupyterSandboxRepository:
    """
    Jupyter-based Sandbox Repository実装（リファクタリング版）
    
    SOLID原則適用:
    - 単一責任の原則: サンドボックス操作に専念
    - 開放閉鎖の原則: 拡張に開いて修正に閉じている
    - リスコフの置換原則: SandboxRepositoryを完全に置換可能
    - インタフェース分離の原則: 必要な機能のみを依存
    - 依存性逆転の原則: 抽象（Protocol）に依存
    """
    
    def __init__(
        self,
        visualization_service: VisualizationServiceProtocol,
        kernel_manager: KernelManagerProtocol
    ):
        """
        JupyterSandboxRepositoryの初期化（依存性注入）
        
        Args:
            visualization_service: 可視化サービス
            kernel_manager: Kernel管理サービス
        """
        self._sandbox_id: Optional[str] = None
        self._visualization_service = visualization_service
        self._kernel_manager = kernel_manager
        logger.info("JupyterSandboxRepository初期化完了（DI統合）")
    
    def create(self, timeout: int = 600) -> str:
        """
        新しいJupyterサンドボックスを作成
        
        単一責任: サンドボックス作成のみに集中
        
        Args:
            timeout: タイムアウト時間（現在未使用だが将来の拡張用）
        """
        kernel_id = self._kernel_manager.start_kernel()
        self._sandbox_id = f"jupyter-sandbox-{kernel_id}"
        
        # 可視化機能を有効化
        self._visualization_service.enable_realtime_plotting()
        
        logger.info("Jupyterサンドボックス作成: %s", self._sandbox_id)
        return self._sandbox_id
    
    def connect(self, sandbox_id: str) -> None:
        """
        既存のJupyterサンドボックスに接続
        
        関心の分離: 接続ロジックをKernelManagerに委譲
        """
        self._sandbox_id = sandbox_id
        # sandbox_idからkernel_idを抽出（簡易実装）
        kernel_id = sandbox_id.replace("jupyter-sandbox-", "")
        self._kernel_manager.connect_to_kernel(kernel_id)
        logger.info("Jupyterサンドボックス接続: %s", sandbox_id)
    
    def execute_code(self, code: str, timeout: int = 1200) -> Dict[str, Any]:
        """
        JupyterサンドボックスでPythonコードを実行
        
        関心の分離: 実行はKernelManager、可視化はVisualizationServiceに委譲
        """
        if not self._sandbox_id:
            raise RuntimeError("サンドボックスが作成または接続されていません")
        
        # Kernelでコード実行
        execution_result = self._kernel_manager.execute_code_async(code, timeout)
        
        # 可視化データの処理
        visualization_summary = self._visualization_service.get_visualization_summary()
        
        # 結果を統合
        return {
            **execution_result,
            "visualization_data": visualization_summary
        }
    
    def upload_file(self, file_path: str, content: bytes) -> None:
        """
        Jupyterサンドボックスにファイルをアップロード
        
        単一責任: ファイルアップロード機能のみ
        """
        if not self._sandbox_id:
            raise RuntimeError("サンドボックスが作成または接続されていません")
        
        logger.info("ファイルアップロード: %s (%d bytes)", file_path, len(content))
        # 実装詳細は将来のイテレーションで追加
    
    def kill(self) -> None:
        """
        Jupyterサンドボックスを停止・削除
        
        リソース管理: 適切なクリーンアップを実行
        """
        if self._sandbox_id:
            logger.info("Jupyterサンドボックス停止: %s", self._sandbox_id)
            self._kernel_manager.shutdown_kernel()
            self._sandbox_id = None
    
    # 可視化機能固有メソッド（関心の分離適用）
    
    def get_visualization_output(self) -> Dict[str, Any]:
        """
        可視化出力を取得
        
        委譲パターン: VisualizationServiceに処理を委譲
        """
        return self._visualization_service.get_visualization_summary()
    
    def enable_realtime_plotting(self) -> None:
        """
        リアルタイムプロッティングを有効化
        
        委譲パターン: VisualizationServiceに処理を委譲
        """
        self._visualization_service.enable_realtime_plotting()
    
    def get_kernel_status(self) -> str:
        """
        Kernelの状態を取得
        
        委譲パターン: KernelManagerに処理を委譲
        """
        status = self._kernel_manager.get_kernel_status()
        return status.value if hasattr(status, 'value') else str(status)
    
    def get_notebook_content(self) -> Dict[str, Any]:
        """
        ノートブックの内容を取得
        
        統合機能: KernelとVisualizationの情報を統合
        """
        kernel_info = self._kernel_manager.get_kernel_info()
        visualization_summary = self._visualization_service.get_visualization_summary()
        
        return {
            "cells": [],  # 将来の実装で追加
            "metadata": {
                "kernelspec": kernel_info.get("language_info", {}),
                "visualization": visualization_summary
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }