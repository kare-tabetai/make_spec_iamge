# CLAUDE_PJ.md

## プロジェクトの目的

このプロジェクトの目的は、AIを用いて高品質なゲームの企画書を作成することです。
質も重要ですが企画アイデアの多様性も重視します。同じ条件で大量に生成してもできるだけかぶりが少ないようにします。

## プロジェクトの情報

- Docs/spec.mdが初期仕様書です
- README.mdにこのプロジェクトの使い方があります
- Docs/agent_architecture.mdがシステムアーキテクチャのドキュメントです

## アーキテクチャドキュメントの更新ルール

エージェントパイプラインのアーキテクチャを変更した場合は、必ず `Docs/agent_architecture.md` も同時に更新してください。
以下のいずれかに該当する変更を行った場合が対象です:

- エージェントの追加・削除・順序変更
- Session State のキーの追加・削除・名称変更
- Pydantic スキーマ（`schemas/models.py`）のフィールド追加・削除・型変更
- パイプラインの構造変更（ネスト構造の変更、SequentialAgent の構成変更など）
- ツールの追加・削除・引数変更
- 設定システム（`config.yaml` / `config.py`）の構造変更
- 出力ディレクトリ構造やログファイルの変更
- 温度設定やモデル設定の変更

更新時は、変更箇所だけでなく関連するセクション（データフロー図、Session State一覧、スキーマ一覧など）も整合性を確認して更新してください。

## 評価軸ドキュメントの同期ルール

`src/game_pitch_agent/agents/pitch_evaluator.py` の各評価インストラクション（`INNOVATION_EVAL_INSTRUCTION`, `COHERENCE_EVAL_INSTRUCTION`, `PLAYABILITY_EVAL_INSTRUCTION`, `PRESENTATION_EVAL_INSTRUCTION`, `EVAL_MERGE_INSTRUCTION`）内の評価軸を変更した場合は、必ず `Docs/evaluation-axes.md` も同時に更新してください。
以下のいずれかに該当する変更を行った場合が対象です:

- 評価軸の追加・削除・名称変更
- 採点基準（10点・5点・1点）の変更
- 採点ルール（刻み、平均目標など）の変更
- 出力フォーマットの変更
- `schemas/models.py` の `PitchEvaluation` クラスのフィールド変更

更新時は、一覧表・詳細基準・出力フォーマット例のすべてを整合性を確認して更新してください。