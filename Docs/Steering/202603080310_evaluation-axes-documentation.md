# 評価項目ドキュメント作成 & 同期の仕組み

## 目的
- 16評価軸の採点基準をドキュメント化し、評価の透明性を確保する
- 評価軸変更時にドキュメントも追従する仕組みを整備する

## 作業内容
1. `Docs/evaluation-axes.md` を新規作成（16軸の一覧・詳細基準・出力フォーマット例）
2. `CLAUDE_PJ.md` に評価軸変更時のドキュメント同期ルールを追記

## 変更ファイル一覧
- `Docs/evaluation-axes.md` — 新規作成
- `CLAUDE_PJ.md` — 評価軸ドキュメント同期ルールを追記
- `Docs/Steering/202603080310_evaluation-axes-documentation.md` — 本ファイル

## 結果
- 16軸すべての採点基準が `pitch_evaluator.py` と一致していることを確認済み
- `CLAUDE_PJ.md` に同期ルールが追記済み

## 残課題
- なし
