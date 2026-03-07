# Game Pitch Agent

ゲームトピックを入力すると、マルチエージェントパイプラインがリサーチからペラ1企画書の生成・画像出力まで自動で行うAIエージェントシステムです。

## 概要

**Google ADK**（Agent Development Kit）の `SequentialAgent` を使い、専門エージェントを直列に接続したパイプラインで動作します。各エージェントは前段の結果を Session State 経由で受け取り、処理結果を次のエージェントへ渡します。

```
トピック入力
    │
    ▼
[1] GoogleResearchAgent      ← Google検索でトピック調査（--search-engine google 時のみ）
    │
    ▼
[2] DuckDuckGoResearchAgent  ← DDG検索（デフォルト単独 / Google併用時は補完）
    │
    ▼
[3-9] BrainstormPipeline     ← 5手法×サブエージェント + 品質フィルタリング統合
    ├── [3] ScamperAgent       ← SCAMPER 7視点
    ├── [4] SixHatsAgent       ← 6つの思考帽子
    ├── [5] ReverseAgent       ← 逆転思考
    ├── [6] MandalartPipeline  ← マンダラート2段階展開（Stage1→Stage2）
    ├── [7] ShiritoriAgent     ← アイデアしりとり
    └── [8] BrainstormMergeAgent ← 5手法の統合 + 品質フィルタリング
    │
    ▼
[9] CoreIdeaAgent            ← コアアイデアの抽出・具体化
    │
    ▼
[10] EvaluationAgent         ← 斬新さ/明確さ/面白さ/実現可能性でスコアリング・選定
    │
    ▼
[11] ExpansionAgent          ← 選定アイデアをペラ1企画書に展開
    │
    ▼
[12] CritiqueAgent           ← 品質批評（閾値未満→ExpansionAgent再実行、最大3回）
    │
    ▼
[13] ImagePromptAgent        ← 企画書ビジュアルの画像生成プロンプト作成
    │
    ▼
出力: Markdown / JSON / PNG画像 / stats.json
    │
    ▼ (オプション: evaluate コマンド or full --evaluate)
[14] PitchEvaluatorAgent    ← 16軸事後評価 → evaluation.json
```

## 出力サンプル

`output/<timestamp>_<topic>/pitch_1/` 以下に以下のファイルが生成されます。

```
output/
└── 20260301_120000_お題___不自由__/
    ├── request_info.json   # リクエスト情報ログ
    ├── logs/
    │   ├── session.log
    │   ├── 01_google_research.log
    │   ├── 02_ddg_research.log
    │   ├── 03_brainstorm_scamper.log
    │   ├── 04_brainstorm_sixhats.log
    │   ├── 05_brainstorm_reverse.log
    │   ├── 06_brainstorm_mandalart.log
    │   ├── 07_brainstorm_shiritori.log
    │   ├── 08_brainstorm.log
    │   ├── 09_core_idea.log
    │   ├── 10_evaluation.log
    │   ├── 11_expansion.log
    │   └── 12_image_prompt.log
    ├── pitch_1/
    │   ├── pitch.md        # Markdown形式の企画書
    │   ├── pitch.json      # 構造化データ
    │   ├── pitch_image.png # 企画書ビジュアル画像（--format image時）
    │   ├── pitch.pptx      # PowerPoint企画書（--format pptx時）
    │   ├── pitch.pdf       # PDF版（PPTX出力時に自動生成、要LibreOffice）
    │   ├── pitch.png       # PNGプレビュー（PPTX出力時に自動生成、要pdftoppm）
    │   └── evaluation.json # 16軸評価結果（evaluate実行時）
    └── pitch_2/
```

## セットアップ

