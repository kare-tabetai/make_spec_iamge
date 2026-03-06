# Fix: PPTX→PDF変換の日本語パス問題

## 日付
2026-03-06

## 概要
LibreOffice headlessモードが日本語（非ASCII）パスを処理できず、PPTX→PDF変換が静かに失敗する問題を修正。

## 根本原因
- `libreoffice --headless --convert-to pdf` に日本語パスを渡すと `Error: source file could not be loaded` で失敗
- exit code は 0 を返すため、コード側のエラーチェック（returncode != 0）をすり抜ける
- 結果、PDF未生成のまま `WARNING` ログのみで静かに失敗

## 修正内容

### 対象ファイル
- `src/game_pitch_agent/tools/pptx_convert.py`

### 修正1: 一時ディレクトリ経由で変換
`convert_pptx_to_pdf()` で、PPTXファイルをASCII-onlyの一時ディレクトリにコピーしてからLibreOfficeで変換し、生成されたPDFを元のディレクトリに移動するように変更。

### 修正2: stderrのエラーチェック強化
returncode == 0 でも stderr に `Error:` が含まれる場合をログに記録。

## 検証結果
- 日本語パス `/tmp/テスト出力_xxx/テスト企画.pptx` → PDF変換成功
