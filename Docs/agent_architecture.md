# ゲーム企画書エージェント システムアーキテクチャ

## 1. システム概要

ゲーム企画書自動生成AIエージェントシステム。任意のトピックを入力すると、13ステップのLLMエージェントパイプラインが順番に処理を行い、ゲーム企画書（ペラ1形式）と企画書画像を自動生成する。

| 項目 | 内容 |
|------|------|
| フレームワーク | Google ADK（Agent Development Kit） |
| エージェント構成 | メインパイプライン（SequentialAgent、11ステップ）+ CritiqueAgent（リファインループ）+ ImagePromptAgent（個別実行）+ PitchEvaluatorAgent（事後評価）+ OverviewEvaluatorAgent（俯瞰評価）。計15ステップ |
| 状態管理 | `InMemorySessionService`（Session State） |
| 実行方式 | `Runner.run_async()` による非同期実行 |
| 入力 | トピック文字列（例: "忍者 × タイムトラベル"） |
| 出力 | 企画書JSON・Markdown・PNG画像（企画書数ぶん）・stats.json・evaluation.json・overview_evaluation.json |

---

## 2. アーキテクチャ全体図

### 2.1 エージェントフロー

```
[ユーザー入力: topic]
        │
        ▼
┌───────────────────────────────────────────────────────┐
│              GamePitchPipeline                         │
│            (SequentialAgent) ステップ1〜11              │
│                                                       │
│  ①GoogleResearchAgent     →  google_research_output   │
│  (optional: --search-engine google 時のみ実行)         │
│         ↓                                             │
│  ②DuckDuckGoResearchAgent →  research_output          │
│  (default: --search-engine ddg でスタンドアロン実行)    │
│         ↓                                             │
│  ┌─────────────────────────────────────────────┐      │
│  │       BrainstormPipeline                    │      │
│  │      (SequentialAgent)                      │      │
│  │                                             │      │
│  │  ③ScamperAgent    → scamper_output          │      │
│  │         ↓                                   │      │
│  │  ④SixHatsAgent    → sixhats_output          │      │
│  │         ↓                                   │      │
│  │  ⑤ReverseAgent    → reverse_output          │      │
│  │         ↓                                   │      │
│  │  ⑥MandalartPipeline (2段階)                  │      │
│  │    ├─ MandalartStage1Agent                  │      │
│  │    │    → mandalart_stage1_output           │      │
│  │    └─ MandalartStage2Agent                  │      │
│  │         → mandalart_output                  │      │
│  │         ↓                                   │      │
│  │  ⑦ShiritoriAgent  → shiritori_output        │      │
│  │         ↓                                   │      │
│  │  ⑧BrainstormMergeAgent → brainstorm_output  │      │
│  └─────────────────────────────────────────────┘      │
│         ↓                                             │
│  ⑨CoreIdeaAgent          →  core_ideas_output        │
│         ↓                                             │
│  ⑩EvaluationAgent        →  evaluation_output        │
│         ↓                                             │
│  ⑪ExpansionAgent         →  expanded_ideas_output    │
└───────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────┐
│  ⑫CritiqueAgent          →  critique_output          │
│  (リファインループ: avg_score < threshold なら         │
│   ExpansionAgent を再実行、最大 critique_max_reruns 回)│
│  ※ critique_feedback を Session State に注入          │
└───────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────┐
│  ⑬ImagePromptAgent       →  image_prompts_output     │
└───────────────────────────────────────────────────────┘
        │
        ▼
[main.py] generate_pitch_image() × N
        │
        ▼
[出力ディレクトリ]
  pitch_1/pitch.json, pitch.md, pitch_image.png
  pitch_2/...
  pitch_N/...
  stats.json
        │
        ▼ (オプション: evaluate コマンド or --evaluate フラグ)
┌───────────────────────────────────────────────────────┐
│  ⑭PitchEvaluatorPipeline (SequentialAgent)            │
│  (各 pitch.json に対して個別実行)                      │
│                                                       │
│  A: InnovationEvalAgent    → eval_innovation_output   │
│         ↓                                             │
│  B: CoherenceEvalAgent     → eval_coherence_output    │
│         ↓                                             │
│  C: PlayabilityEvalAgent   → eval_playability_output  │
│         ↓                                             │
│  D: PresentationEvalAgent  → eval_presentation_output │
│         ↓                                             │
│  M: EvalMergeAgent         → pitch_evaluation_output  │
│                                                       │
│  → pitch_N/evaluation.json として保存                  │
└───────────────────────────────────────────────────────┘
        │
        ▼ (2件以上のpitch時 / --no-overview でスキップ)
┌───────────────────────────────────────────────────────┐
│  ⑮OverviewEvaluatorAgent (LlmAgent)                  │
│  (全pitchを俯瞰して比較評価)                           │
│                                                       │
│  Python側: axis_averages（16軸平均値を算出）            │
│  LLM側:   diversity_scores（7カテゴリの多様性）         │
│           pitch_rankings（推薦順位）                    │
│           summary（俯瞰コメント）                       │
│                                                       │
│  → overview_evaluation.json として保存                 │
└───────────────────────────────────────────────────────┘
```

### 2.2 Session State を介したデータ受け渡し

```
Session State（InMemorySessionService）

  初期値:
  ┌────────────────────────────────────────┐
  │ topic          = "ユーザー入力"         │
  │ num_pitches    = 3                     │
  │ min_ideas_count = 15 (3×5)            │
  └────────────────────────────────────────┘
          ↓ 各エージェントが読み書き
  最終値:
  ┌────────────────────────────────────────┐
  │ topic                  (初期値)        │
  │ num_pitches            (初期値)        │
  │ min_ideas_count        (初期値)        │
  │ google_research_output (Agent①出力)   │
  │ research_output        (Agent②出力)   │
  │ scamper_output         (Agent③出力)   │
  │ sixhats_output         (Agent④出力)   │
  │ reverse_output         (Agent⑤出力)   │
  │ mandalart_stage1_output(Agent⑥前半出力)│
  │ mandalart_output       (Agent⑥後半出力)│
  │ shiritori_output       (Agent⑦出力)   │
  │ brainstorm_output      (Agent⑧出力)   │
  │ core_ideas_output      (Agent⑨出力)   │
  │ evaluation_output      (Agent⑩出力)   │
  │ expanded_ideas_output  (Agent⑪出力)   │
  │ critique_output        (Agent⑫出力)   │
  │ critique_feedback      (リファインループ中に注入) │
  │ image_prompts_output   (Agent⑬出力)   │
  └────────────────────────────────────────┘
```

---

## 3. エージェント詳細

### Agent ① GoogleResearchAgent（オプション）

