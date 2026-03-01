# 出力フォルダパスのタイムゾーンをJSTに修正

## タスク概要
出力フォルダのパスやログに含まれる日時が `datetime.now()` (タイムゾーン指定なし) で生成されており、コンテナ/WSL2環境のシステムタイムゾーン（UTC）が使われていた問題をJSTに修正。

## 修正内容

### `src/game_pitch_agent/pipeline.py` (3箇所)
1. `from zoneinfo import ZoneInfo` を import に追加
2. L31: `datetime.now()` → `datetime.now(ZoneInfo("Asia/Tokyo"))` (フォルダ名用タイムスタンプ)
3. L229: エージェントログのタイムスタンプをJSTに修正
4. L246: フォールバックログのタイムスタンプをJSTに修正

### `src/game_pitch_agent/main.py` (1箇所)
1. `from zoneinfo import ZoneInfo` を import に追加
2. L181: request_info.json のタイムスタンプをJSTに修正

## 技術的判断
- `zoneinfo` はPython 3.9+の標準ライブラリのため追加依存なし
- 全4箇所を統一的に `ZoneInfo("Asia/Tokyo")` で修正
