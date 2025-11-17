# DataAnalysisAgent

AIを活用したデータ分析自動化エージェント。クリーンアーキテクチャ設計により、高い保守性と拡張性を実現しています。

## 🚀 特徴

- **WebベースチャットUI**: Streamlitによる対話的な分析インターフェース
- **クリーンアーキテクチャ**: 依存性注入による疎結合設計
- **マルチフォーマット出力**: HTML/Markdown形式でのレポート生成
- **Jupyter Kernel統合**: IPythonカーネルによる高速なコード実行
- **Azure OpenAI対応**: Structured Outputsによる型安全なLLM連携
- **日本語完全対応**: matplotlib/seabornでの日本語フォント自動設定
- **モジュラー設計**: 独立したコンポーネントによる高い拡張性

## 📋 システム要件

- Python 3.12以上（Python 3.13対応）
- UV（パッケージマネージャー）
- Azure OpenAI API キー
- Windows標準日本語フォント（Yu Gothic, MS Gothic等）

## 🏗️ アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────────┐
│                    Presentation Layer                          │
│  ┌─────────────────┐                ┌─────────────────────────┐  │
│  │ State Machine   │                │   Workflow Facade      │  │
│  │   Framework     │ ◄──────────────┤   (Unified API)       │  │
│  └─────────────────┘                └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    Application Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Use Cases     │  │    Handlers     │  │   Renderers     │  │
│  │                 │  │                 │  │                 │  │
│  │ • GenerateCode  │  │ • PlanningHandler│ │ • HTMLRenderer  │  │
│  │ • ExecuteCode   │  │ • CodingHandler │  │ • MDRenderer    │  │
│  │ • GenerateReport│  │ • ExecutingHandler│ │                 │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      Domain Layer                              │
│  ┌─────────────────┐                ┌─────────────────────────┐  │
│  │    Entities     │                │    Repositories         │  │
│  │                 │                │    (Interfaces)         │  │
│  │ • DataThread    │                │ • LLMRepository         │  │
│  │ • Plan          │                │ • SandboxRepository     │  │
│  │ • Program       │                │                         │  │
│  │ • Review        │                │                         │  │
│  └─────────────────┘                └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  Repositories   │  │   DI Container  │  │   External      │  │
│  │ (Implementations)│  │                 │  │   Services      │  │
│  │ • OpenAILLM     │  │ • Service       │  │ • Azure OpenAI  │  │
│  │ • JupyterSandbox│  │   Registration  │  │ • IPython Kernel│  │
│  │                 │  │ • Lifecycle     │  │                 │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 ワークフロー

9段階の自動化データ分析ワークフロー：

```
Step 1: データフレーム読み込み
   ↓
Step 2: データフレーム分析（describe, info, sample）
   ↓
Step 3: 分析計画生成（LLMによる仮説分解）
   ↓
Step 4-7: 各タスク実行
   ├─→ コード生成（LLM）
   ├─→ コード実行（Jupyter Kernel）
   └─→ 結果保存（PNG画像）
   ↓
Step 8: 結果レビュー（LLMによる品質評価）
   ↓
Step 9: レポート生成（HTML/Markdown）
```

### 主要コンポーネント

#### 1. **LLMリポジトリ** (`OpenAILLMRepository`)
- Azure OpenAI Structured Outputsによる型安全なレスポンス
- Pydantic BaseModelとの自動連携
- オフラインフォールバックモード（ルールベース生成）

#### 2. **サンドボックスリポジトリ** (`JupyterSandboxRepository`)
- IPythonカーネルによる高速コード実行
- matplotlib日本語フォント自動設定
- エスケープシーケンス自動デコード（Azure OpenAI対応）
- リアルタイム実行結果取得

#### 3. **ユースケース層**
- `GenerateCodeUseCase`: Pythonコード生成
- `ExecuteCodeUseCase`: サンドボックスでの安全な実行
- `GeneratePlanUseCase`: 分析計画の立案
- `GenerateReportUseCase`: 最終レポート作成

