# Steering: 現状の問題点修正 (2026-02-28)

## タスク概要

`output/20260228_051044` の実行結果分析から特定した3つの品質問題を修正。
実装計画: `Docs/現状の問題点.md` 参照。

## 問題と対応

### 問題1: 多様性の不足（P0）→ evaluation.py 修正

**根本原因**: EvaluationAgent が単純な合計スコア順位で選定し、斬新さ9.5のアイデアが合計スコアで落選するケースが発生。

**対応**: 選定プロセスを3ステップに段階化。
- Step1: 各アイデアのコア体験を4軸（操作感/感情目標/プレイスタイル/時間スケール）で分類
- Step2: 最も異なる軸の組み合わせを優先選定
- Step3: タイブレイクのみ重み付きスコア使用（斬新さ×0.4 + 明確さ×0.2 + 面白さ×0.2 + 実現可能性×0.2）

**変更ファイル**: `src/game_pitch_agent/agents/evaluation.py`

### 問題2: ペラ1ビジュアルの画一性（P1）→ image_prompt.py 修正

**根本原因**: 全企画書に「左ビジュアル：右テキスト = 50:50」の固定レイアウトを適用。

**対応**:
- レイアウトを4種類提示（HORIZONTAL_SPLIT / VERTICAL_STACK / FULL_OVERLAY / TRIPTYCH）し、AIが自由選択
- アートスタイルも参考例を提示するだけで縛らない
- テキスト量を最小限（キーワード・短いフレーズのみ）に明示

**変更ファイル**: `src/game_pitch_agent/agents/image_prompt.py`

### 問題3: コアアイデアの革新性不足（P2）→ brainstorm.py + core_idea.py + models.py 修正

**根本原因**: BrainstormAgent/CoreIdeaAgent のプロンプトが既存ゲームの延長線上を許容しやすい。

**対応**:
- BrainstormAgent: 革新性チェックリスト追加、20個中6個（約30%）を「常識を覆すアイデア」に指定
- CoreIdeaAgent: innovation_score（1-10）の自己評価フィールド追加、6個中2個（約33%）を実験的アイデアに指定
- models.py: BrainstormIdea に `is_convention_breaking` フィールド追加、CoreGameIdea に `innovation_score` フィールド追加、IdeaScore に `weighted_score` と `core_experience_axes` フィールド追加

**変更ファイル**: `src/game_pitch_agent/agents/brainstorm.py`, `src/game_pitch_agent/agents/core_idea.py`, `src/game_pitch_agent/schemas/models.py`

## 変更一覧

| ファイル | 変更種別 |
|---------|---------|
| `src/game_pitch_agent/agents/evaluation.py` | プロンプト修正（段階的選定・重み付けスコア） |
| `src/game_pitch_agent/agents/image_prompt.py` | プロンプト修正（レイアウト・スタイル自由化） |
| `src/game_pitch_agent/agents/brainstorm.py` | プロンプト修正（革新性チェック・30%適用） |
| `src/game_pitch_agent/agents/core_idea.py` | プロンプト修正（自己評価・33%実験的指示） |
| `src/game_pitch_agent/schemas/models.py` | スキーマ修正（複数フィールド追加） |
| `README.md` | 更新履歴追記 |

## 検証ポイント

- EvaluationAgent の `selection_rationale` に Step1〜3 の思考が含まれるか
- 各アイデアの `core_experience_axes` が異なる分類になっているか
- 画像プロンプトのレイアウトが企画書間で多様か
- `innovation_score` が core_ideas_output.json に記録されているか
- ブレインストーミングの `is_convention_breaking: true` が約6個含まれるか
