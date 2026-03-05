# Steering: PPTX企画書出力機能の追加

**日付:** 2026-03-05
**バージョン:** 0.4.0

## 概要

python-pptxを使用してPowerPoint形式(.pptx)のペラ1企画書を出力する機能を追加。
既存の画像生成パスはそのまま残し、`--format`オプションで切り替える。

## 動機

- Gemini画像生成AIを使わずに企画書をビジュアル出力したいケースがある
- PPTX形式なら後から手動で編集可能
- GOOGLE_API_KEY不要で動作するため、API制限やコストの心配がない

## 変更内容

### 新規ファイル
- `src/game_pitch_agent/tools/pptx_render.py` — PPTX生成モジュール

### 修正ファイル
- `pyproject.toml` — `python-pptx>=1.0.0` 依存追加、version 0.4.0
- `src/game_pitch_agent/tools/__init__.py` — `render_pitch_pptx` export追加
- `src/game_pitch_agent/main.py` — `--format` オプション追加、PPTX生成パスの分岐
- `README.md` — 使い方・オプション・更新履歴追加
- `Docs/agent_architecture.md` — ツール・出力構造にPPTX追記

### CLI変更

`render` と `full` サブコマンドに `--format {image,pptx}` オプション追加（デフォルト: `image`）。

```bash
# PPTX生成（render）
uv run game-pitch render --dir output/<dir> --format pptx

# PPTX生成（full）
uv run game-pitch full --topic "テスト" --format pptx
```

### PPTXスライドレイアウト

- 16:9 Blankスライド
- 6セクション: コンセプト / コアメカニクス / ゲーム概要 / ゲームサイクル / アートスタイル / USP+実現可能性
- 2カラム配置、日本語フォント（Meiryo）
- 色設計: 濃紺タイトルバー + アクセント青セクションヘッダー

## 検証結果

- `uv sync` — python-pptx 1.0.2 インストール確認
- `render --format pptx` — 正常にPPTX生成
- `--force` — 既存PPTX上書き再生成動作確認
- 既存PPTXありの場合 — スキップ動作確認
- PPTX出力時のMarkdown再生成 — PPTX参照リンク付きで生成確認
