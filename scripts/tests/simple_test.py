#!/usr/bin/env python3
"""シンプルなJupyter Sandbox基本テスト
"""

from src.infrastructure.di_container import DIContainer

def simple_test():
    """最小限のテスト"""
    print("🔹 シンプルテスト開始")

    container = DIContainer()
    sandbox = container.get_sandbox_repository()

    # 作成
    sandbox_id = sandbox.create()
    print(f"作成: {sandbox_id}")

    # 1つずつテスト
    print("テスト1: 基本出力")
    result1 = sandbox.execute_code('print("Test 1 OK")')
    print(f"出力: '{result1['stdout'].strip()}'")

    print("テスト2: 計算")
    result2 = sandbox.execute_code('x = 5 + 3\nprint(f"5 + 3 = {x}")')
    print(f"出力: '{result2['stdout'].strip()}'")

    print("テスト3: matplotlib基本")
    result3 = sandbox.execute_code("""
import matplotlib.pyplot as plt
print("matplotlib imported successfully")
""")
    print(f"出力: '{result3['stdout'].strip()}'")

    # 停止
    sandbox.kill()
    print("🔹 テスト完了")

if __name__ == "__main__":
    simple_test()
