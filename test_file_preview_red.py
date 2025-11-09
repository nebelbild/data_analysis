"""
TDD Red Phase: ファイルプレビュー機能のテスト

handle_file_uploaded()が正しく呼ばれ、プレビュー機能が動作することを確認するテスト
"""

import pytest
from unittest.mock import MagicMock, patch
import streamlit as st


def test_file_preview_flow_integration():
    """
    TDD Red Phase: ファイルアップロード→プレビュー表示のフローをテスト
    
    現在の問題:
    - show_file_upload_ui()がTrueを返すが、handle_file_uploaded()が呼ばれない
    - 結果としてプレビューが表示されない
    """
    from src.presentation.chat_ui import show_file_upload_ui, handle_file_uploaded
    from src.presentation.session_state_manager import SessionStateManager
    
    # Given: 有効なファイルがアップロードされた状態をシミュレート
    with patch('src.presentation.components.file_browser.render_file_browser') as mock_render:
        mock_render.return_value = "data/test_file.csv"
        
        with patch.object(SessionStateManager, 'set_selected_file_path') as mock_set_path:
            with patch.object(SessionStateManager, 'set_file_mode') as mock_set_mode:
                # When: ファイルアップロードUIを表示
                result = show_file_upload_ui()
                
                # Then: ファイルが選択されたはず
                assert result is True
                mock_set_path.assert_called_with("data/test_file.csv")
                mock_set_mode.assert_called_with(True)
    
    # When: handle_file_uploaded()を明示的に呼び出し
    with patch.object(SessionStateManager, 'get_selected_file_path', return_value="data/test_file.csv"):
        with patch('streamlit.success') as mock_success:
            with patch('streamlit.subheader') as mock_subheader:
                with patch('src.presentation.file_utils.safe_preview_file') as mock_preview:
                    mock_preview.return_value = {
                        "success": True,
                        "dataframe": MagicMock(),
                        "warnings": [],
                        "info": []
                    }
                    
                    # 期待: handle_file_uploaded()でプレビューが表示される
                    handle_file_uploaded()
                    
                    # Assert: 成功メッセージとプレビューが表示される
                    mock_success.assert_called()
                    mock_subheader.assert_called_with("📊 ファイルプレビュー")


if __name__ == "__main__":
    test_file_preview_flow_integration()
    print("TDD Red Phase: テスト完了 - 問題を確認")