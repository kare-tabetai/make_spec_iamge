# PPTX出力時にPDF/PNGも同時出力

## 日付
2026-03-06

## 概要
PPTX形式で企画書を出力する際に、LibreOffice headless + pdftoppm を使って PDF と PNG も同時に自動生成する機能を追加。

## 変更内容

### 新規ファイル
- `src/game_pitch_agent/tools/pptx_convert.py` - PPTX -> PDF/PNG 変換モジュール
  - `convert_pptx_to_pdf()`: LibreOffice headless で PPTX -> PDF
  - `convert_pdf_to_png()`: pdftoppm で PDF -> PNG（-singlefile、200dpi）
  - `convert_pptx()`: 上記をまとめて実行するファサード

### 変更ファイル
- `.devcontainer/Dockerfile` - `libreoffice-impress`, `fonts-noto-cjk`, `poppler-utils` を追加
- `src/game_pitch_agent/tools/__init__.py` - `convert_pptx` のexport追加
- `src/game_pitch_agent/main.py`
  - `build_markdown()` に `pdf_path`, `png_path` 引数追加
  - `render_pitch_pptx_file()` の戻り値を dict に変更、変換処理を統合
  - `save_pitch_files()` の戻り値に `pdf_path`, `png_path` を追加
  - `_log_summary()` に PDF/PNG パスのログ出力を追加
  - `async_render()` 内の呼び出しを新しい戻り値に対応
- `README.md` - 更新履歴、依存ライブラリ、出力ファイル構成を更新

## 設計方針
- ツール未インストール時は warning ログのみで skip（PPTX自体は生成済み）
- subprocess.run に timeout 設定（LibreOffice: 60秒、pdftoppm: 30秒）
- 例外を投げず None を返す graceful degradation

## 出力ファイル構成（変更後）
```
pitch_1/
  pitch.json
  pitch.md
  pitch.pptx
  pitch.pdf        <- NEW
  pitch.png        <- NEW
```

## devcontainer再ビルドが必要
Dockerfileにパッケージを追加したため、devcontainerの再ビルドが必要。
