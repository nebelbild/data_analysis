#!/usr/bin/env python3
"""
グラフ生成専用テスト
"""

from src.infrastructure.di_container import DIContainer

def graph_test():
    """グラフ生成のテスト"""
    print("📊 グラフ生成専用テスト開始")
    
    container = DIContainer()
    sandbox = container.get_sandbox_repository()
    
    # 作成
    sandbox_id = sandbox.create()
    print(f"作成: {sandbox_id}")
    
    # グラフ生成テスト
    print("テスト: plt.show()でのPNG出力")
    graph_code = '''
import matplotlib.pyplot as plt
import numpy as np

# データ生成
x = np.linspace(0, 2*np.pi, 100)
y = np.sin(x)

# グラフ作成
plt.figure(figsize=(8, 6))
plt.plot(x, y, 'b-', linewidth=2, label='sin(x)')
plt.title('Sine Wave')
plt.xlabel('X')
plt.ylabel('Y')
plt.legend()
plt.grid(True)

print("グラフを作成しました")
plt.show()  # これでPNG出力されるはず
'''
    
    result = sandbox.execute_code(graph_code)
    print(f"stdout: '{result['stdout'].strip()}'")
    print(f"stderr: '{result['stderr'].strip()}'")
    print(f"結果数: {len(result['results'])}")
    
    for i, res in enumerate(result['results']):
        print(f"  結果{i+1}: {res['type']}")
        if res['type'] == 'png':
            print(f"    PNG画像サイズ: {len(res['content'])} bytes")
        else:
            print(f"    内容: {res['content'][:100]}...")
    
    # 停止
    sandbox.kill()
    print("📊 グラフテスト完了")

if __name__ == "__main__":
    graph_test()