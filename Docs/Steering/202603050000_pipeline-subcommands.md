# パイプライン分離: generate / render / full サブコマンド

**日付**: 2026-03-05
**バージョン**: 0.3.0

## 背景

従来の `game-pitch` CLIは単一コマンドでテキスト生成（Steps 1-11）と画像生成（Step 12 + Gemini API）を一括実行していた。ユーザーから「マークダウン企画書の生成」と「画像によるペラ1企画書化」を分離して個別に呼び出せるようにしたいという要望があった。

## 変更内容

### CLIサブコマンド化

| コマンド | 用途 |
|---------|------|
| `game-pitch generate --topic "..."` | Steps 1-11: テキストパイプラインのみ実行 → JSON + Markdown |
| `game-pitch render --dir <出力dir>` | 既存出力に対して ImagePromptAgent + 画像生成 |
| `game-pitch full --topic "..."` | フルパイプライン（従来の動作と同等） |

### 変更ファイル

| ファイル | 変更内容 |
|---------|---------|
| `src/game_pitch_agent/main.py` | サブコマンド構造に書き換え。`render_pitch_image()` 抽出、`async_generate()` / `async_render()` / `async_full()` 追加 |
| `src/game_pitch_agent/pipeline.py` | `run_image_prompt_for_pitch()` 追加（単一企画書へのImagePromptAgent実行） |
| `README.md` | 新CLI使用例に更新、更新履歴追記 |

### 主な設計判断

1. **`render_pitch_image()` の抽出**: `save_pitch_files()` 内の画像生成ロジックを独立関数化し、`render` コマンドから再利用可能にした
2. **`run_image_prompt_for_pitch()`**: renderコマンドで `image_prompt` が無い場合に、単体でImagePromptAgentを実行する関数を追加
3. **`_load_config_for_render()`**: renderコマンド用に `request_info.json` から元の設定を読み込み、CLI引数で上書きするヘルパー
4. **レガシーモード廃止**: サブコマンドなしの呼び出しは廃止（`required=True`）
5. **`request_info.json` の拡張**: `command` フィールド追加、`render_history` で render 実行履歴を記録

## メリット

- テキスト生成のみを高速に繰り返し実行できる（画像APIコスト削減）
- 既存出力に対して後から画像を生成/再生成できる
- 画像生成パラメータ（言語・モデル等）を変えて再レンダリングできる
- `--force` で既存画像の上書き再生成が可能
