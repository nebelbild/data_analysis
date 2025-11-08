"""
TDD Green Phase: GenerateCodeUseCase 実装

設計関心事:
- 単一責任の原則: コード生成のみを責務とする
- 依存性逆転の原則: LLMRepositoryインターフェースに依存
- テスト容易性: 外部依存を注入で受け取る
- 関心の分離: ビジネスロジックと外部サービスを分離
- 複雑なビジネスルール: 前回スレッド情報に基づく自己修正機能
"""

from typing import Dict, List

from src.domain.entities import DataThread, Program
from src.domain.repositories.llm_repository import LLMRepository
from src.llms.load_template import load_template


class GenerateCodeUseCase:
    """
    コード生成ユースケース
    
    データ情報とユーザー要求を基に、実行可能なPythonコードを生成する。
    前回実行結果がある場合は、自己修正機能により改善されたコードを生成。
    
    設計原則:
    - 単一責任: コード生成のビジネスロジックのみ
    - 依存性逆転: 具象LLM実装ではなくインターフェースに依存
    - テスト容易性: モック可能なリポジトリ注入
    - 複雑な条件分岐: 前回スレッド情報による文脈構築
    """

    def __init__(self, llm_repository: LLMRepository) -> None:
        """
        依存性注入によるLLMRepositoryの設定
        
        Args:
            llm_repository: LLM操作を抽象化したリポジトリ
        """
        self._llm_repository = llm_repository

    def execute(
        self,
        data_info: str,
        user_request: str,
        remote_save_dir: str = "outputs/process_id/id",
        previous_thread: DataThread | None = None,
        model: str = "gpt-4o-mini-2024-07-18",
        template_file: str = "src/prompts/generate_code.jinja",
    ) -> Program:
        """
        コード生成を実行
        
        Args:
            data_info: データの説明（CSV構造など）
            user_request: ユーザーのコード生成要求
            remote_save_dir: リモート保存ディレクトリ
            previous_thread: 前回の実行スレッド情報（自己修正用）
            model: 使用するLLMモデル名
            template_file: プロンプトテンプレートのパス
            
        Returns:
            Program: 生成されたプログラム（コード、実行計画、達成条件）
            
        Raises:
            Exception: LLM呼び出しが失敗した場合
            
        ビジネスルール:
        - 前回スレッドがある場合は、コード、出力、エラー、観測結果を文脈に含める
        - 自己修正機能: 前回の失敗を踏まえた改善コードを生成
        - テンプレートベース: Jinjaテンプレートによるプロンプト生成
        """
        # 1. 基本メッセージの構築
        messages = self._build_base_messages(data_info, user_request, remote_save_dir, template_file)

        # 2. 前回スレッド情報の文脈追加（自己修正機能）
        if previous_thread:
            messages = self._add_previous_thread_context(messages, previous_thread)

        # 3. LLMを通じたコード生成
        response = self._llm_repository.generate(
            messages=messages,
            model=model,
            response_format=Program,
        )

        # 4. LLMResponseからProgramエンティティを抽出
        if hasattr(response, 'content') and isinstance(response.content, Program):
            return response.content
        else:
            # フォールバック: responseがProgramの場合はそのまま返す
            return response if isinstance(response, Program) else response

    def _build_base_messages(
        self, data_info: str, user_request: str, remote_save_dir: str, template_file: str
    ) -> List[Dict[str, str]]:
        """
        基本メッセージを構築
        
        Args:
            data_info: データ情報
            user_request: ユーザー要求
            remote_save_dir: 保存ディレクトリ
            template_file: テンプレートファイルパス
            
        Returns:
            List[Dict[str, str]]: 基本メッセージリスト
            
        命名根拠:
        - _build_base_messages: 基本メッセージ構築の意図が明確
        - プライベートメソッド: 外部から呼び出し不要
        """
        # テンプレート読み込み（既存実装を踏襲）
        template = load_template(template_file)
        system_message = template.render(
            data_info=data_info,
            remote_save_dir=remote_save_dir,
        )

        # 基本メッセージ構築（OpenAI Chat API形式）
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"タスク要求: {user_request}"},
        ]

    def _add_previous_thread_context(
        self, messages: List[Dict[str, str]], previous_thread: DataThread
    ) -> List[Dict[str, str]]:
        """
        前回スレッド情報を文脈に追加（自己修正機能）
        
        Args:
            messages: 基本メッセージリスト
            previous_thread: 前回実行スレッド情報
            
        Returns:
            List[Dict[str, str]]: 文脈追加後のメッセージリスト
            
        ビジネスルール:
        1. 前回のコードをassistantメッセージとして追加
        2. stdout/stderrがあればsystemメッセージとして追加
        3. 観測結果があればuserメッセージとして改善要求を追加
        
        命名根拠:
        - _add_previous_thread_context: 文脈追加の意図が明確
        - previous_thread: 前回実行情報を表現
        """
        # 前回のコードを会話履歴に追加
        if previous_thread.code:
            messages.append({"role": "assistant", "content": previous_thread.code})

        # 前回の実行結果（stdout/stderr）を追加
        if previous_thread.stdout and previous_thread.stderr:
            messages.extend([
                {"role": "system", "content": f"stdout: {previous_thread.stdout}"},
                {"role": "system", "content": f"stderr: {previous_thread.stderr}"},
            ])

        # 前回の観測結果を改善要求として追加
        if previous_thread.observation:
            messages.append({
                "role": "user",
                "content": f"以下を参考にして、ユーザー要求を満たすコードを再生成してください: {previous_thread.observation}",
            })

        return messages