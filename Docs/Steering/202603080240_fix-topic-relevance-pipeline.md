# トピック不一致問題の改善: エージェントプロンプト修正

## 目的
- 評価分析で判明した `theme_concept_relevance = 1.0`（最低点）問題を解消
- パイプライン全体でトピックが失われていたため、各エージェントにトピック意識を追加

## 作業内容

### 根本原因
- ExpansionAgent が `"topic"` を Session State から読み込む指示を持っていなかった
- 他のエージェント（MergeAgent, CritiqueAgent, EvaluationAgent）もトピックを意識する仕組みがなかった
- `_run_single_agent` のユーザーメッセージが `"続行してください"` のみで、topicが含まれていなかった

### 変更内容（優先度順）

1. **expansion.py (P1: CRITICAL)**: Session State読み込みに `"topic"` 追加、トピック関連性セクション追加
2. **brainstorm.py MergeAgent (P2)**: Session State読み込みに `"topic"` 追加、品質フィルタに「テーマと完全に無関係」条件追加
3. **critique.py (P3)**: Session State読み込みに `"topic"` 追加、5番目の評価軸 `topic_relevance` 追加、overall_scoreを5軸平均に更新
4. **evaluation.py (P4)**: Session State読み込みに `"topic"` 追加、5番目の評価軸「テーマ関連度」追加（重み0.15）
5. **core_idea.py (P5)**: トピック関連性の軽い制約追加
6. **schemas/models.py**: `CritiqueFeedback` と `IdeaScore` に `topic_relevance` フィールド追加
7. **pipeline.py**: `_run_single_agent` のユーザーメッセージにtopicを含めるよう修正

## 変更ファイル一覧
- `src/game_pitch_agent/agents/expansion.py`
- `src/game_pitch_agent/agents/brainstorm.py`
- `src/game_pitch_agent/agents/critique.py`
- `src/game_pitch_agent/agents/evaluation.py`
- `src/game_pitch_agent/agents/core_idea.py`
- `src/game_pitch_agent/schemas/models.py`
- `src/game_pitch_agent/pipeline.py`

## 結果

### theme_concept_relevance スコア比較

| テーマ | 改善前 | 改善後 |
|---|---|---|
| 和風ホラー | 1.0, 1.5 | **9.0, 9.0, 8.5** |
| 宇宙探索サバイバル | 1.0 | **5.0, 4.5, 3.0** |
| 音楽リズムバトル | 1.0 | **8.5, 7.5, 9.0** |

### 改善後の企画書タイトル
- 和風ホラー: 祓魔編集室、神隠しRTA、忌ノ庭
- 宇宙探索サバイバル: Host of the Star-Eater、Terminal Fireworks、Gravity Pinball Express
- 音楽リズムバトル: Zen Sniper: Sonic Camouflage、Groove Letter、Slime BPM Tactics

## 残課題
- 「宇宙探索サバイバル」のテーマ関連度がやや低い（3.0〜5.0）。ブレスト発散フェーズのサブエージェントにも軽い制約を入れることで改善の余地あり
- ただし発散フェーズの自由度を維持するため、現時点では意図的に未修正
