# 改善案12項目 実装進捗メモ

作成日: 2026-03-06 03:30
ブランチ: feat/improvement-12items

## Phase 1: 低リスク・即効性（プロンプト/設定変更中心）
- [x] Item 12: 温度設定の段階的チューニング
  - SCAMPER:1.3, SixHats:1.4, Reverse:1.6, Mandalart:1.2, Shiritori:1.5, CoreIdea:1.3
- [x] Item 1: Google検索エージェントのオプション化
  - `--search-engine ddg|google` 引数追加、DDGスタンドアロンモード追加
- [x] Item 6: ImagePromptAgent情報量バランス精密化
  - テキスト優先順位ルール追加、ワンシーン描写義務化
- [x] Item 7: ゲーム画面モックアップ指示
  - GAMEPLAY_MOCKUPレイアウト追加、HUD要素指示追加

## Phase 2: スキーマ進化（models.py + エージェントプロンプト）
- [x] Item 9: ゲームサイクルの構造的深化
  - GameCycleにtrigger/escalation追加、循環構造図プロンプト追加、Markdown/PPTX更新
- [x] Item 11: ResearchAgentへの不満点調査追加
  - ResearchOutputにpain_points追加、DDGプロンプト更新、ブレストエージェントに参照指示追加
- [x] Item 10: BrainstormMerge品質フィルタリング強化
  - FilteredIdeaスキーマ追加、除外基準3つ追加、最低15個維持制御
- [x] Item 2: マンダラート2段階展開化
  - MandalartStage1Agent + MandalartStage2Agent + MandalartPipeline(SequentialAgent)
  - MandalartOutputスキーマ追加

## Phase 3: インフラ（ツール/パイプライン強化）
- [x] Item 5: 画像生成リトライ機構
  - 指数バックオフ(1s→2s→4s)、安全フィルタ検出+プロンプト緩和、リトライログ
- [x] Item 3: トークン数・コストstats出力
  - イベントからusage_metadata収集、stats.json保存、コンソールサマリー表示
- [x] Item 4: JSON検証ミドルウェア
  - _VALIDATION_MAPでstate_key→Pydanticモデルマッピング、model_validate()実行、warningログ

## Phase 4: 新エージェント
- [x] Item 8: CritiqueAgent + リファインループ
  - 4軸スコア(concept_mechanic_alignment, game_cycle_concreteness, catchcopy_originality, usp_differentiation)
  - critique_threshold(6.0)未満でExpansionAgent再実行、最大3回
  - パイプライン分割: メイン(1-11) → Critique → ImagePrompt

## 変更ファイル一覧

### 変更
- `src/game_pitch_agent/agents/brainstorm.py` - 温度個別化、マンダラート2段階化、品質フィルタリング、pain_points参照
- `src/game_pitch_agent/agents/core_idea.py` - 温度1.3に変更
- `src/game_pitch_agent/agents/research.py` - DDGスタンドアロン、pain_points追加
- `src/game_pitch_agent/agents/image_prompt.py` - モックアップレイアウト、テキスト優先度、ビジュアル義務
- `src/game_pitch_agent/agents/expansion.py` - ゲームサイクル循環構造、リファインモード
- `src/game_pitch_agent/agents/__init__.py` - critique_agentエクスポート追加
- `src/game_pitch_agent/schemas/models.py` - GameCycle拡張、pain_points、FilteredIdea、MandalartOutput、CritiqueFeedback/CritiqueOutput
- `src/game_pitch_agent/pipeline.py` - パイプライン分割、CritiqueAgent+リファインループ、JSON検証、トークン統計、search_engine
- `src/game_pitch_agent/main.py` - --search-engine引数、stats表示/保存、ゲームサイクル新フィールド表示
- `src/game_pitch_agent/config.py` - critique_threshold、critique_max_reruns追加
- `src/game_pitch_agent/tools/image_gen.py` - リトライ機構、安全フィルタ緩和
- `src/game_pitch_agent/tools/pptx_render.py` - ゲームサイクル新フィールド表示
- `config.yaml` - critique設定追加

### 新規
- `src/game_pitch_agent/agents/critique.py` - CritiqueAgent

### ドキュメント更新
- `Docs/agent_architecture.md` - 全変更反映
- `README.md` - CLIオプション・更新履歴追記
