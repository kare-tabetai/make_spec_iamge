# Game Pitch Agent

ゲームトピックを入力すると、マルチエージェントパイプラインがリサーチからペラ1企画書の生成・画像出力まで自動で行うAIエージェントシステムです。

## 概要

**Google ADK**（Agent Development Kit）の `SequentialAgent` を使い、7つの専門エージェントを直列に接続したパイプラインで動作します。各エージェントは前段の結果を Session State 経由で受け取り、処理結果を次のエージェントへ渡します。

```
トピック入力
    │
    ▼
[1] GoogleResearchAgent   ← Google検索でトピック調査
    │
    ▼
[2] DuckDuckGoResearchAgent ← DDG検索で補完・インディー/海外事例
    │
    ▼
[3] BrainstormAgent       ← SCAMPER・6 Hats等でアイデア発散
    │
    ▼
[4] CoreIdeaAgent         ← コアアイデアの抽出・具体化
    │
    ▼
[5] EvaluationAgent       ← 斬新さ/明確さ/面白さ/実現可能性でスコアリング・選定
    │
    ▼
[6] ExpansionAgent        ← 選定アイデアをペラ1企画書に展開
    │
    ▼
[7] ImagePromptAgent      ← 企画書ビジュアルの画像生成プロンプト作成
    │
    ▼
出力: Markdown / JSON / PNG画像
```

## 出力サンプル

`output/<timestamp>_<topic>/pitch_1/` 以下に以下のファイルが生成されます。

```
output/
└── 20260228_120000_宇宙を舞台にした孤独なロボット/
    ├── logs/
    │   ├── session.log
    │   ├── 01_google_research.log
    │   ├── 02_ddg_research.log
    │   ├── ...
    │   └── 07_image_prompt.log
    ├── pitch_1/
    │   ├── pitch.md        # Markdown形式の企画書
    │   ├── pitch.json      # 構造化データ
    │   └── pitch_image.png # 企画書ビジュアル画像
    ├── pitch_2/
    └── pitch_3/
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

### 基本的な使い方

```bash
# テストモード（デフォルト・低コスト）で実行
uv run game-pitch --topic "宇宙を舞台にした孤独なロボットの旅"

# 本番モード（高精度モデル）で実行
uv run game-pitch --topic "宇宙を舞台にした孤独なロボットの旅" --mode prod

# 生成する企画書の枚数を指定（デフォルト: 3）
uv run game-pitch --topic "宇宙を舞台にした孤独なロボットの旅" --num-pitches 5

# 設定ファイルを指定
uv run game-pitch --topic "..." --config path/to/config.yaml
```

### オプション一覧

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `--topic` | ゲームアイデアのトピック（必須） | - |
| `--mode` | 実行モード `test` / `prod` | `config.yaml` の設定値 |
| `--num-pitches` | 生成する企画書の枚数 | `config.yaml` の設定値（3） |
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
│   │   └── image_prompt.py   # 画像プロンプト生成エージェント
│   ├── schemas/
│   │   └── models.py         # Pydantic スキーマ定義
│   ├── tools/
│   │   ├── web_search.py     # DuckDuckGo 検索ツール
│   │   └── image_gen.py      # Gemini 画像生成ツール
│   ├── config.py             # 設定ローダー
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
| `python-dotenv` | `.env` ファイルの読み込み |

## 更新履歴

| バージョン | 日付 | 内容 |
|-----------|------|------|
| 0.1.0 | 2026-02-27 | 初回実装 ([Steering](Docs/Steering/progress_20260227.md)) |
