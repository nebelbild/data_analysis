"""
Legacy regression tests for file cleanup behaviour.

These tests complement the presentation-layer unit tests by simulating
the full workflow orchestrator to ensure uploaded/selected files are not
deleted accidentally after the analysis run completes.
"""

import time
import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.infrastructure.di_container import DIContainer
from src.presentation.workflow_orchestrator import StreamlitWorkflowOrchestrator


@pytest.fixture
def orchestrator() -> StreamlitWorkflowOrchestrator:
    """Build an orchestrator with mocked use cases."""
    container = MagicMock(spec=DIContainer)

    mock_plan_use_case = MagicMock()
    mock_plan_use_case.execute.return_value = MagicMock(tasks=[])
    container.get_generate_plan_use_case.return_value = mock_plan_use_case

    mock_code_use_case = MagicMock()
    mock_code_use_case.execute.return_value = MagicMock(code="print('test')")
    container.get_generate_code_use_case.return_value = mock_code_use_case

    mock_execute_use_case = MagicMock()
    mock_execute_use_case.execute.return_value = MagicMock(
        stdout="test", stderr="", results=[],
    )
    container.get_execute_code_use_case.return_value = mock_execute_use_case

    mock_report_use_case = MagicMock()
    mock_report_use_case.execute.return_value = "Test Report"
    container.get_generate_report_use_case.return_value = mock_report_use_case

    return StreamlitWorkflowOrchestrator(container)


def test_workflow_cleanup_preserves_existing_dataset(orchestrator: StreamlitWorkflowOrchestrator) -> None:
    """Ensure existing datasets under ./data are not deleted as part of cleanup."""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    existing_dataset = data_dir / "important_dataset.csv"
    existing_dataset.write_text("critical,data\nvalue1,value2\n", encoding="utf-8")

    session_id = str(uuid.uuid4())
    message = "データを分析してください"

    try:
        result = orchestrator.process_user_message_async(message, session_id, str(existing_dataset))
        assert result == "STARTED"

        status = None
        for _ in range(50):
            status = orchestrator.get_job_status(session_id)
            if status["status"] in ["completed", "error"]:
                break
            time.sleep(0.1)

        assert status is not None
        assert existing_dataset.exists(), "既存の重要ファイルが削除されました"
        content = existing_dataset.read_text(encoding="utf-8")
        assert "critical,data" in content
    finally:
        existing_dataset.unlink(missing_ok=True)
        orchestrator.cleanup_session(session_id)