## 🛠️ セットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/nebelbild/data_analysis.git
cd data_analysis
```

### 2. UVパッケージマネージャーのインストール

UVは高速なPythonパッケージマネージャーです。以下のいずれかの方法でインストールしてください。

#### Windows（PowerShell）

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### macOS/Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### pipを使用する場合

```bash
pip install uv
```

インストール後、以下のコマンドでバージョンを確認：

```bash
uv --version
```

### 3. Python環境のセットアップ

```bash
# UV を使用した依存関係のインストール
# .venv仮想環境が自動的に作成され、依存関係がインストールされます
uv sync

# 仮想環境をアクティブ化
source .venv/bin/activate  # Linux/Mac
# または
.venv\Scripts\activate     # Windows
```

**注意**: `uv sync`コマンドを実行すると、`.venv`ディレクトリが自動的に作成され、`pyproject.toml`と`uv.lock`に基づいて依存関係がインストールされます。手動で仮想環境を作成する必要はありません。

### 4. 環境変数の設定

`.env`ファイルを作成し、以下の環境変数を設定：

```env
# Azure OpenAI API設定
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
OPENAI_DEPLOYMENT_NAME=your-deployment-name
```

<details><summary>🔑 APIキーの取得方法</summary>

#### Azure OpenAI API キー
1. [Azure Portal](https://portal.azure.com/) にアクセス
2. Azure OpenAI Serviceリソースを作成
3. 「キーとエンドポイント」からAPI キーとエンドポイントを取得
4. `.env`ファイルに設定

</details>

## 🚀 使用方法

### チャットUIの起動（推奨）

#### 起動手順

```bash
# 1. プロジェクトルートに移動
cd C:\Users\you\work\00_proj\DataAnalysisAgent

# 2. 仮想環境を有効化
.venv\Scripts\activate  # Windows
# または
source .venv/bin/activate  # macOS/Linux