### 前提条件

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) パッケージマネージャー
- Google AI Studio の API キー（[取得方法](https://aistudio.google.com/apikey)）

### インストール

```bash
# リポジトリをクローン
git clone <repository-url>
cd game-pitch-agent

# 依存パッケージをインストール
uv sync
```

### 環境変数の設定

プロジェクトルートに `.env` ファイルを作成してください。

```bash
# .env
GOOGLE_API_KEY=your_api_key_here
```

## 使い方

3つのサブコマンドで目的に応じた実行が可能です。

### `generate` — テキスト企画書のみ生成

テキストパイプライン（Steps 1-11）のみ実行し、Markdown / JSON 企画書を出力します。画像は生成しません。

```bash
# テストモードで企画書を生成
uv run game-pitch generate --topic "お題:「不自由」" --num-pitches 5

# 本番モードで5件生成
uv run game-pitch generate --topic "お題:「不自由」" --mode prod --num-pitches 5
```

### `render` — 既存の企画書から画像/PPTX生成

`generate` で出力した企画書ディレクトリに対して、画像生成またはPPTX生成を実行します。

```bash
# generate の出力ディレクトリを指定して画像生成（デフォルト）
uv run game-pitch render --dir output/20260301_120000_xxx

# PPTX形式で出力（GOOGLE_API_KEY不要）
uv run game-pitch render --dir output/20260301_120000_xxx --format pptx

# 言語を変更して再生成
uv run game-pitch render --dir output/20260301_120000_xxx --language en

# 既存画像/PPTXを上書き再生成
uv run game-pitch render --dir output/20260301_120000_xxx --force
```

### `full` — フルパイプライン実行

テキスト生成と画像/PPTX生成をまとめて一括実行します（従来の動作と同等）。

```bash
# フルパイプライン実行
uv run game-pitch full --topic "お題:「不自由」"

# PPTX形式で出力（画像生成AIを使わない）
uv run game-pitch full --topic "お題:「不自由」" --format pptx

# 本番モード・英語画像
uv run game-pitch full --topic "お題:「不自由」" --mode prod --language en

# 画像生成をスキップ（generateと同等の結果）
uv run game-pitch full --topic "お題:「不自由」" --no-image

# フルパイプライン実行後に自動評価
uv run game-pitch full --topic "お題:「不自由」" --no-image --evaluate
```

### `evaluate` — 既存の企画書を16軸で評価

生成済みの企画書に対して、16軸（各0〜10点）で自動評価を行い、`evaluation.json` を各ピッチフォルダに保存します。

```bash
# 既存の出力ディレクトリを指定して評価
uv run game-pitch evaluate --dir output/20260306_224547_xxx

# トピックを明示的に指定
uv run game-pitch evaluate --dir output/20260306_224547_xxx --topic "お題:「不自由」"

# テストモードで評価（軽量モデル使用）
uv run game-pitch evaluate --dir output/20260306_224547_xxx --mode test

# 既存の評価結果を上書き
uv run game-pitch evaluate --dir output/20260306_224547_xxx --force
```

### サブコマンド別オプション一覧

#### `generate` オプション

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `--topic` | ゲームアイデアのトピック（必須） | - |
| `--mode` | 実行モード `test` / `prod` | `config.yaml` の設定値 |
| `--num-pitches` | 生成する企画書の枚数 | test: 2 / prod: 3（`config.yaml`） |
| `--config` | 設定ファイルのパス | プロジェクトルートの `config.yaml` |
| `--search-engine` | 検索エンジン `ddg` / `google` | `ddg` |

#### `render` オプション

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `--dir` | 対象の出力ディレクトリ（必須） | - |
| `--format` | 出力形式 `image` / `pptx` | `image` |
| `--mode` | 実行モード `test` / `prod` | 元の `request_info.json` の値 |
| `--language` | 画像の言語 `ja` / `en` | 元の `request_info.json` の値 |
| `--force` | 既存画像/PPTXを上書き再生成 | `false` |
| `--config` | 設定ファイルのパス | プロジェクトルートの `config.yaml` |

#### `full` オプション

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `--topic` | ゲームアイデアのトピック（必須） | - |
| `--format` | 出力形式 `image` / `pptx` | `image` |
| `--mode` | 実行モード `test` / `prod` | `config.yaml` の設定値 |
| `--num-pitches` | 生成する企画書の枚数 | test: 2 / prod: 3（`config.yaml`） |
| `--language` | 画像の言語 `ja` / `en` | `config.yaml` の設定値（`ja`） |
| `--no-image` | 画像生成をスキップ | `false` |
| `--config` | 設定ファイルのパス | プロジェクトルートの `config.yaml` |
| `--search-engine` | 検索エンジン `ddg` / `google` | `ddg` |
| `--evaluate` | 生成後に企画書を自動評価 | `false` |

#### `evaluate` オプション

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `--dir` | 対象の出力ディレクトリ（必須） | - |
| `--topic` | 評価トピック | `request_info.json` の値 |
| `--mode` | 実行モード `test` / `prod` | `request_info.json` の値 |
| `--force` | 既存 `evaluation.json` を上書き | `false` |
| `--config` | 設定ファイルのパス | プロジェクトルートの `config.yaml` |

## 設定ファイル

`config.yaml` で動作設定を変更できます。

```yaml
mode: test  # test | prod

models:
  inference:
    prod: gemini-3.1-pro-preview    # 本番用推論モデル
    test: gemini-2.5-flash-lite     # テスト用推論モデル（低コスト）
  image_generation:
    prod: gemini-3.1-flash-image-preview
    test: gemini-3.1-flash-image-preview

generation:
  num_pitches: 3           # 生成する企画書の枚数
  min_ideas_multiplier: 5  # CoreIdeaAgent が生成するアイデアの最小倍率
  image_width: 1024        # 画像の幅（px）
  image_height: 512        # 画像の高さ（px）
  language: ja             # 企画書画像の言語: ja（日本語）/ en（英語）
  critique_threshold: 6.0  # CritiqueAgentの品質閾値（この値未満で再実行）
  critique_max_reruns: 3   # 最大リラン回数

output:
  directory: output        # 出力ディレクトリ
```

## プロジェクト構造

```
game-pitch-agent/
├── src/game_pitch_agent/
│   ├── agents/
│   │   ├── research.py       # Google / DuckDuckGo 検索エージェント
│   │   ├── brainstorm.py     # アイデア発散エージェント
│   │   ├── core_idea.py      # コアアイデア抽出エージェント
│   │   ├── evaluation.py     # アイデア評価・選定エージェント
│   │   ├── expansion.py      # 企画書展開エージェント
│   │   ├── critique.py       # 品質批評エージェント（リファインループ）
│   │   ├── image_prompt.py   # 画像プロンプト生成エージェント
│   │   └── pitch_evaluator.py # 企画書事後評価エージェント（16軸採点）
│   ├── schemas/
│   │   └── models.py         # Pydantic スキーマ定義
│   ├── tools/
│   │   ├── web_search.py     # DuckDuckGo 検索ツール
│   │   ├── image_gen.py      # Gemini 画像生成ツール
│   │   ├── pptx_render.py    # PPTX 企画書生成ツール
│   │   └── pptx_convert.py   # PPTX -> PDF/PNG 変換ツール
│   ├── config.py             # 設定ローダー
│   ├── constraints.py        # ランダム制約カード定義
│   ├── pipeline.py           # SequentialAgent パイプライン
│   └── main.py               # CLI エントリーポイント
├── config.yaml               # 設定ファイル
├── pyproject.toml            # パッケージ設定・依存関係
└── output/                   # 生成物出力ディレクトリ（.gitignore 対象）
```

## 依存ライブラリ

| ライブラリ | 用途 |
|-----------|------|
| `google-adk` | マルチエージェントフレームワーク |
| `google-genai` | Gemini API クライアント（推論・画像生成） |
| `duckduckgo-search` | DuckDuckGo 検索ツール |
| `pydantic` | エージェント間通信用スキーマ定義 |
| `pyyaml` | 設定ファイル読み込み |
| `pillow` | 画像処理 |
| `python-pptx` | PowerPoint（PPTX）生成 |
| `python-dotenv` | `.env` ファイルの読み込み |
| `libreoffice` | PPTX -> PDF変換（システムパッケージ、オプション） |
| `poppler-utils` | PDF -> PNG変換（`pdftoppm`、システムパッケージ、オプション） |
| `fonts-noto-cjk` | 日本語フォント（LibreOffice用、システムパッケージ、オプション） |

## 更新履歴

| バージョン | 日付 | 内容 |
|-----------|------|------|
| 0.9.3 | 2026-03-08 | トピック不一致問題修正: パイプライン全体でトピックが失われていた問題を解消。ExpansionAgent/MergeAgent/CritiqueAgent/EvaluationAgent/CoreIdeaAgentにトピック意識を追加、CritiqueとEvaluationに`topic_relevance`評価軸を新設、`_run_single_agent`のユーザーメッセージにtopicを含めるよう修正。theme_concept_relevanceが1.0→3.0〜9.0に大幅改善 ([Steering](Docs/Steering/202603080240_fix-topic-relevance-pipeline.md)) |
| 0.9.2 | 2026-03-07 | PitchEvaluatorAgentデータフロー修正: ユーザーメッセージにpitchデータを直接埋め込み、evaluation.jsonのタイトル・IDがpitch.jsonと不一致になるハルシネーション問題を解消 ([Steering](Docs/Steering/202603070645_fix-evaluator-dataflow.md)) |
| 0.9.1 | 2026-03-07 | 評価分析テスト: 8テーマ×16軸の横断分析を実施。ExpansionAgent出力パースのバグ修正(`_extract_pitches`関数追加) ([Steering](Docs/Steering/202603070400_evaluation-analysis.md)) |
| 0.9.0 | 2026-03-07 | 評価軸改善（17軸→16軸）: 冗長軸削除(concept_uniqueness/core_mechanic_uniqueness)、新軸追加(game_cycle_quality/elevator_pitch_clarity)、軸改名・統合(hook_strength→first_impression_hook, narrative_mechanic_integration→thematic_mechanic_unity, theme_core_mechanic_relevance+concept_mechanic_coherence→design_coherence) ([Steering](Docs/Steering/202603070400_improve-evaluation-axes.md)) |
| 0.8.0 | 2026-03-06 | 企画書評価AIエージェント追加: `evaluate` サブコマンドで生成済み企画書を16軸（各0〜10点）で自動評価。`full --evaluate` フラグで生成後に自動評価も可能。PitchEvaluatorAgent / PitchEvaluation スキーマ / evaluation.json 出力 ([Steering](Docs/Steering/202603070320_add-pitch-evaluator.md)) |
| 0.7.0 | 2026-03-06 | 企画書の面白さ・多様性向上: (1)CoreIdeaAgentでcross_connections活用 (2)ExpansionAgentにFew-shot例示追加 (3)新フィールド5種追加(play_scene/elevator_pitch/emotional_curve/target_player/camera_perspective) (4)Markdown出力をテーブル+フローチャート形式に刷新 (5)PPTX出力に新フィールド反映 (6)ランダム制約カードによるブレスト多様性強化 ([Steering](Docs/Steering/202603062330_improve-pitch-quality-diversity.md)) |
| 0.6.0 | 2026-03-06 | 12項目改善: CritiqueAgent+リファインループ新設、マンダラート2段階展開、Google検索オプション化(`--search-engine`)、温度設定個別チューニング、ゲームサイクル構造深化(trigger/escalation)、不満点調査追加、品質フィルタリング強化、画像生成リトライ機構、トークン統計出力(stats.json)、JSON検証ミドルウェア、ImagePromptバランス精密化、ゲーム画面モックアップ指示追加 ([Steering](Docs/Steering/improvement-12items-202603060330.md)) |
| 0.5.1 | 2026-03-06 | PPTX→PDF変換の日本語パス問題を修正: 一時ディレクトリ経由で変換することでLibreOfficeの非ASCIIパス問題を回避 ([Steering](Docs/Steering/fix-pptx-pdf-japanese-path-20260306.md)) |
| 0.5.0 | 2026-03-06 | PPTX出力時にPDF/PNGも同時出力: LibreOffice headless + pdftoppm で自動変換。ツール未インストール時はPPTXのみ生成 ([Steering](Docs/Steering/add-pptx-export-20260306.md)) |
| 0.4.0 | 2026-03-05 | PPTX出力機能追加: `--format pptx` オプションでPowerPoint形式の企画書を出力可能に。画像生成AI不要で動作 ([Steering](Docs/Steering/add-pptx-render-20260305.md)) |
| 0.3.0 | 2026-03-05 | サブコマンド化: `generate` / `render` / `full` の3コマンドに分離。テキスト生成のみ・画像のみ再生成が個別に実行可能に ([Steering](Docs/Steering/pipeline-subcommands-20260305.md)) |
| 0.2.1 | 2026-03-01 | `--no-image` オプション追加: 画像生成をスキップしてMarkdownのみ出力可能に ([Steering](Docs/Steering/add-no-image-option-20260301.md)) |
| 0.2.0 | 2026-03-01 | アイデア発散パイプライン刷新: BrainstormAgent を5手法別サブエージェント（SCAMPER/6Hats/逆転思考/マンダラート/しりとり）に分割、温度1.5設定、ターゲット情報削除、request_info.json出力追加 ([Steering](Docs/Steering/improvement-202603010219.md)) |
| 0.1.2 | 2026-02-28 | 品質改善: EvaluationAgent の多様性選定ロジック改善（3ステップ選定・重み付きスコア導入）、ImagePromptAgent のレイアウト多様化、BrainstormAgent/CoreIdeaAgent の革新性強化 ([Steering](Docs/Steering/fix-quality-issues-20260228.md)) |
| 0.1.1 | 2026-02-28 | 企画書画像の言語設定機能追加（`--language` オプション、`config.yaml` 対応、デフォルト日本語） ([Steering](Docs/Steering/add-language-option-20260228.md)) |
| 0.1.0 | 2026-02-27 | 初回実装 ([Steering](Docs/Steering/progress_20260227.md)) |
