"""KernelManager最小実装

TDD Green Phase: Jupyter Kernelとの通信管理の最小実装
WebSocket監視、接続状態管理、エラーハンドリングの基礎機能を提供
"""

from typing import Any
from collections.abc import Callable
import logging
from enum import Enum


logger = logging.getLogger(__name__)


class KernelStatus(Enum):
    """Kernelの状態を表す列挙型"""

    IDLE = "idle"
    BUSY = "busy"
    STARTING = "starting"
    RESTARTING = "restarting"
    DEAD = "dead"
    DISCONNECTED = "disconnected"


class KernelManager:
    """Jupyter Kernel管理サービス

    Jupyter KernelとのWebSocket通信を管理し、
    接続状態監視、エラーハンドリング等を提供
    """

    def __init__(self):
        """KernelManagerの初期化"""
        self._kernel_id: str | None = None
        self._status = KernelStatus.DISCONNECTED
        self._websocket_connection: object | None = None
        self._status_callbacks: list[Callable[[KernelStatus], None]] = []
        logger.info("KernelManager初期化完了")

    def start_kernel(self, kernel_spec: str = "python3") -> str:
        """新しいKernelを起動

        Args:
            kernel_spec: Kernelの仕様（python3, etc.）

        Returns:
            str: 起動されたKernelのID

        """
        self._kernel_id = f"kernel_{kernel_spec}_001"
        self._status = KernelStatus.STARTING
        logger.info("Kernel起動開始: %s", self._kernel_id)

        # 最小実装: 即座にIDLEに移行
        self._status = KernelStatus.IDLE
        self._notify_status_change()

        return self._kernel_id

    def connect_to_kernel(self, kernel_id: str) -> None:
        """既存のKernelに接続

        Args:
            kernel_id: 接続先KernelのID

        """
        self._kernel_id = kernel_id
        self._status = KernelStatus.IDLE
        logger.info("Kernel接続: %s", kernel_id)
        self._notify_status_change()

    def get_kernel_status(self) -> KernelStatus:
        """現在のKernel状態を取得

        Returns:
            KernelStatus: Kernelの現在の状態

        """
        return self._status

    def execute_code_async(self, code: str, timeout: int = 1200) -> dict[str, Any]:
        """Kernelでコードを非同期実行

        Args:
            code: 実行するコード
            timeout: タイムアウト（秒）

        Returns:
            Dict[str, Any]: 実行結果

        """
        if self._status != KernelStatus.IDLE:
            raise RuntimeError(f"Kernel状態が実行可能ではありません: {self._status}")

        # 実行状態に変更
        self._status = KernelStatus.BUSY
        self._notify_status_change()

        try:
            # 最小実装: 固定レスポンス
            result = {
                "execution_count": 1,
                "stdout": f"# 実行されたコード:\n{code}\n# 実行完了",
                "stderr": "",
                "status": "ok",
                "execution_result": {
                    "data": {},
                    "metadata": {},
                    "execution_count": 1,
                },
            }

            # 実行完了後、IDLEに戻る
            self._status = KernelStatus.IDLE
            self._notify_status_change()

            return result

        except Exception as e:
            logger.error("コード実行中にエラー: %s", str(e))
            self._status = KernelStatus.IDLE
            self._notify_status_change()
            raise

    def restart_kernel(self) -> None:
        """Kernelを再起動"""
        if self._kernel_id:
            logger.info("Kernel再起動: %s", self._kernel_id)
            self._status = KernelStatus.RESTARTING
            self._notify_status_change()

            # 最小実装: 即座にIDLEに移行
            self._status = KernelStatus.IDLE
            self._notify_status_change()

    def shutdown_kernel(self) -> None:
        """Kernelを終了"""
        if self._kernel_id:
            logger.info("Kernel終了: %s", self._kernel_id)
            self._status = KernelStatus.DEAD
            self._notify_status_change()
            self._kernel_id = None

    def add_status_callback(self, callback: Callable[[KernelStatus], None]) -> None:
        """状態変更コールバックを追加

        Args:
            callback: 状態変更時に呼び出されるコールバック関数

        """
        self._status_callbacks.append(callback)

    def remove_status_callback(self, callback: Callable[[KernelStatus], None]) -> None:
        """状態変更コールバックを削除

        Args:
            callback: 削除するコールバック関数

        """
        if callback in self._status_callbacks:
            self._status_callbacks.remove(callback)

    def _notify_status_change(self) -> None:
        """状態変更を通知"""
        for callback in self._status_callbacks:
            try:
                callback(self._status)
            except Exception as e:
                logger.error("状態変更コールバックエラー: %s", str(e))

    def get_kernel_info(self) -> dict[str, Any]:
        """Kernel情報を取得

        Returns:
            Dict[str, Any]: Kernel情報

        """
        return {
            "kernel_id": self._kernel_id,
            "status": self._status.value,
            "language_info": {
                "name": "python",
                "version": "3.9.0",
                "mimetype": "text/x-python",
                "file_extension": ".py",
            },
            "protocol_version": "5.3",
        }
