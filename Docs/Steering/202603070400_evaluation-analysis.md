# 企画書テスト生成 & 評価分析

## 目的
- 16軸評価システム（v0.9.0）の実効性を検証
- 多様な8テーマで企画書を生成+評価し、評価JSONを横断的に統計分析

## 作業内容

### Step 1: 8テーマでテスト生成+評価
コマンド: `uv run game-pitch full --topic "<テーマ>" --no-image --evaluate`

| # | テーマ | 生成数 | 有効評価数 | 備考 |
|---|--------|--------|-----------|------|
| 1 | お題:「孤独」 | 2 | 1 | pitch_2の評価がスコアなし |
| 2 | 猫カフェ経営シミュレーション | 1 | 1 | |
| 3 | 時間が逆行する世界 | 2 | 2 | |
| 4 | 音だけで遊ぶゲーム | 2 | 1 | pitch_1の評価がスコアなし |
| 5 | 地下迷宮の料理人 | 2 | 2 | |
| 6 | 植物 vs 機械 | 3 | 2 | pitch_3の評価がスコアなし |
| 7 | 100人同時かくれんぼ | 1 | 0 | 評価失敗 |
| 8 | 夢の中の郵便配達 | 2 | 1 | pitch_2の評価がスコアなし |

**合計**: 15件生成 → 10件の有効評価データ（67% 成功率）

### Step 2: バグ修正
- **ExpansionAgent出力パース問題**: LLMが`{"pitches": [...]}`ではなく単一オブジェクトを返すケースがあり、企画書が0件になるバグを修正
  - `_extract_pitches()`ヘルパー関数を追加し、リスト/単一オブジェクト/pitchesキーの3パターンに対応

### Step 3: 分析結果

#### 1. スコア分布（16軸、n=10）

| 軸 | 平均 | 標準偏差 | 最小 | 最大 | 弁別力 |
|----|------|---------|------|------|--------|
| concept_novelty | 4.80 | 1.00 | 3.5 | 6.5 | 良好 |
| core_mechanic_novelty | 4.15 | 1.18 | 3.0 | 6.0 | 良好 |
| mechanic_intuitiveness | 6.60 | 0.62 | 6.0 | 7.5 | やや低い |
| feasibility | 6.70 | 0.90 | 5.0 | 8.0 | 良好 |
| theme_concept_relevance | **7.65** | **0.45** | 7.0 | 8.0 | **低い** |
| theme_art_style_relevance | 6.80 | 0.78 | 5.0 | 8.0 | 普通 |
| design_coherence | 6.00 | 0.63 | 5.0 | 7.0 | やや低い |
| art_style_concept_coherence | 6.50 | 0.71 | 5.0 | 7.5 | 普通 |
| mechanic_art_style_coherence | 5.65 | 0.50 | 5.0 | 6.5 | **低い** |
| first_impression_hook | 5.60 | 0.80 | 4.0 | 7.0 | 良好 |
| elevator_pitch_clarity | 6.10 | 0.77 | 5.0 | 7.5 | 普通 |
| game_cycle_quality | 5.30 | 0.98 | 4.0 | 7.0 | 良好 |
| thematic_mechanic_unity | 5.65 | 1.03 | 4.0 | 7.5 | 良好 |
| game_feel | 4.70 | 0.78 | 3.5 | 6.5 | 普通 |
| risk_reward_depth | 4.45 | 0.93 | 3.0 | 6.0 | 良好 |
| overall_fun | 5.10 | 0.73 | 4.5 | 6.5 | 普通 |

- **全体平均**: 5.73（理想の5.0よりやや高め → 軽度のインフレ傾向）
- **平均標準偏差**: 0.80（弁別力としてはまずまず）

#### 2. 軸間相関（高相関ペア、r > 0.85）

| 軸1 | 軸2 | 相関係数 r | 解釈 |
|-----|-----|-----------|------|
| elevator_pitch_clarity | overall_fun | 0.912 | ピッチが明快な企画は面白い ← 妥当 |
| thematic_mechanic_unity | overall_fun | 0.909 | テーマとメカの一致が面白さに直結 ← 妥当 |
| mechanic_intuitiveness | mechanic_art_style_coherence | 0.908 | **冗長性の疑い** |
| core_mechanic_novelty | elevator_pitch_clarity | 0.890 | メカが新しいとピッチも際立つ ← 妥当 |
| core_mechanic_novelty | overall_fun | 0.873 | 新しいメカ → 面白い ← 妥当 |
| elevator_pitch_clarity | thematic_mechanic_unity | 0.869 | ピッチ明快とテーマ統一は関連 ← やや冗長 |
| concept_novelty | core_mechanic_novelty | 0.865 | **冗長性の疑い**：コンセプト新規性とメカ新規性 |

