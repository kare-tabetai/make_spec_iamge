# 企画書評価AIエージェントの追加

## 目的
- 生成済みのゲーム企画書（pitch.json）を17軸で自動評価するAIエージェントを追加する
- 評価結果を各ピッチフォルダに `evaluation.json` として保存する
- 既存の `EvaluationAgent`（アイデア選定用）や `CritiqueAgent`（品質改善ループ用）とは独立した、事後評価専用のエージェント

## 作業内容
1. `PitchEvaluation` Pydanticモデル追加（17軸スコア + サマリー）
2. `PitchEvaluatorAgent` 作成（ベテランゲーム批評家の人格設定、厳格な採点基準）
3. `pipeline.py` に `run_pitch_evaluation()` ヘルパー追加
4. `main.py` に `evaluate` サブコマンド追加
5. `full` サブコマンドに `--evaluate` フラグ追加
6. README.md 更新（使い方、オプション一覧、更新履歴、構造図）
7. `Docs/agent_architecture.md` 更新（Agent⑭追加、フロー図更新）

## 変更ファイル一覧
- `src/game_pitch_agent/agents/pitch_evaluator.py` — 新規
- `src/game_pitch_agent/agents/__init__.py` — 修正
- `src/game_pitch_agent/schemas/models.py` — 修正（PitchEvaluation追加）
- `src/game_pitch_agent/pipeline.py` — 修正（run_pitch_evaluation追加）
- `src/game_pitch_agent/main.py` — 修正（evaluate サブコマンド、--evaluate フラグ）
- `README.md` — 修正
- `Docs/agent_architecture.md` — 修正
- `Docs/Steering/202603070320_add-pitch-evaluator.md` — 新規

## 結果
- `evaluate` サブコマンドが正常動作することを確認
- 既存出力ディレクトリに対して評価を実行し、`evaluation.json` が生成されることを確認
- `--force` フラグで上書き再評価が動作することを確認
- 17軸スコアが0〜10の範囲で適切に採点されることを確認
- サマリーログに平均スコアが正しく出力されることを確認

## 残課題
- なし
