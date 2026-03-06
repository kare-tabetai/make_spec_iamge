# タスク進捗メモ: Research Agent の Google Search + Function Calling 混在問題を修正

## 日時
2026-02-28

## 問題

`uv run game-pitch` 実行時に以下のエラーが発生：

```
ERROR: パイプライン実行エラー: 400 INVALID_ARGUMENT
'Tool use with function calling is unsupported by the model.'
```

### 原因
`WebResearchAgent` が `google_search`（Gemini の Grounding 機能）と
`duckduckgo_search`（通常の Function Calling）を同一エージェントに混在させていた。
Gemini API の制約で、これら2種類のツールを1つのリクエストに混在させることは不可。

```python
# research.py:52 ← 問題箇所
tools=[google_search, duckduckgo_search],  # NG: 混在
```

## 修正方針

1つの `WebResearchAgent` を2つの逐次エージェントに分割：

```
[GoogleResearchAgent]     → google_search のみ → google_research_output
[DuckDuckGoResearchAgent] → duckduckgo_search のみ → research_output (統合)
[BrainstormAgent]
...
```

## 変更ファイル

1. `src/game_pitch_agent/agents/research.py` - 2つの関数に分割
2. `src/game_pitch_agent/agents/__init__.py` - 新しい関数をエクスポート
3. `src/game_pitch_agent/pipeline.py` - エージェントリストとログを7ステップに更新

## 進捗

- [x] Steeringファイル作成
- [x] research.py を分割（create_google_research_agent / create_ddg_research_agent）
- [x] agents/__init__.py を更新
- [x] pipeline.py を更新（7ステップ構成）
- [x] research.py: 「リサーチ専任」「JSONのみ出力」指示を強化
- [x] core_idea.py: 出力JSONキーを明示（ideas + diversity_notesのみ）
- [x] pipeline.py: extract_json_from_state を raw_decode で堅牢化
- [x] pipeline.py: ユーザーメッセージをトピック提示のみに変更
- [x] 動作確認: 全7エージェント ✓、4件の企画書と画像が生成された