#### 3. テーマ別傾向の問題点

**重大な問題: テーマと企画内容の乖離**

| テーマ | 生成された企画タイトル |
|--------|----------------------|
| 猫カフェ経営シミュレーション | **Echoes of the Void** |
| 時間が逆行する世界 | **星屑の海賊団**, **星屑の錬金術師** |
| 音だけで遊ぶゲーム | **星屑の航海士** |
| 地下迷宮の料理人 | **星屑のキッチン**, **星屑の錬金術師** |
| 植物 vs 機械 | **星屑の調理師**, **猫と紡ぐ、夢の図書館** |

→ テーマに関係なく「星屑の○○」パターンが多発。Expansion Agentがテーマを無視して汎用的な企画を生成している可能性が高い。

#### 4. 弁別力分析

- **弁別力が低い軸**（σ < 0.50）:
  - `theme_concept_relevance`（σ=0.45）: ほぼ全件7.0-8.0で収束 → テーマと無関係な企画でも高スコアが付く矛盾
  - `mechanic_art_style_coherence`（σ=0.50）: 変動幅が小さい

- **弁別力が良好な軸**（σ > 0.90）:
  - `core_mechanic_novelty`（σ=1.18）
  - `concept_novelty`（σ=1.00）
  - `game_cycle_quality`（σ=0.98）
  - `thematic_mechanic_unity`（σ=1.03）
  - `risk_reward_depth`（σ=0.93）
  - `feasibility`（σ=0.90）

#### 5. 全体傾向

- **スコアインフレ**: 平均5.73で理想の5.0よりやや高め。特に`theme_concept_relevance`(7.65), `feasibility`(6.70), `mechanic_intuitiveness`(6.60)が高い
- **デフレ傾向の軸**: `core_mechanic_novelty`(4.15), `risk_reward_depth`(4.45), `game_feel`(4.70) → これらは厳しめに採点されている

#### 6. 総合評価と改善提案

##### 評価システムの有効性
- **16軸体制は概ね有効**だが、いくつかの構造的問題がある
- overall_funとの相関が高い軸が多く、独立した評価軸として機能していないものがある

##### 改善提案

1. **評価の信頼性問題（最優先）**
   - 5/15件（33%）で評価がスコアなしで失敗 → **PitchEvaluatorAgentのプロンプト/出力パースの堅牢化が必要**

2. **企画生成品質の問題（最優先）**
   - テーマと企画内容の乖離が深刻（「星屑の○○」パターン）
   - ExpansionAgentのプロンプトにテーマへの忠実度を強制する仕組みが必要

3. **軸の統合候補**
   - `mechanic_intuitiveness` と `mechanic_art_style_coherence` → 高相関(r=0.908)、統合検討
   - `concept_novelty` と `core_mechanic_novelty` → 高相関(r=0.865)、統合検討

4. **弁別力の改善**
   - `theme_concept_relevance` → ほぼ全件7.0以上で意味なし。評価基準をより厳格に
   - 評価プロンプトに「平均5.0を目指すこと」「7以上は特筆すべき優れた点がある場合のみ」等の指示追加

5. **相関の整理**
   - `art_style_concept_coherence` と `design_coherence` の高相関(r=0.783) → 役割の明確化

## 変更ファイル一覧
- `/workspace/src/game_pitch_agent/main.py` - `_extract_pitches()`関数追加、pitches抽出のフォールバック処理
- `/workspace/scripts/analyze_evaluations.py` - 評価分析スクリプト（新規作成）
- `/workspace/Docs/Steering/202603070400_evaluation-analysis.md` - 本ファイル

## 残課題

### 高優先度
1. **PitchEvaluatorAgentの出力パース堅牢化**: 33%の失敗率は実用に堪えない
2. **ExpansionAgentのテーマ忠実度**: テーマと無関係な企画が多発している（「星屑の○○」パターン）
3. **テスト生成枚数の不安定さ**: 2件指定だが1件や3件になるケースあり

### 中優先度
4. 軸間相関の高い軸の統合検討
5. 弁別力の低い軸（`theme_concept_relevance`）の評価基準厳格化
6. スコアインフレ対策（プロンプトへの制約追加）

### 低優先度
7. サンプルサイズを増やしての再検証（現在n=10で統計的に心もとない）
8. 評価の再現性テスト（同じ企画を複数回評価してブレを確認）