| 項目 | 内容 |
|------|------|
| ファイルパス | `src/game_pitch_agent/agents/research.py` |
| クラス | `LlmAgent` |
| 役割 | Google検索でトピックに関するゲーム市場情報を収集する |
| 使用ツール | `google_search`（ADK組み込み） |
| 入力キー | `topic` |
| 出力キー | `google_research_output` |
| 実行条件 | `--search-engine google` 指定時のみ実行（デフォルトではスキップ） |

**検索エンジン選択:**
- `--search-engine ddg`（デフォルト）: GoogleResearchAgent をスキップし、DDGエージェントがスタンドアロンで実行
- `--search-engine google`: GoogleResearchAgent → DDGエージェントの両方を実行

**プロンプトの核心部分:**
- 4つの観点で2〜3回のGoogle検索を実行（既存ゲーム、市場トレンド、ユニークアイデアのヒント、関連カルチャー）
- 結果をJSON形式のみで出力（コードブロック・説明文なし）

**出力スキーマ（ResearchOutput）:**
```json
{
  "original_topic": "string",
  "research_items": [
    {
      "topic": "string",
      "summary": "string",
      "key_insights": ["string"],
      "source_hints": ["string"]
    }
  ],
  "market_context": "string",
  "related_games": ["string"],
  "pain_points": ["string"]
}
```

---

### Agent ② DuckDuckGoResearchAgent

| 項目 | 内容 |
|------|------|
| ファイルパス | `src/game_pitch_agent/agents/research.py` |
| クラス | `LlmAgent` |
| 役割 | DuckDuckGo検索でリサーチ結果を出力する（Google併用時は補完、スタンドアロン時は単独で網羅的に調査） |
| 使用ツール | `duckduckgo_search`（カスタムツール） |
| 入力キー | `topic`, `google_research_output`（存在する場合のみ） |
| 出力キー | `research_output` |

**動作モード:**
- **スタンドアロンモード**（`--search-engine ddg`、デフォルト）: 3〜4回の検索でより広範なスコープをカバー（既存ゲーム、市場トレンド、プレイヤーの不満・批判、インディーゲーム・海外事例）
- **補完モード**（`--search-engine google`）: Google検索でカバーされていない3観点を2〜3回のDuckDuckGo検索で補完

**プロンプトの核心部分:**
- Google検索結果との統合またはスタンドアロンでの網羅的調査
- プレイヤーの不満・批判（pain_points）の収集
- 結果をJSONで出力

**出力スキーマ:** ResearchOutput と同一構造（`pain_points` フィールドを含む）

---

### Agent ③〜⑧ BrainstormPipeline（ネストされたSequentialAgent）

| 項目 | 内容 |
|------|------|
| ファイルパス | `src/game_pitch_agent/agents/brainstorm.py` |
| クラス | `SequentialAgent`（サブエージェントを包含） |
| 役割 | 調査結果を基に5つの発散手法で多角的にゲームアイデアを生成し、統合する |
| 使用ツール | なし |

#### サブエージェント構成

| # | エージェント名 | 手法 | temperature | 最低生成数 | 出力キー |
|---|---------------|------|-------------|-----------|---------|
| ③ | ScamperAgent | SCAMPER（代替・組み合わせ・適用・変更・転用・排除・逆転） | 1.3 | 7個 | `scamper_output` |
| ④ | SixHatsAgent | 6 Thinking Hats（白・赤・黄・黒・緑・青の視点） | 1.4 | 6個 | `sixhats_output` |
| ⑤ | ReverseAgent | 逆転思考（「もし○○だったら？」） | 1.6 | 5個 | `reverse_output` |
| ⑥ | MandalartPipeline | マンダラート（曼荼羅チャート）2段階パイプライン | 1.2 | 6個 | `mandalart_stage1_output`, `mandalart_output` |
| ⑦ | ShiritoriAgent | アイデアしりとり（連想連鎖） | 1.5 | 10個 | `shiritori_output` |
| ⑧ | BrainstormMergeAgent | 5手法の統合・重複排除・交差分析・品質フィルタリング | デフォルト | 20個（フィルタリング後15個以上） | `brainstorm_output` |

#### MandalartPipeline（2段階構成）

MandalartAgent は MandalartPipeline に分割され、2段階で実行される:

| ステージ | エージェント名 | 出力キー | 内容 |
|---------|---------------|---------|------|
| Stage 1 | MandalartStage1Agent | `mandalart_stage1_output` | 中心ワード（center_word）+ 8つのstage1_words を生成 |
| Stage 2 | MandalartStage2Agent | `mandalart_output` | 64個の展開ワード（expanded words）、8つの選出ヒント（selected hints）、アイデアを生成 |

**MandalartOutput スキーマ:**
```json
{
  "center_word": "string",
  "stage1_words": ["string（8個）"],
  "expanded_words": ["string（64個）"],
  "selected_hints": ["string（8個）"],
  "ideas": [
    {
      "idea": "string",
      "method": "マンダラート - [概念]",
      "rationale": "string",
      "is_convention_breaking": false
    }
  ]
}
```

#### 品質フィルタリング

BrainstormMergeAgent は統合時に品質フィルタリングを実施する:

- **除外基準:**
  - 既存タイトルとの強い関連（既存ゲームの焼き直し）
  - 抽象的すぎるアイデア（具体的なメカニクスが見えない）
  - 技術的に実現不可能なアイデア
- **フィルタリング後の最低アイデア数:** 15個
- 除外されたアイデアは `filtered_ideas` に理由付きで記録

**革新性チェック:**
- 各サブエージェント③〜⑦が `is_convention_breaking` フラグでアイデアの革新性を明示
- ReverseAgent は全アイデアが `is_convention_breaking: true`
- BrainstormMergeAgent が5手法の結果を統合し `cross_connections`（意外な組み合わせ）を5つ以上抽出

**入力キー:** `research_output`（各サブエージェントが参照）

**出力スキーマ（BrainstormOutput）:**
```json
{
  "theme": "string",
  "ideas": [
    {
      "idea": "string",
      "method": "string（SCAMPER - Substitute / 6Hats - 白（事実） / 逆転思考 / マンダラート - [概念] / しりとり - [要素] など）",
      "rationale": "string",
      "is_convention_breaking": false
    }
  ],
  "filtered_ideas": [
    {
      "idea": "string",
      "method": "string",
      "exclusion_reason": "string（既存タイトル関連 / 抽象的すぎる / 技術的に不可能 など）"
    }
  ],
  "cross_connections": ["string"]
}
```

FilteredIdea: `idea`, `method`, `exclusion_reason`

---

### Agent ⑨ CoreIdeaAgent

