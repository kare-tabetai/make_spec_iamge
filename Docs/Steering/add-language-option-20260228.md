# 企画書画像の言語設定機能追加

## 日付
2026-02-28

## 背景・課題
ImagePromptAgent の INSTRUCTION に「英語で記述」が固定されており、生成される画像内テキスト（タイトル・キャッチコピー等）が常に英語になっていた。

## 変更内容

### 変更ファイル（5件）

| ファイル | 変更内容 |
|---------|---------|
| `config.yaml` | `generation.language: ja` を追加 |
| `src/game_pitch_agent/config.py` | `GenerationConfig.language` フィールド追加、`load_config` に `language_override` 引数追加 |
| `src/game_pitch_agent/agents/image_prompt.py` | `IMAGE_PROMPT_INSTRUCTION_JA` / `IMAGE_PROMPT_INSTRUCTION_EN` を定義、`create_image_prompt_agent(language)` 引数追加 |
| `src/game_pitch_agent/pipeline.py` | `create_image_prompt_agent` 呼び出しに `language=config.generation.language` を渡す |
| `src/game_pitch_agent/main.py` | `--language {ja,en}` CLI引数追加、起動ログに言語情報追加 |

### 設計方針
- スキーマ（`schemas/models.py`）は変更しない。`prompt_en` フィールド名はそのまま維持（内部処理のみで使用）
- `config.yaml` のデフォルトを `ja`（日本語）に設定
- `mode_override` と同じパターンで `language_override` を実装

## 使い方

```bash
# デフォルト（日本語）
uv run game-pitch --topic "宇宙を舞台にした孤独なロボットの旅"

# 日本語を明示
uv run game-pitch --topic "..." --language ja

# 英語
uv run game-pitch --topic "..." --language en
```

## 動作確認
- `uv run game-pitch --help` で `--language {ja,en}` オプションが表示されることを確認
- `load_config(language_override='en')` で `config.generation.language == 'en'` になることを確認
