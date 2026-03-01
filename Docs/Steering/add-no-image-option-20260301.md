# タスク: `--no-image` CLIオプションの追加

## 日付
2026-03-01

## 概要
画像生成をスキップする `--no-image` フラグを追加。マークダウン企画書のみ必要な場合に画像生成（ImagePromptAgent + Gemini画像API）をスキップし、時間とAPIコストを節約できるようにした。

## 変更ファイル

### `src/game_pitch_agent/pipeline.py`
- `run_pipeline()` に `skip_image: bool = False` パラメータを追加
- `skip_image=True` の場合、`create_image_prompt_agent` をエージェントリストから除外
- `agent_logs` からも Step 12 (image_prompt) を除外

### `src/game_pitch_agent/main.py`
- argparse に `--no-image` フラグを追加（`action="store_true"`）
- `save_pitch_files()` に `skip_image: bool = False` パラメータを追加
- `skip_image=True` の場合、画像生成ブロック全体をスキップしログ出力
- `async_main()` から `run_pipeline()` と `save_pitch_files()` に `skip_image` を伝搬
- 起動ログに画像生成の有効/スキップ状態を表示
- `request_info.json` に `skip_image` フィールドを追加
- epilog の使用例に `--no-image` の例を追加

### `README.md`
- 使用例セクションに `--no-image` の例を追加
- オプション一覧テーブルに `--no-image` を追記
- 更新履歴に本変更を記録

## 動作
- `--no-image` なし: 従来通り全12ステップ実行（画像生成あり）
- `--no-image` あり: Step 1-11 のみ実行、ImagePromptAgent スキップ、画像ファイル生成なし、Markdown/JSON は正常出力