| 項目 | 内容 |
|------|------|
| ファイルパス | `src/game_pitch_agent/agents/core_idea.py` |
| クラス | `LlmAgent` |
| 役割 | ブレインストーミング結果から具体的なコアアイデアを `num_pitches × min_ideas_multiplier` 個生成する |
| 使用ツール | なし |
| 温度設定 | `temperature=1.3` |
| 入力キー | `topic`, `brainstorm_output`, `num_pitches` |
| 出力キー | `core_ideas_output` |

**プロンプトの核心部分:**
- `min_ideas_count` 個以上のコアアイデアを生成（config では `min_ideas_multiplier = 5` を使用）
- 4軸の多様性を確保（操作感・感情目標・プレイスタイル・時間スケール）
- 各アイデアに `innovation_score`（1〜10）を付与
- 実験的アイデア（innovation_score 7以上）を約33%義務付け

**出力スキーマ（CoreIdeasOutput）:**
```json
{
  "ideas": [
    {
      "id": "idea_001",
      "title": "string",
      "genre": "string",
      "core_experience": "string",
      "target_player": "string",
      "core_mechanic": "string",
      "unique_selling_point": "string",
      "concept_statement": "string",
      "innovation_score": 7.5
    }
  ],
  "diversity_notes": "string"
}
```

---

### Agent ⑩ EvaluationAgent

| 項目 | 内容 |
|------|------|
| ファイルパス | `src/game_pitch_agent/agents/evaluation.py` |
| クラス | `LlmAgent` |
| 役割 | 4軸評価でアイデアをスコアリングし、多様性を最大化するよう `num_pitches` 個を選定する |
| 使用ツール | なし |
| 入力キー | `core_ideas_output`, `num_pitches` |
| 出力キー | `evaluation_output` |

**プロンプトの核心部分:**
- 4軸評価（斬新さ×0.4 + 明確さ×0.2 + 面白さ×0.2 + 実現可能性×0.2）
- 3ステップ選定プロセス:
  1. 各アイデアを4軸（操作感・感情目標・プレイスタイル・時間スケール）で分類
  2. **多様性ファースト**で選定（スコアだけでなく体験の差異を最優先）
  3. 多様性が同等の場合のみ weighted_score でタイブレイク

**出力スキーマ（EvaluationOutput）:**
```json
{
  "scores": [
    {
      "idea_id": "idea_001",
      "novelty": 8.5,
      "clarity": 7.0,
      "fun_factor": 9.0,
      "feasibility": 6.5,
      "total_score": 31.0,
      "weighted_score": 8.1,
      "core_experience_axes": {
        "operation": "アクション",
        "emotion": "スリル",
        "playstyle": "ソロ",
        "timescale": "数分"
      },
      "evaluation_comment": "string",
      "selected": true
    }
  ],
  "selected_idea_ids": ["idea_001", "idea_003"],
  "selection_rationale": "string"
}
```

---

### Agent ⑪ ExpansionAgent

| 項目 | 内容 |
|------|------|
| ファイルパス | `src/game_pitch_agent/agents/expansion.py` |
| クラス | `LlmAgent` |
| 役割 | 選定されたコアアイデアをペラ1企画書として使える内容に展開する |
| 使用ツール | なし |
| 入力キー | `core_ideas_output`, `evaluation_output`（`selected_idea_ids` を参照）, `critique_feedback`（リファインループ時） |
| 出力キー | `expanded_ideas_output` |

**プロンプトの核心部分:**
- コンセプト（感情・体験の目的地）とシステム（ゲームメカニクス）を明確に分離
- キャッチコピー: 発音しやすく・記憶に残る・独自性を一言で表現
- ゲームサイクル: トリガー → メインアクション → 短期報酬 → エスカレーション → トリガー の循環を明示
- ターゲットプレイヤー項目は非出力（普遍的な訴求力を重視）

**出力スキーマ（ExpandedIdeasOutput）:**
```json
{
  "pitches": [
    {
      "idea_id": "string",
      "title": "string",
      "catchcopy": "string（20文字以内）",
      "concept": "string（感情・体験の目的地）",
      "overview": "string（100文字程度）",
      "genre": "string",
      "platform": "string",
      "core_mechanic": "string",
      "game_cycle": {
        "trigger": "string",
        "main_action": "string",
        "short_term_reward": "string",
        "escalation": "string",
        "long_term_reward": "string"
      },
      "art_style": "string",
      "usp": "string",
      "feasibility_note": "string"
    }
  ]
}
```

---

### Agent ⑫ CritiqueAgent（新規）

| 項目 | 内容 |
|------|------|
| ファイルパス | `src/game_pitch_agent/agents/critique.py` |
| クラス | `LlmAgent` |
| 役割 | ExpansionAgent の出力を4軸で評価し、品質が閾値未満の場合はリファインループを実行する |
| 使用ツール | なし |
| 入力キー | `expanded_ideas_output` |
| 出力キー | `critique_output` |
| 実行位置 | メインパイプライン（SequentialAgent）の外で個別実行 |

**4軸評価スコアリング:**

| 軸 | 説明 |
|----|------|
| `concept_mechanic_alignment` | コンセプトとメカニクスの整合性 |
| `game_cycle_concreteness` | ゲームサイクルの具体性 |
| `catchcopy_originality` | キャッチコピーの独自性 |
| `usp_differentiation` | USPの差別化度 |

**リファインループ:**
1. CritiqueAgent が expanded_ideas_output を評価
2. 4軸スコアの平均値が `critique_threshold`（デフォルト 6.0）未満の場合:
   - `critique_feedback` を Session State に注入
   - ExpansionAgent を再実行
   - 最大 `critique_max_reruns`（デフォルト 3）回まで繰り返し
3. 閾値を満たすか最大回数に達したら次のステップへ

**出力スキーマ（CritiqueOutput）:**
```json
{
  "feedbacks": [
    {
      "idea_id": "string",
      "concept_mechanic_alignment": 7.5,
      "game_cycle_concreteness": 6.0,
      "catchcopy_originality": 8.0,
      "usp_differentiation": 5.5,
      "avg_score": 6.75,
      "comment": "string（改善提案）"
    }
  ]
}
```

CritiqueFeedback: `idea_id`, `concept_mechanic_alignment`, `game_cycle_concreteness`, `catchcopy_originality`, `usp_differentiation`, `avg_score`, `comment`

---

### Agent ⑬ ImagePromptAgent

| 項目 | 内容 |
|------|------|
| ファイルパス | `src/game_pitch_agent/agents/image_prompt.py` |
| クラス | `LlmAgent` |
| 役割 | 展開された企画書ごとに、ペラ1画像生成用のプロンプトを作成する |
| 使用ツール | なし |
| 入力キー | `expanded_ideas_output` |
| 出力キー | `image_prompts_output` |
| 実行位置 | メインパイプライン（SequentialAgent）の外で個別実行 |

