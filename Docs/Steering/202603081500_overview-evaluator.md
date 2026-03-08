# 俯瞰評価エージェント（Overview Evaluator）

## 目的
- 全pitchを俯瞰して比較評価する `OverviewEvaluatorAgent` を新設
- 個別の16軸評価に加えて、pitch間の多様性・推薦順位・全体コメントを提供
- `overview_evaluation.json` として出力ディレクトリ直下に保存

## 作業内容
- `OverviewEvaluatorAgent`（LlmAgent）を新規作成
- axis_averages はPython側で算出（LLMに計算させない）
- diversity_scores（7カテゴリ）、pitch_rankings、summary はLLMが生成
- `_run_evaluate_on_dir()` の末尾で自動実行（pitch 2件以上の場合）
- `--no-overview` フラグで俯瞰評価のみスキップ可能
- generate / full / evaluate 全コマンドで利用可能

## 変更ファイル一覧
- `src/game_pitch_agent/agents/overview_evaluator.py` （新規）
- `src/game_pitch_agent/agents/__init__.py` （エクスポート追加）
- `src/game_pitch_agent/schemas/models.py` （DiversityScores, PitchRanking, OverviewEvaluation 追加）
- `src/game_pitch_agent/pipeline.py` （run_overview_evaluation() 追加）
- `src/game_pitch_agent/main.py` （統合 + --no-overview フラグ）
- `README.md` （更新履歴追記、パイプライン図更新）

## 結果
- 全コマンドで俯瞰評価が自動実行される
- `overview_evaluation.json` に多様性スコア・ランキング・総合コメントが出力される
- `--no-overview` でスキップ可能

## 残課題
- なし
