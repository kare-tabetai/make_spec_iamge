# デフォルト評価実行

## 目的
- 企画書生成時（generate / full）にデフォルトで16軸評価を実行する
- `--no-evaluate` で無効化可能にする

## 作業内容
- `gen_parser` に `--no-evaluate` 引数を追加
- `async_generate()` 末尾に評価実行ロジックを追加
- `full_parser` の `--evaluate` を `--no-evaluate` に反転
- `async_full()` の評価実行条件を反転
- epilog の使用例を更新
- README.md を更新

## 変更ファイル一覧
- src/game_pitch_agent/main.py
- README.md

## 結果
- generate/full コマンドでデフォルトで16軸評価が実行される
- `--no-evaluate` フラグで評価をスキップ可能
- evaluate サブコマンドは変更なし
- ヘルプ出力で --no-evaluate が正しく表示されることを確認済み

## 残課題
- なし