**プロンプトの核心部分:**
- 言語設定（`ja`/`en`）に応じて2種類の命令文を使い分け
- 画像サイズ 1024×512px 横長フォーマット
- レイアウト5パターン: HORIZONTAL_SPLIT / VERTICAL_STACK / FULL_OVERLAY / TRIPTYCH / GAMEPLAY_MOCKUP（または自由考案）
- 複数の企画書が同じレイアウトにならないよう多様性を指示
- **ビジュアル要件:** 「代表的なゲームシーン」を視覚的に表現すること
- **テキスト優先度ルール:**
  - 必須（required）: タイトル
  - 推奨（recommended）: キャッチコピー
  - 任意（optional）: キーワード
  - 禁止（prohibited）: 長文説明、UIテキスト

**出力スキーマ（ImagePromptsOutput）:**
```json
{
  "image_prompts": [
    {
      "idea_id": "string",
      "title": "string",
      "prompt": "string（画像生成プロンプト）",
      "layout_description": "string",
      "art_style_notes": "string"
    }
  ]
}
```

---

### Agent ⑭ PitchEvaluatorPipeline（オプション・事後評価・マルチエージェント）

| 項目 | 内容 |
|------|------|
| ファイルパス | `src/game_pitch_agent/agents/pitch_evaluator.py` |
| クラス | `SequentialAgent`（5つの LlmAgent サブエージェントを包含） |
| 役割 | 生成済みの企画書を4専門グループで16軸（各0〜10点）事後評価する |
| 使用ツール | なし |
| 入力キー | `pitch_data`（pitch.json全体）、`evaluation_topic`（トピック） |
| 出力キー | `pitch_evaluation_output`（最終出力、EvalMergeAgent が書き込み） |
| 実行位置 | `evaluate` サブコマンドまたは `full --evaluate` フラグで個別実行 |

#### サブエージェント構成

| # | エージェント名 | グループ | ペルソナ | 担当軸数 | 出力キー |
|---|---------------|---------|---------|---------|---------|
| A | InnovationEvalAgent | Innovation（革新性） | イノベーション・スカウト | 3 | `eval_innovation_output` |
| B | CoherenceEvalAgent | Coherence（設計整合性） | デザインアーキテクト | 6 | `eval_coherence_output` |
| C | PlayabilityEvalAgent | Playability（プレイアビリティ） | プレイテスター | 4 | `eval_playability_output` |
| D | PresentationEvalAgent | Presentation（プレゼンテーション） | マーケティングディレクター | 2 | `eval_presentation_output` |
| M | EvalMergeAgent | Merge（統合） | ベテランゲーム批評家 | 1 | `pitch_evaluation_output` |

**アーキテクチャ:**
```
PitchEvaluatorOnlyPipeline (SequentialAgent) ← pipeline.py が生成
  └── PitchEvaluatorPipeline (SequentialAgent) ← create_pitch_evaluator_agent() の返り値
        ├── InnovationEvalAgent      → eval_innovation_output
        ├── CoherenceEvalAgent       → eval_coherence_output
        ├── PlayabilityEvalAgent     → eval_playability_output
        ├── PresentationEvalAgent    → eval_presentation_output
        └── EvalMergeAgent           → pitch_evaluation_output（最終出力）
```

**各グループの評価軸:**

| グループ | 軸 |
|---------|-----|
| A: Innovation | concept_novelty, core_mechanic_novelty, feasibility |
| B: Coherence | theme_concept_relevance, theme_art_style_relevance, design_coherence, art_style_concept_coherence, mechanic_art_style_coherence, thematic_mechanic_unity |
| C: Playability | mechanic_intuitiveness, game_cycle_quality, game_feel, risk_reward_depth |
| D: Presentation | first_impression_hook, elevator_pitch_clarity |
| Merge | overall_fun + summary |

**出力スキーマ（PitchEvaluation — 変更なし）:**
```json
{
  "idea_id": "string",
  "title": "string",
  "topic": "string",
  "concept_novelty": 0.0,
  "core_mechanic_novelty": 0.0,
  "...": "（16軸すべて 0.0〜10.0）",
  "summary": "string（総合評価コメント）"
}
```

---

### Agent ⑮ OverviewEvaluatorAgent（俯瞰比較評価）

| 項目 | 内容 |
|------|------|
| ファイルパス | `src/game_pitch_agent/agents/overview_evaluator.py` |
| クラス | `LlmAgent` |
| 役割 | 全pitchを俯瞰して多様性・ランキング・総合コメントを生成する |
| 使用ツール | なし |
| 入力 | ユーザーメッセージに全pitchのマークダウン + evaluation.json を埋め込み |
| 出力キー | `overview_evaluation_output` |
| 実行条件 | 評価済みpitchが2件以上の場合に自動実行。`--no-overview` でスキップ |

**処理の分担:**
- **Python側（pipeline.py）**: `axis_averages`（16軸の全pitch平均値）を算出
- **LLM側**: `diversity_scores`（7カテゴリ）、`pitch_rankings`、`summary` を生成

**出力スキーマ（OverviewEvaluation）:**
```json
{
  "topic": "お題名",
  "pitch_count": 3,
  "generated_at": "2026-03-08T12:00:00+09:00",
  "axis_averages": {
    "concept_novelty": 5.5,
    "...": "（16軸すべての全pitch平均値）"
  },
  "diversity_scores": {
    "concept_diversity": 7.0,
    "mechanic_diversity": 6.5,
    "genre_diversity": 8.0,
    "art_style_diversity": 5.0,
    "world_setting_diversity": 7.5,
    "target_player_diversity": 6.0,
    "overall_diversity": 6.5
  },
  "pitch_rankings": [
    {
      "rank": 1,
      "idea_id": "...",
      "title": "...",
      "avg_score": 6.2,
      "overall_fun": 7.0,
      "strengths": "この企画の強み（50文字程度）"
    }
  ],
  "summary": "全体を俯瞰した総合コメント（200-300文字）"
}
```

---

## 4. ツール詳細

### ツール① google_search（ADK組み込み）

| 項目 | 内容 |
|------|------|
| ファイル | Google ADK 内蔵（`from google.adk.tools import google_search`） |
| 用途 | Google検索を実行してウェブ情報を取得 |
| 使用エージェント | GoogleResearchAgent（`--search-engine google` 時のみ） |

**引数:** クエリ文字列（エージェントが自然言語で渡す）
**戻り値:** 検索結果テキスト（ADKが自動処理）
**エラーハンドリング:** ADKフレームワーク側で管理

---

### ツール② duckduckgo_search（カスタムツール）

