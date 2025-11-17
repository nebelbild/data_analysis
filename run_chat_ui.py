"""Streamlit Chat UI 起動スクリプト

このスクリプトは、Pythonパスを適切に設定してStreamlitアプリを起動します。
"""

import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Streamlitを起動
if __name__ == "__main__":
    import streamlit.web.cli as stcli
    
    chat_ui_path = project_root / "src" / "presentation" / "chat_ui.py"
    
    sys.argv = [
        "streamlit",
        "run",
        str(chat_ui_path),
        "--server.port=8501",
        "--server.address=localhost",
    ]
    
    sys.exit(stcli.main())
