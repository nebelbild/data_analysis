#!/usr/bin/env python3
"""
Jupyter Sandbox実機能テスト
"""

from src.infrastructure.di_container import DIContainer

def test_jupyter_sandbox():
    """Jupyter sandboxの基本動作テスト"""
    print("🧪 Jupyter Sandbox実機能テスト開始")
    
    try:
        # DIコンテナからsandboxを取得
        container = DIContainer()
        sandbox = container.get_sandbox_repository()
        
        # サンドボックス作成
        print("📝 サンドボックス作成中...")
        sandbox_id = sandbox.create()
        print(f"✅ 作成完了: {sandbox_id}")
        
        # 基本的なコード実行
        print("⚡ 基本コード実行テスト...")
        result = sandbox.execute_code('print("Hello World")')
        print(f"stdout: {result['stdout']}")
        print(f"stderr: {result['stderr']}")
        
        # 数値計算テスト
        print("🔢 数値計算テスト...")
        result = sandbox.execute_code('result = 2 + 3\nprint(f"2 + 3 = {result}")')
        print(f"stdout: {result['stdout']}")
        
        # グラフ生成テスト（修正版）
        print("📊 グラフ生成テスト...")
        graph_code = """
import matplotlib.pyplot as plt
import numpy as np
import base64
import io

# データ生成
x = np.linspace(0, 10, 100)
y = np.sin(x)

# グラフ作成
plt.figure(figsize=(8, 6))
plt.plot(x, y, label='sin(x)')
plt.title('Sin Wave')
plt.xlabel('X')
plt.ylabel('Y')
plt.legend()
plt.grid(True)

# PNG形式で保存
buffer = io.BytesIO()
plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
buffer.seek(0)
image_base64 = base64.b64encode(buffer.getvalue()).decode()
plt.close()  # メモリリークを防ぐ

# 結果を表示（長さのみ）
print(f"Generated PNG image: {len(image_base64)} characters")

# matplotlibで自動表示されるように
plt.figure(figsize=(6, 4))
plt.plot([1,2,3,4], [1,4,2,3])
plt.title('Test Plot')
plt.show()
"""
        result = sandbox.execute_code(graph_code)
        print(f"stdout: {result['stdout']}")
        print(f"グラフ結果数: {len(result['results'])}")
        
        for i, res in enumerate(result['results']):
            print(f"  結果{i+1}: {res['type']}")
            if res['type'] == 'png':
                print(f"    PNG画像サイズ: {len(res['content'])} bytes")
        
        # サンドボックス停止
        print("🛑 サンドボックス停止...")
        sandbox.kill()
        print("✅ テスト完了")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        raise

if __name__ == "__main__":
    test_jupyter_sandbox()