| 項目 | 内容 |
|------|------|
| ファイル | `src/game_pitch_agent/tools/web_search.py` |
| 用途 | DuckDuckGoでウェブ検索を行い、結果を整形した文字列で返す |
| 使用エージェント | DuckDuckGoResearchAgent |

**引数:**

| 引数名 | 型 | デフォルト | 説明 |
|--------|-----|-----------|------|
| `query` | `str` | 必須 | 検索クエリ |
| `max_results` | `int` | `5` | 最大結果件数 |

**戻り値:** 各結果を `{番号}. **{タイトル}**\n   {本文}\n   URL: {url}` 形式に整形した文字列

**エラーハンドリング:**
- `ImportError`: `duckduckgo-search` ライブラリ未インストール → エラーメッセージ文字列を返す
- `Exception`: 検索失敗 → `f"検索エラー: {str(e)}"` を返す

---

### ツール③ generate_pitch_image（パイプライン外ツール）

| 項目 | 内容 |
|------|------|
| ファイル | `src/game_pitch_agent/tools/image_gen.py` |
| 用途 | Gemini画像生成モデルでペラ1企画書画像を生成・PNG保存する |
| 使用箇所 | `main.py`（パイプライン実行後に呼び出し、`--format image` 時） |

**引数:**

| 引数名 | 型 | デフォルト | 説明 |
|--------|-----|-----------|------|
| `prompt` | `str` | 必須 | 画像生成プロンプト |
| `output_path` | `str` | 必須 | 保存先パス（.png） |
| `model_name` | `str` | `gemini-2.0-flash-preview-image-generation` | 使用モデル名 |
| `width` | `int` | `1024` | 画像幅（px） |
| `height` | `int` | `512` | 画像高さ（px） |

**戻り値:** 保存先パス文字列（成功時）

**エラーハンドリング:**
- `GOOGLE_API_KEY` 未設定時に `ValueError` を raise
- 画像データが含まれない場合に `RuntimeError` を raise
- その他例外はログ記録後に再 raise

**リトライ機能:**
- 指数バックオフによるリトライ（最大3回: 1秒 → 2秒 → 4秒）
- セーフティフィルター検出時にプロンプトをソフトニング（表現を穏やかに修正）して再試行
- 各リトライのログ記録

**処理フロー:**
1. `GOOGLE_API_KEY` 環境変数を確認
2. `genai.Client` で Gemini API に接続
3. `generate_content()` で画像生成リクエスト（`response_modalities=["IMAGE", "TEXT"]`）
4. レスポンスから `inline_data` を抽出
5. base64デコード後、Pillowで指定サイズにリサイズしてPNG保存
6. 失敗時: 指数バックオフで再試行（セーフティフィルター時はプロンプトソフトニング）

---

### ツール④ render_pitch_pptx（パイプライン外ツール）

| 項目 | 内容 |
|------|------|
| ファイル | `src/game_pitch_agent/tools/pptx_render.py` |
| 用途 | python-pptxでペラ1企画書をPowerPoint形式（.pptx）で生成・保存する |
| 使用箇所 | `main.py`（パイプライン実行後に呼び出し、`--format pptx` 時） |

**引数:**

| 引数名 | 型 | デフォルト | 説明 |
|--------|-----|-----------|------|
| `pitch` | `dict` | 必須 | ExpandedPitchフィールドの辞書 |
| `output_path` | `str` | 必須 | 保存先パス（.pptx） |
| `image_path` | `str \| None` | `None` | 埋め込み画像パス（あれば） |

**戻り値:** 保存先パス文字列