# 3. Streamlitを起動
streamlit run src/presentation/chat_ui.py
```

**または、起動スクリプトを使用**:

```bash
python run_chat_ui.py
```

ブラウザが自動的に開き、対話的なチャットインターフェースが表示されます。

**重要**: 必ずプロジェクトルート（`DataAnalysisAgent`ディレクトリ）から起動してください。

**主な機能**:
- ファイル選択（フォルダ選択/アップロード）
- データプレビュー
- 対話的な分析要求
- リアルタイム進捗表示
- グラフとレポートの表示
- ファイル履歴とブックマーク

詳細は [チャットUI使用ガイド](docs/user_guide/chat_ui_usage.md) を参照してください。

### コマンドラインでの実行

```bash
# サンプルワークフローの実行
python scripts/simple_workflow.py
```

実行すると以下が生成されます：
- `output/{session_id}/analysis_report.md`: マークダウン形式のレポート
- `output/{session_id}/report.html`: HTML形式のレポート
- `output/{session_id}/*.png`: 生成されたグラフ画像

### 出力例

```
output/20251108_223552/
├── analysis_report.md        # 詳細な分析レポート
├── report.html                # HTMLビューアー
├── style.css                  # HTMLスタイル
├── simple_workflow_0_1_0.png  # タスク1のグラフ
├── simple_workflow_1_1_0.png  # タスク2のグラフ
├── simple_workflow_2_1_0.png  # タスク3のグラフ
└── simple_workflow_3_1_0.png  # タスク4のグラフ
```

## 🔧 技術的な実装詳細

### Azure OpenAI Structured Outputs

Pydantic BaseModelを使用した型安全なレスポンス取得：

```python
from pydantic import BaseModel

class Program(BaseModel):
    achievement_condition: str
    execution_plan: str
    code: str

# Azure OpenAI APIから型安全にレスポンスを取得
response = client.beta.chat.completions.parse(
    model=deployment_name,
    messages=messages,
    response_format=Program
)
program: Program = response.choices[0].message.parsed
```

### 日本語フォント自動設定

Python 3.13対応の手動フォント設定（`japanize_matplotlib`非依存）：

```python
import matplotlib.font_manager as fm

# フォントキャッシュをリビルド
fm._rebuild()

# Windows標準フォントを自動検出
japanese_fonts = ['Yu Gothic', 'MS Gothic', 'Meiryo', 'BIZ UDGothic']
available_fonts = [f.name for f in fm.fontManager.ttflist]

for font_name in japanese_fonts:
    if font_name in available_fonts:
        matplotlib.rcParams['font.sans-serif'] = [font_name]
        plt.rcParams['axes.unicode_minus'] = False
        break
```

### エスケープシーケンス処理

Azure OpenAI Structured Outputsで返される`\\n`を実際の改行に変換：

```python
def execute_code(self, code: str, timeout: int = 1200) -> Dict[str, Any]:
    # \\n -> \n, \\t -> \t などの変換
    decoded_code = code.replace('\\n', '\n').replace('\\t', '\t')
    return self._execute_code_internal(decoded_code, timeout)
```

## 🧪 テスト実行

```bash
# 全テスト実行
python -m pytest tests/ -v

# カバレッジ付きテスト実行
python -m pytest tests/ --cov=src --cov-report=html

# 特定のテストのみ実行
python -m pytest tests/unit/ -v          # ユニットテストのみ
python -m pytest tests/integration/ -v   # 統合テストのみ
python -m pytest tests/e2e/ -v           # E2Eテストのみ
```

## 📦 依存関係

主要なライブラリ：

- `openai>=1.66.3`: Azure OpenAI API連携
- `pandas>=2.2.3`: データ処理
- `matplotlib>=3.7.0`: グラフ生成
- `seaborn>=0.12.0`: 統計グラフ
- `scipy>=1.11.0`: 科学計算（統計分析）
- `ipython>=8.0.0`: カーネル管理
- `jupyter-client>=8.0.0`: Jupyterプロトコル
- `pydantic>=2.10.6`: データバリデーション
- `jinja2>=3.1.6`: テンプレートエンジン
- `python-dotenv>=1.0.1`: 環境変数管理

開発用ライブラリ：

- `pytest>=8.3.4`: テストフレームワーク
- `ruff>=0.7.2`: リンター/フォーマッター
- `mypy>=1.13.0`: 型チェッカー

## 🐛 トラブルシューティング

### Streamlit起動時のエラー

#### ModuleNotFoundError: No module named 'src'

**問題**: Streamlit起動時に`ModuleNotFoundError: No module named 'src'`エラー  
**原因**: Pythonが`src`モジュールを見つけられない（カレントディレクトリの問題）  
**解決策**:

```bash
# 1. プロジェクトルートに移動
cd C:\Users\you\work\00_proj\DataAnalysisAgent

# 2. 正しいディレクトリから起動
streamlit run src/presentation/chat_ui.py

# または起動スクリプトを使用
python run_chat_ui.py
```

#### ポートが既に使用されている

**問題**: `Address already in use`エラー  
**解決策**: 別のポートで起動

```bash
streamlit run src/presentation/chat_ui.py --server.port=8502
```

### Python 3.13環境での問題

**問題**: `japanize_matplotlib`がインストールできない  
**原因**: Python 3.13で`distutils`が削除された  
**解決策**: 自動的に手動フォント設定を使用（本プロジェクトで実装済み）

### 日本語フォントが表示されない

**問題**: グラフの日本語が文字化け（豆腐文字）  
**原因**: 日本語フォントが検出されていない  
**解決策**: 
1. Windows標準フォント（Yu Gothic, MS Gothic等）がインストールされているか確認
2. `fm._rebuild()`でフォントキャッシュをリビルド（実装済み）

### LLMが生成したコードでSyntaxError

**問題**: `SyntaxError: unexpected character after line continuation character`  
**原因**: Azure OpenAI Structured Outputsが`\\n`をエスケープシーケンスとして返す  
**解決策**: 自動的にデコード処理を実行（`jupyter_sandbox_repository.py`で実装済み）

### scipyがインストールされていない

**問題**: `ModuleNotFoundError: No module named 'scipy'`  
**原因**: LLMが統計分析（ANOVA等）を使用したコードを生成  
**解決策**: 
```bash
uv sync  # 依存関係を再インストール
```

## 🤝 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずissueを開いて変更内容を議論してください。

## 📚 参考資料

- [Azure OpenAI Service](https://azure.microsoft.com/ja-jp/products/ai-services/openai-service)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Jupyter Client Documentation](https://jupyter-client.readthedocs.io/)
- [matplotlib Documentation](https://matplotlib.org/)
- [seaborn Documentation](https://seaborn.pydata.org/)
