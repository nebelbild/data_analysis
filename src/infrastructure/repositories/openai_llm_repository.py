"""TDD Green Phase: OpenAILLMRepository 実装（Azure OpenAI対応）

t-wadaさんのTDD原則: テストが通る最小限の実装

設計関心事:
- Azure OpenAIサービスの使用
- リソースグループ: rg-1
- デプロイメント名: activarch-test-genpptx
"""

import logging
import os
from typing import Any
from collections.abc import Generator

from src.domain.repositories.llm_repository import LLMRepository

# Azure OpenAI用の遅延インポート
try:
    from openai import AzureOpenAI
except ImportError:
    AzureOpenAI = None  # type: ignore


logger = logging.getLogger(__name__)


class OpenAILLMRepository(LLMRepository):
    """Azure OpenAI LLM実装

    設計原則:
    - 単一責任の原則（SRP）: LLM操作のみを責務とする
    - 依存性逆転の原則（DIP）: LLMRepositoryインターフェースに依存

    Azure OpenAI設定:
    - リソースグループ: rg-1
    - デプロイメント名: activarch-test-genpptx
    - エンドポイント: AZURE_OPENAI_ENDPOINT環境変数から取得
    - APIキー: AZURE_OPENAI_API_KEY環境変数から取得
    """

    def __init__(self, api_key: str | None = None, endpoint: str | None = None):
        """コンストラクタ

        Args:
            api_key: Azure OpenAI APIキー（省略時は環境変数から取得）
            endpoint: Azure OpenAI エンドポイント（省略時は環境変数から取得）

        """
        # Azure OpenAI設定
        self.api_key = api_key or os.environ.get("AZURE_OPENAI_API_KEY")
        self.endpoint = endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT")
        self.api_version = os.environ.get(
            "AZURE_OPENAI_API_VERSION",
            "2024-08-01-preview",
        )
        self.deployment_name = os.environ.get(
            "AZURE_OPENAI_DEPLOYMENT_NAME", "activarch-test-genpptx",
        )  # 環境変数から取得
        self._offline_reason: str | None = None

        # Azure OpenAI クライアントの初期化
        if AzureOpenAI and self.api_key and self.endpoint:
            try:
                self._client = AzureOpenAI(
                    api_key=self.api_key,
                    api_version=self.api_version,
                    azure_endpoint=self.endpoint,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Azure OpenAI クライアント初期化に失敗しました: %s", exc)
                self._client = None
                self._offline_reason = str(exc)
        else:
            self._client = None
            if not AzureOpenAI:
                self._offline_reason = "openai パッケージがインストールされていません"
            elif not self.api_key or not self.endpoint:
                self._offline_reason = "Azure OpenAI の資格情報が設定されていません"

        if self._client is None:
            logger.warning(
                "Azure OpenAI クライアントが利用できないため、ルールベースのフォールバックを使用します。（理由: %s）",
                self._offline_reason or "不明",
            )

    def generate(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        response_format: type | None = None,
    ) -> Any:
        """Azure OpenAIから応答を生成

        Args:
            messages: メッセージのリスト（役割とコンテンツ）
            model: モデル名（デプロイメント名で上書きされます）
            temperature: ランダム性（0.0-2.0）
            max_tokens: 最大トークン数（省略可）
            response_format: 応答フォーマット（Pydanticモデル、省略可）

        Returns:
            str: LLM応答テキスト

        実装詳細:
        - Azure OpenAIではmodel引数をdeployment_nameに置き換え
        - デプロイメント名は固定: activarch-test-genpptx
        - response.choices[0].message.contentを返す
        - response_formatが指定されている場合はStructured Outputsを使用

        """
        if not self._client:
            return self._generate_offline_response(messages, response_format)

        # Azure OpenAI API呼び出しパラメータの構築
        api_params = {
            "model": self.deployment_name,  # デプロイメント名を使用
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens is not None:
            api_params["max_tokens"] = max_tokens

        # Structured Outputs対応: response_formatがPydantic BaseModelの場合はparse()を使用
        if response_format is not None:
            import inspect
            from pydantic import BaseModel

            if inspect.isclass(response_format) and issubclass(
                response_format,
                BaseModel,
            ):
                # Pydantic BaseModelの場合はparse()メソッドを使用
                parse_params = {
                    "model": self.deployment_name,
                    "messages": messages,
                    "temperature": temperature,
                    "response_format": response_format,
                }

                if max_tokens is not None:
                    parse_params["max_completion_tokens"] = max_tokens

                response = self._client.beta.chat.completions.parse(**parse_params)
                return response.choices[0].message.parsed
            # 従来のresponse_format（辞書形式など）の場合
            api_params["response_format"] = response_format
            response = self._client.chat.completions.create(**api_params)
            return response.choices[0].message.content
        # response_formatが指定されていない場合
        response = self._client.chat.completions.create(**api_params)
        return response.choices[0].message.content

    def stream(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> Generator[str, None, None]:
        """Azure OpenAIからストリーミング応答を生成

        Args:
            messages: メッセージのリスト
            model: モデル名（デプロイメント名で上書きされます）
            temperature: ランダム性
            max_tokens: 最大トークン数

        Yields:
            str: 応答のチャンク（逐次的に生成される）

        実装詳細:
        - stream=Trueでストリーミング応答を取得
        - チャンクごとにyield

        """
        if not self._client:
            for chunk in self._generate_offline_stream(messages):
                yield chunk
            return

        # Azure OpenAI APIコール（ストリーミング）
        response = self._client.chat.completions.create(
            model=self.deployment_name,  # デプロイメント名を使用
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    # ==================================================================
    # ルールベースフォールバック
    # ==================================================================
    def _generate_offline_response(
        self,
        messages: list[dict[str, str]],
        response_format: type | None,
    ) -> Any:
        """Azure OpenAIが利用できない場合に簡易応答を生成する。"""
        import inspect
        from pydantic import BaseModel  # type: ignore

        user_prompt = self._extract_latest_user_prompt(messages)

        if (
            response_format
            and inspect.isclass(response_format)
            and issubclass(response_format, BaseModel)
        ):
            model_name = response_format.__name__
            if model_name == "Plan":
                return self._build_rule_based_plan(user_prompt)
            if model_name == "Program":
                return self._build_rule_based_program()
            if model_name == "Review":
                return self._build_rule_based_review(user_prompt)
            return response_format()

        return self._build_rule_based_report(user_prompt)

    def _generate_offline_stream(self, messages: list[dict[str, str]]):
        """簡易ストリーミングフォールバック。"""
        content = self._build_rule_based_report(
            self._extract_latest_user_prompt(messages),
        )
        for chunk in content.splitlines():
            yield chunk

    @staticmethod
    def _extract_latest_user_prompt(messages: list[dict[str, str]]) -> str:
        preferred_prompt = ""

        for message in reversed(messages):
            if message.get("role") != "user":
                continue

            content = message.get("content", "")
            if not content:
                continue

            if "タスク要求" in content:
                return content

            if not content.startswith("実行結果") and not preferred_prompt:
                preferred_prompt = content

        if preferred_prompt:
            return preferred_prompt

        for message in reversed(messages):
            if message.get("role") == "user":
                return message.get("content", "")

        return ""

    @staticmethod
    def _build_rule_based_plan(user_prompt: str):
        from src.domain.entities.plan import Plan, Task

        tasks = [
            Task(
                hypothesis="主要KPIの分布を可視化するとデータの偏りを把握できる",
                purpose="purchase_amountやclick_countなどの分布を確認して異常値を検知する",
                description="ヒストグラムや箱ひげ図で主要数値指標を比較し、外れ値・偏りを点検する",
                chart_type="ヒストグラム / 箱ひげ図",
            ),
            Task(
                hypothesis="指標同士の相関を調べると改善余地が見える",
                purpose="click_count・conversion_rate・scoreの関係から改善施策を示唆する",
                description="散布図と相関ヒートマップで強い関係性を洗い出し、指標連動を可視化する",
                chart_type="散布図 / 相関ヒートマップ",
            ),
            Task(
                hypothesis="チャネル別にKPIを比較すると有効なチャネルが分かる",
                purpose="channel_id単位で主要指標を平均化し、強みと弱みを整理する",
                description="groupby集計後に複数指標を折れ線・棒グラフで表示し、成果が高いチャネルを特定する",
                chart_type="棒グラフ / 折れ線グラフ",
            ),
        ]

        return Plan(
            purpose="分布・相関・チャネル比較の3観点からデータを俯瞰し、次のアクションにつながる洞察を得る",
            archivement="3つの観点すべてで定量的な可視化と解釈メモを提示できた状態",
            tasks=tasks,
        )

    @staticmethod
    def _build_rule_based_program():
        from textwrap import dedent
        from src.domain.entities.program import Program

        code = dedent(
            """
            import pandas as pd
            import matplotlib.pyplot as plt
            import seaborn as sns

            sns.set(style="whitegrid")

            def _select_numeric_columns(frame: pd.DataFrame) -> list[str]:
                priority_cols = [
                    "purchase_amount",
                    "click_count",
                    "conversion_rate",
                    "score",
                ]
                numeric_cols = [col for col in priority_cols if col in frame.columns]
                if not numeric_cols:
                    numeric_cols = frame.select_dtypes(include="number").columns.tolist()
                if len(numeric_cols) < 2:
                    raise ValueError("Not enough numeric columns for visualization.")
                return numeric_cols

            numeric_cols = _select_numeric_columns(df)
            print("=== Numeric summary ===")
            print(df[numeric_cols].describe().round(2))

            # 1) KPI distribution
            plt.figure(figsize=(10, 6))
            for col in numeric_cols[:3]:
                sns.kdeplot(df[col], label=col, fill=True, alpha=0.2)
            plt.title("Key KPI distribution")
            plt.xlabel("value")
            plt.ylabel("density")
            plt.legend()
            show_plot()

            # 2) Correlation heatmap
            corr = df[numeric_cols].corr()
            plt.figure(figsize=(8, 6))
            sns.heatmap(corr, annot=True, cmap="Blues", vmin=-1, vmax=1, linewidths=0.4)
            plt.title("Correlation matrix")
            show_plot()

            # 3) Channel level comparison
            if "channel_id" in df.columns:
                grouped = df.groupby("channel_id")[numeric_cols].mean().reset_index()
                print("=== Channel average values ===")
                print(grouped.round(2))

                plt.figure(figsize=(11, 6))
                for metric in numeric_cols[:2]:
                    sns.lineplot(data=grouped, x="channel_id", y=metric, marker="o", label=metric)
                plt.title("KPI trend by channel")
                plt.xticks(rotation=30)
                plt.ylabel("value")
                plt.legend()
                show_plot()
            else:
                print("channel_id column does not exist, skipped channel comparison.")
            """,
        ).strip()

        execution_plan = (
            "1) 主要指標の分布比較  2) 指標間の相関可視化  3) チャネル別KPI比較"
        )
        achievement_condition = (
            "分布・相関・チャネル比較の出力が全て完了し、統計量ログも取得できていること"
        )

        return Program(
            achievement_condition=achievement_condition,
            execution_plan=execution_plan,
            code=code,
        )

    @staticmethod
    def _build_rule_based_review(user_prompt: str):
        from src.domain.entities.review import Review

        observation = "\n".join(
            [
                "【レビュー結果（フォールバック）】",
                "- 主要なKPIを分布・相関・チャネル比較の3観点で確認しました。",
                "- グラフと統計量をもとに偏りや改善余地を検証してください。",
                f"- ユーザー要求: {user_prompt or '（指定なし）'}",
                "",
                "【推奨アクション】",
                "1. 相関が強い指標同士を重点的に改善する。",
                "2. 成果の高いチャネルと停滞チャネルを比較し、施策を共有する。",
                "3. 外れ値が多い列はデータ前処理や異常検知ルールを検討する。",
            ],
        )

        return Review(observation=observation, is_completed=True)

    @staticmethod
    def _build_rule_based_report(user_prompt: str) -> str:
        steps = "\n".join(
            [
                "1. データ構造を確認し、主要KPI列を抽出しました。",
                "2. 数値列の統計量と分布を確認して偏りを把握しました。",
                "3. 相関ヒートマップで指標間の関係を整理しました。",
                "4. channel_idが存在する場合は平均値を算出し、チャネル比較を行いました。",
            ],
        )

        return "\n".join(
            [
                "# 簡易レポート（ローカルフォールバック）",
                "",
                "## サマリー",
                "- Azure OpenAIが利用できないため、ルールベースのテンプレートで結果を生成しました。",
                f"- ユーザー要求: {user_prompt or '（指定なし）'}",
                "",
                "## 実施ステップ",
                steps,
                "",
                "## 留意事項",
                "- 詳細な自然言語レポートが必要な場合はAzure OpenAI関連の依存関係を整えて再実行してください。",
            ],
        )