**特徴:**
- 16:9 Blankスライドに6セクション（コンセプト、コアメカニクス、ゲーム概要、ゲームサイクル、アートスタイル+画像、USP+実現可能性）を2カラムで配置
- フォント: Meiryo（日本語対応）
- タイトルバー: 濃紺(#1B2A4A) + 白文字、ジャンル/プラットフォームバッジ
- GOOGLE_API_KEY不要（ローカル生成のみ）

---

## 5. Session State データフロー

| フェーズ | 追加・更新されるキー | 読み取るキー |
|---------|-------------------|------------|
| 初期化（pipeline.py） | `topic`, `num_pitches`, `min_ideas_count` | -- |
| Agent①実行後（optional） | `google_research_output` | `topic` |
| Agent②実行後 | `research_output`（Google+DDG統合 or DDGスタンドアロン） | `topic`, `google_research_output`（存在時） |
| Agent③実行後 | `scamper_output` | `research_output` |
| Agent④実行後 | `sixhats_output` | `research_output` |
| Agent⑤実行後 | `reverse_output` | `research_output` |
| Agent⑥-Stage1実行後 | `mandalart_stage1_output`（center_word + 8 stage1_words） | `research_output` |
| Agent⑥-Stage2実行後 | `mandalart_output`（64 expanded words + hints + ideas） | `research_output`, `mandalart_stage1_output` |
| Agent⑦実行後 | `shiritori_output` | `research_output` |
| Agent⑧実行後 | `brainstorm_output`（5手法統合 + フィルタリング） | `scamper_output`, `sixhats_output`, `reverse_output`, `mandalart_output`, `shiritori_output` |
| Agent⑨実行後 | `core_ideas_output` | `brainstorm_output`, `topic`, `num_pitches` |
| Agent⑩実行後 | `evaluation_output` | `core_ideas_output`, `num_pitches` |
| Agent⑪実行後 | `expanded_ideas_output` | `core_ideas_output`, `evaluation_output`, `critique_feedback`（リファイン時） |
| Agent⑫実行後 | `critique_output`, `critique_feedback`（リファインループ時に注入） | `expanded_ideas_output` |
| Agent⑬実行後 | `image_prompts_output` | `expanded_ideas_output` |

---

## 6. スキーマ一覧（Pydantic Models）

定義ファイル: `src/game_pitch_agent/schemas/models.py`

### ResearchOutput

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `original_topic` | `str` | 元のトピック |
| `research_items` | `list[ResearchItem]` | 調査結果リスト |
| `market_context` | `str` | 市場・トレンドの文脈 |
| `related_games` | `list[str]` | 関連する既存ゲームタイトル |
| `pain_points` | `list[str]` | プレイヤーの不満・批判点 |

ResearchItem: `topic`, `summary`, `key_insights: list[str]`, `source_hints: list[str]`

---

### BrainstormOutput

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `theme` | `str` | ブレインストーミングのテーマ |
| `ideas` | `list[BrainstormIdea]` | 発散したアイデアリスト（フィルタリング後15個以上、統合時20個以上） |
| `filtered_ideas` | `list[FilteredIdea]` | 品質フィルタリングで除外されたアイデアリスト |
| `cross_connections` | `list[str]` | アイデア間の意外な組み合わせ |

BrainstormIdea: `idea`, `method`, `rationale`, `is_convention_breaking: bool`

FilteredIdea: `idea`, `method`, `exclusion_reason`

---

### MandalartOutput（新規）

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `center_word` | `str` | マンダラート中心ワード |
| `stage1_words` | `list[str]` | Stage1で生成された8つの関連ワード |
| `expanded_words` | `list[str]` | Stage2で展開された64個のワード |
| `selected_hints` | `list[str]` | 選出された8つのヒントワード |
| `ideas` | `list[BrainstormIdea]` | マンダラートから生成されたアイデアリスト |

---

### CoreIdeasOutput

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `ideas` | `list[CoreGameIdea]` | コアアイデアリスト（`num_pitches × multiplier` 個以上） |
| `diversity_notes` | `str` | 多様性を確保するために意識した点 |

CoreGameIdea: `id`, `title`, `genre`, `core_experience`, `target_player`, `core_mechanic`, `unique_selling_point`, `concept_statement`, `innovation_score: float(1-10)`

---

### EvaluationOutput

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `scores` | `list[IdeaScore]` | 全アイデアのスコアリスト |
| `selected_idea_ids` | `list[str]` | 選定されたアイデアIDリスト |
| `selection_rationale` | `str` | 選定理由（多様性の観点を含む） |

IdeaScore: `idea_id`, `novelty`, `clarity`, `fun_factor`, `feasibility`, `total_score`, `weighted_score`, `core_experience_axes(CoreExperienceAxes)`, `evaluation_comment`, `selected: bool`

CoreExperienceAxes: `operation`, `emotion`, `playstyle`, `timescale`

---

### ExpandedIdeasOutput

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `pitches` | `list[ExpandedPitch]` | 展開された企画書リスト（`num_pitches` 個） |

ExpandedPitch: `idea_id`, `title`, `catchcopy`, `concept`, `overview`, `genre`, `platform`, `core_mechanic`, `game_cycle(GameCycle)`, `art_style`, `usp`, `feasibility_note`

GameCycle: `trigger`, `main_action`, `short_term_reward`, `escalation`, `long_term_reward`

**GameCycleの循環構造:**
```
trigger → main_action → short_term_reward → escalation → trigger（ループ）
                                                ↓
                                          long_term_reward（累積目標）
```

---

### CritiqueOutput（新規）

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `feedbacks` | `list[CritiqueFeedback]` | 各企画書への評価フィードバックリスト |

CritiqueFeedback: `idea_id`, `concept_mechanic_alignment: float`, `game_cycle_concreteness: float`, `catchcopy_originality: float`, `usp_differentiation: float`, `avg_score: float`, `comment: str`

---

### ImagePromptsOutput

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `image_prompts` | `list[ImagePrompt]` | 画像生成プロンプトリスト（`num_pitches` 個） |

ImagePrompt: `idea_id`, `title`, `prompt`, `layout_description`, `art_style_notes`

---

### OverviewEvaluation（俯瞰比較評価）

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `topic` | `str` | お題名 |
| `pitch_count` | `int` | 評価対象のpitch数 |
| `generated_at` | `str` | 生成日時（ISO 8601） |
| `axis_averages` | `dict[str, float]` | 16軸の全pitch平均値 |
| `diversity_scores` | `DiversityScores` | 多様性スコア（7カテゴリ） |
| `pitch_rankings` | `list[PitchRanking]` | 推薦順位 |
| `summary` | `str` | 俯瞰コメント |

DiversityScores: `concept_diversity`, `mechanic_diversity`, `genre_diversity`, `art_style_diversity`, `world_setting_diversity`, `target_player_diversity`, `overall_diversity`

PitchRanking: `rank`, `idea_id`, `title`, `avg_score`, `overall_fun`, `strengths`

---

### PitchDocument（最終出力集約）

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `idea_id` | `str` | アイデアID |
| `title` | `str` | ゲームタイトル |
| `pitch` | `ExpandedPitch` | 展開済み企画書 |
| `image_prompt` | `ImagePrompt` | 画像生成プロンプト |
| `image_path` | `Optional[str]` | 生成された画像のパス |
| `markdown_path` | `Optional[str]` | Markdownファイルのパス |
| `json_path` | `Optional[str]` | JSONファイルのパス |

---

## 7. パイプライン実行フロー

実装ファイル: `src/game_pitch_agent/pipeline.py`

```
run_pipeline(topic, config, output_dir)
    │
    ├─① エージェントを作成
    │     - create_google_research_agent(model)  ← --search-engine google 時のみ
    │     - create_ddg_research_agent(model)
    │     - create_brainstorm_pipeline(model)  ← 内部にサブエージェント
    │       └── MandalartPipeline（2段階: Stage1 + Stage2）
    │     - create_core_idea_agent(model)
    │     - create_evaluation_agent(model)
    │     - create_expansion_agent(model)
    │     - create_critique_agent(model)       ← メインパイプライン外で実行
    │     - create_image_prompt_agent(model, language)  ← メインパイプライン外で実行
    │
    ├─② SequentialAgent にステップ1〜11のエージェントを登録
    │     pipeline = SequentialAgent(name="GamePitchPipeline", sub_agents=agents)
    │
    ├─③ InMemorySessionService + Runner を初期化
    │
    ├─④ 初期 Session State を設定
    │     { topic, num_pitches, min_ideas_count }
    │
    ├─⑤ runner.run_async() でメインパイプラインを非同期実行
    │     イベントループで is_final_response() を待機
    │
    ├─⑥ CritiqueAgent を実行（リファインループ）
    │     ├─ expanded_ideas_output を評価
    │     ├─ avg_score < critique_threshold の場合:
    │     │   ├─ critique_feedback を Session State に注入
    │     │   ├─ ExpansionAgent を再実行
    │     │   └─ 最大 critique_max_reruns 回まで繰り返し
    │     └─ critique_output を Session State に保存
    │
    ├─⑦ ImagePromptAgent を個別実行
    │
    ├─⑧ session_service.get_session() で最終 Session State を取得
    │
    ├─⑨ extract_json_from_state() で各エージェントの出力をJSONにパース
    │     ステップ分のログを logs/{step:02d}_{agent_name}.log に保存
    │
    ├─⑩ JSON検証ミドルウェア
    │     各 state_key の出力を Pydantic model_validate() で検証
    │     バリデーションエラー時は warning ログ（パイプラインは継続）
    │
    ├─⑪ トークン使用量統計を収集
    │     stats.json を出力ディレクトリに保存
    │     コンソールにサマリを表示
    │
    └─⑫ 結果辞書を返す
          { topic, config, google_research_output, ..., critique_output, image_prompts_output }
```

### extract_json_from_state() の処理フロー

LLMが出力した値が文字列の場合、以下の手順でJSONに変換する:

```
1. dict/list型なら直接返す
2. str型の場合:
   a. コードブロック（``` ）を除去
   b. json.loads() で直接パース → 成功なら返す
   c. { or [ を起点に json.JSONDecoder.raw_decode() で抽出
   d. 全て失敗 → warning ログを出力して None を返す
```

### JSON検証ミドルウェア

パイプライン実行後、各エージェントの出力を対応する Pydantic モデルで検証する:

```
各 state_key に対して:
  1. Pydantic model_validate() を実行
  2. 成功 → そのまま使用
  3. 失敗 → warning ログを出力（パイプラインは停止せず継続）
```

---

## 8. 設定システム

### 8.1 設定ファイル構成

| ファイル | 役割 |
|---------|------|
| `config.yaml` | 主設定ファイル（モード、モデル名、生成パラメータ） |
| `src/game_pitch_agent/config.py` | YAML読み込み + Pydanticモデル定義 |

### 8.2 config.yaml の構造

```yaml
mode: test  # test | prod

models:
  inference:
    prod: gemini-3.1-pro-preview       # 高品質・高コスト
    test: gemini-2.5-flash-lite        # 低コスト・高速
  image_generation:
    prod: gemini-3.1-flash-image-preview
    test: gemini-3.1-flash-image-preview

generation:
  num_pitches: 3             # 生成する企画書の数（prodモード時）
  num_pitches_test: 2        # テストモード時の企画書の数
  min_ideas_multiplier: 5    # CoreIdeaAgent が生成する最低アイデア数の倍率
  image_width: 1024          # 画像幅（px）
  image_height: 512          # 画像高さ（px）
  language: ja               # ja | en（画像プロンプトの言語）
  critique_threshold: 6.0    # CritiqueAgent の合格閾値（4軸平均スコア）
  critique_max_reruns: 3     # リファインループの最大回数

output:
  directory: output          # 出力先ディレクトリ
```

### 8.3 Pydantic 設定モデル

```
AppConfig
├── mode: Literal["test", "prod"]
├── models: ModelsConfig
│   ├── inference_prod: str
│   ├── inference_test: str
│   ├── image_generation_prod: str
│   └── image_generation_test: str
├── generation: GenerationConfig
│   ├── num_pitches: int = 3
│   ├── num_pitches_test: int = 2
│   ├── min_ideas_multiplier: int = 2
│   ├── image_width: int = 1024
│   ├── image_height: int = 512
│   ├── language: Literal["ja", "en"] = "ja"
│   ├── critique_threshold: float = 6.0
│   └── critique_max_reruns: int = 3
└── output: OutputConfig
    └── directory: str = "output"
```

`AppConfig.inference_model` プロパティ: `mode` に応じて `inference_prod` / `inference_test` を返す
`AppConfig.image_model` プロパティ: `mode` に応じて `image_generation_prod` / `image_generation_test` を返す

テストモード時は `num_pitches_test` の値が `num_pitches` に自動適用される。

### 8.4 CLI引数による上書き

`main.py` からの CLI 引数で設定を動的に上書き可能:

```bash
uv run game-pitch --topic "忍者×タイムトラベル"
uv run game-pitch --topic "..." --mode prod
uv run game-pitch --topic "..." --num-pitches 5
uv run game-pitch --topic "..." --language en
uv run game-pitch --topic "..." --search-engine google    # Google検索も併用
uv run game-pitch --topic "..." --search-engine ddg       # DDGのみ（デフォルト）
uv run game-pitch --topic "..." --mode prod --num-pitches 3 --language en
```

---

## 9. 出力ディレクトリ構造

```
output/
└── {YYYYMMDD_HHMMSS}_{topic(先頭30文字)}/
    ├── request_info.json              # リクエストメタデータ
    ├── stats.json                     # トークン使用量統計
    ├── logs/
    │   ├── session.log                # セッション全体ログ
    │   ├── 01_google_research.log     # Agent①の出力JSON（optional）
    │   ├── 02_ddg_research.log        # Agent②の出力JSON
    │   ├── 03_brainstorm_scamper.log  # Agent③の出力JSON
    │   ├── 04_brainstorm_sixhats.log  # Agent④の出力JSON
    │   ├── 05_brainstorm_reverse.log  # Agent⑤の出力JSON
    │   ├── 06_brainstorm_mandalart_stage1.log # Agent⑥-Stage1の出力JSON
    │   ├── 07_brainstorm_mandalart.log # Agent⑥-Stage2の出力JSON
    │   ├── 08_brainstorm_shiritori.log # Agent⑦の出力JSON
    │   ├── 09_brainstorm.log          # Agent⑧の出力JSON（統合結果）
    │   ├── 10_core_idea.log           # Agent⑨の出力JSON
    │   ├── 11_evaluation.log          # Agent⑩の出力JSON
    │   ├── 12_expansion.log           # Agent⑪の出力JSON
    │   ├── 13_critique.log            # Agent⑫の出力JSON
    │   └── 14_image_prompt.log        # Agent⑬の出力JSON
    ├── pitch_1/
    │   ├── pitch.json                 # 企画書データ（JSON形式）
    │   ├── pitch.md                   # 企画書（Markdown形式）
    │   ├── pitch_image.png            # 企画書画像（--format image時、1024×512px）
    │   └── pitch.pptx                 # PowerPoint企画書（--format pptx時）
    ├── pitch_2/
    │   ├── pitch.json
    │   ├── pitch.md
    │   ├── pitch_image.png
    │   └── pitch.pptx
    ├── pitch_N/
    │   ├── pitch.json
    │   ├── pitch.md
    │   ├── pitch_image.png
    │   └── pitch.pptx
    └── overview_evaluation.json       # 俯瞰比較評価（pitch 2件以上時）
```

ログファイルの構造（各エージェントのログ）:
```json
{
  "agent": "agent_name",
  "state_key": "state_key_name",
  "timestamp": "ISO8601文字列",
  "data": { ... }  // 正常時
  // または
  "raw": "生テキスト（先頭5000文字）",
  "error": "JSONデコード失敗"  // エラー時
}
```

---

## 10. 重要な設計パターン

### 10.1 多段階アイデア絞り込み

```
BrainstormPipeline: 5手法 × 各5〜10個 = 34個以上（発散）
        ↓ BrainstormMergeAgent統合 + 品質フィルタリング
BrainstormMergeAgent: 20個以上（重複排除・統合）→ フィルタリング後15個以上
        ↓
CoreIdeaAgent:   num_pitches × multiplier 個（具体化）
                 例: 3 × 5 = 15個以上
        ↓
EvaluationAgent: num_pitches 個（選定）
                 例: 3個
        ↓
ExpansionAgent:  num_pitches 個（深化）
        ↓
CritiqueAgent:   品質評価 → 閾値未満なら ExpansionAgent に戻る（最大3回）
```

アイデアを段階的に絞り、CritiqueAgent のリファインループで品質を担保することで、高品質な企画書のみが最終出力に残る。

---

### 10.2 ネストされたパイプライン構造

BrainstormPipeline は `SequentialAgent` のネスト構造を採用:

```
GamePitchPipeline (SequentialAgent) ← ステップ1〜11
  ├── GoogleResearchAgent (LlmAgent) ← optional
  ├── DuckDuckGoResearchAgent (LlmAgent)
  └── BrainstormPipeline (SequentialAgent)
  │     ├── ScamperAgent (LlmAgent)
  │     ├── SixHatsAgent (LlmAgent)
  │     ├── ReverseAgent (LlmAgent)
  │     ├── MandalartPipeline (SequentialAgent)
  │     │     ├── MandalartStage1Agent (LlmAgent)
  │     │     └── MandalartStage2Agent (LlmAgent)
  │     ├── ShiritoriAgent (LlmAgent)
  │     └── BrainstormMergeAgent (LlmAgent)
  ├── CoreIdeaAgent (LlmAgent)
  ├── EvaluationAgent (LlmAgent)
  └── ExpansionAgent (LlmAgent)

CritiqueAgent (LlmAgent) ← 個別実行、リファインループ
ImagePromptAgent (LlmAgent) ← 個別実行
PitchEvaluatorPipeline (SequentialAgent) ← 個別実行
  ├── InnovationEvalAgent (LlmAgent)
  ├── CoherenceEvalAgent (LlmAgent)
  ├── PlayabilityEvalAgent (LlmAgent)
  ├── PresentationEvalAgent (LlmAgent)
  └── EvalMergeAgent (LlmAgent)
OverviewEvaluatorAgent (LlmAgent) ← 個別実行、pitch 2件以上時
```

各サブエージェントが独立した発散手法を担当し、最後にMergeAgentが統合する。
Session State を共有するため、各サブエージェントは同一の `research_output` を参照できる。

---

### 10.3 多様性ファースト選択

EvaluationAgent は単純なスコア順ではなく、**4軸での体験の多様性**を最優先で選定する:

```
Step 1: 操作感 × 感情目標 × プレイスタイル × 時間スケール で各アイデアを分類
Step 2: 4軸の組み合わせが最も異なるアイデアを選定（多様性最優先）
Step 3: 多様性が同等の場合のみ weighted_score でタイブレイク
```

これにより、似たようなゲームが複数生成されることを防ぎ、バリエーションに富む企画書セットを実現する。

---

### 10.4 JSON抽出の堅牢化（extract_json_from_state）

LLMの出力は必ずしも純粋なJSONではないため、複数段階のフォールバックでパースを行う:

```python
1. dict/list型なら直接返す
2. str型の場合:
   a. コードブロック（``` ）を除去
   b. json.loads() で直接パース
   c. { or [ を起点に json.JSONDecoder.raw_decode() で抽出
   d. 全て失敗 → None を返しフォールバックログを保存
```

---

### 10.5 2モード構成（test / prod）

| 設定 | test モード | prod モード |
|------|------------|------------|
| 推論モデル | `gemini-2.5-flash-lite`（高速・低コスト） | `gemini-3.1-pro-preview`（高品質） |
| 企画書数 | `num_pitches_test`（デフォルト2） | `num_pitches`（デフォルト3） |
| 用途 | 開発・デバッグ | 本番生成 |
| CLI切り替え | `--mode test`（デフォルト） | `--mode prod` |

---

### 10.6 革新性の強制

BrainstormPipeline と CoreIdeaAgent の両方で「常識を覆すアイデア」の割合を指定:

- **BrainstormPipeline**:
  - 各サブエージェントが `is_convention_breaking` フラグを付与
  - ReverseAgent は全アイデアが `is_convention_breaking: true`
  - 5手法で多角的に革新性を確保
- **CoreIdeaAgent**: `innovation_score 7以上` の実験的アイデアを約33%義務付け

これにより、ありきたりなゲームアイデアが量産されることを防ぐ。

---

### 10.7 温度制御による創造性の段階管理

| エージェント | temperature | 理由 |
|------------|-------------|------|
| Agent③ ScamperAgent | 1.3 | SCAMPER手法による構造的な発散 |
| Agent④ SixHatsAgent | 1.4 | 多角的視点からの発散 |
| Agent⑤ ReverseAgent | 1.6 | 最大限の逆転・破壊的発想 |
| Agent⑥ MandalartPipeline | 1.2 | 構造化された連想展開 |
| Agent⑦ ShiritoriAgent | 1.5 | 自由な連想連鎖 |
| Agent⑧ BrainstormMergeAgent | デフォルト | 正確な統合・分析 |
| Agent⑨ CoreIdeaAgent | 1.3 | 具体的だが創造的なアイデア生成 |
| その他全エージェント | デフォルト | 正確性・論理性を重視 |

---

### 10.8 CritiqueAgent によるリファインループ

ExpansionAgent の出力品質を担保するため、CritiqueAgent による評価・リファインループを実装:

```
ExpansionAgent → expanded_ideas_output
       ↓
CritiqueAgent（4軸評価）
       ↓
avg_score >= critique_threshold (6.0)?
  ├─ YES → 次のステップへ（ImagePromptAgent）
  └─ NO  → critique_feedback を注入して ExpansionAgent を再実行
            （最大 critique_max_reruns 回）
```

**4軸評価基準:**
1. **concept_mechanic_alignment** - コンセプトとメカニクスが一貫しているか
2. **game_cycle_concreteness** - ゲームサイクルが具体的で循環構造が明確か
3. **catchcopy_originality** - キャッチコピーが独自性を持ち印象に残るか
4. **usp_differentiation** - USPが既存タイトルと明確に差別化されているか

---

### 10.9 トークン使用量統計

パイプライン実行中にトークン使用量を収集し、実行完了後に統計情報を提供:

- **stats.json**: 出力ディレクトリに保存。各エージェントのトークン使用量を記録
- **コンソールサマリ**: パイプライン完了時にトークン使用量の概要を表示

---

### 10.10 JSON検証ミドルウェア

パイプラインの信頼性を高めるため、各エージェント出力を Pydantic モデルで検証する:

- 各 `state_key` に対して `model_validate()` を実行
- バリデーションエラー発生時は warning ログを出力
- パイプラインは停止せず処理を継続（グレースフルデグラデーション）
