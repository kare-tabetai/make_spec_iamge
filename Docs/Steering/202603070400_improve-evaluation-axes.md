# 企画書評価軸の改善（17軸→16軸）

## 目的
- 冗長な評価軸を削除し、欠落していた観点を追加、一部軸を改善する
- 17軸から16軸へ整理

## 作業内容
### 削除する軸（2軸）
- `concept_uniqueness` — `concept_novelty` とほぼ同義
- `core_mechanic_uniqueness` — `core_mechanic_novelty` とほぼ同義

### 追加する軸（2軸）
- `game_cycle_quality` — ゲームサイクルの質
- `elevator_pitch_clarity` — 一言で伝わる力

### 修正する軸（3軸）
- `hook_strength` → `first_impression_hook`
- `narrative_mechanic_integration` → `thematic_mechanic_unity`
- `theme_core_mechanic_relevance` + `concept_mechanic_coherence` → `design_coherence`（統合）

### 最終16軸
concept_novelty, core_mechanic_novelty, mechanic_intuitiveness, feasibility, theme_concept_relevance, theme_art_style_relevance, design_coherence, art_style_concept_coherence, mechanic_art_style_coherence, first_impression_hook, elevator_pitch_clarity, game_cycle_quality, thematic_mechanic_unity, game_feel, risk_reward_depth, overall_fun

## 変更ファイル一覧
- `src/game_pitch_agent/schemas/models.py`
- `src/game_pitch_agent/agents/pitch_evaluator.py`
- `src/game_pitch_agent/main.py`
- `Docs/agent_architecture.md`
- `README.md`

## 結果
- 16軸での評価が正常に動作することを確認

## 残課題
- なし
