# PitchEvaluatorAgent データフロー修正

## 目的
- evaluation.json のタイトル・トピックが pitch.json と不一致になるハルシネーション問題を修正

## 作業内容
- 根本原因: `run_pitch_evaluation` が新規セッションで実行されるため、Session State の `pitch_data` がLLMの会話コンテキストに含まれずハルシネーション発生
- 修正: ユーザーメッセージにpitchデータとトピックをJSON文字列として直接埋め込み
- プロンプトの参照指示を「Session Stateから読む」→「ユーザーメッセージから読む」に変更
- idea_id / title の正確な転記を明示的に指示追加

## 変更ファイル一覧
- `src/game_pitch_agent/pipeline.py` - メッセージにpitch JSONを埋め込み
- `src/game_pitch_agent/agents/pitch_evaluator.py` - プロンプトの参照指示変更

## 結果
- テスト実行（テーマ: 宇宙探索）で pitch.json と evaluation.json の idea_id / title が完全一致
- 全16軸で有効なスコア（0でない値）を確認

## 残課題
- なし
