# 企画書の面白さ・多様性を向上させる改善

## 目的
- 企画書の「面白さ」と「多様性」を向上させる
- 同一トピックで繰り返し実行しても異なるアイデアが出るようにする
- 企画書を読んだ人が直感的に「面白そう」と感じる要素を追加する

## 作業内容

### Phase 1: プロンプト改善
1. **CoreIdeaAgent**: `cross_connections`（異種手法間の意外な組み合わせ）を明示的に活用する指示を追加
2. **ExpansionAgent**: 高品質な架空の企画書例（Few-shot）をプロンプトに追加し、出力品質の底上げと安定化を実現

### Phase 2: スキーマ拡張（新フィールド5つ）
`ExpandedPitch` に以下のフィールドを追加（すべて `default=""` で後方互換性を維持）:
- `play_scene`: プレイシーン描写（30-50文字の具体的ワンシーン）
- `elevator_pitch`: エレベーターピッチ（[作品A] meets [作品B] 形式）
- `emotional_curve`: 感情曲線（プレイ開始〜1時間の感情変化）
- `target_player`: ターゲットプレイヤー像
- `camera_perspective`: ゲーム視点（2D横スクロール/TPS/FPS等）

### Phase 3: マークダウン出力・PPTX刷新
- `build_markdown()` を全面リフォーマット:
  - 冒頭にタイトル + キャッチコピー + エレベーターピッチを集約
  - プレイシーン描写を冒頭に配置
  - 基本情報をテーブル形式に
  - ゲームサイクルをフローチャート形式に
  - USPをボックス引用で強調
- PPTX: タイトルバーに視点情報追加、新フィールド行を追加

### Phase 4: ランダム制約カード注入
- `constraints.py` を新規作成: ジャンル/感情/メカニクス/ターゲットの4カテゴリ各10種の制約を定義
- パイプライン実行時にランダムな制約カードセットを生成し Session State に注入
- 5つのブレストエージェント（SCAMPER/6Hats/逆転/マンダラート/しりとり）がそれぞれ異なる制約を参照

## 変更ファイル一覧
- `src/game_pitch_agent/agents/core_idea.py` - cross_connections活用プロンプト追加
- `src/game_pitch_agent/agents/expansion.py` - Few-shot例示 + 5フィールド生成指示追加
- `src/game_pitch_agent/agents/brainstorm.py` - 各エージェントに制約カード参照プロンプト追加
- `src/game_pitch_agent/schemas/models.py` - ExpandedPitchに5フィールド追加
- `src/game_pitch_agent/main.py` - build_markdown()全面リフォーマット
- `src/game_pitch_agent/tools/pptx_render.py` - 新フィールド行追加、タイトルバーに視点情報
- `src/game_pitch_agent/pipeline.py` - 制約カード生成・Session State注入
- `src/game_pitch_agent/constraints.py` - 新規: 制約カード定義モジュール
- `README.md` - 更新履歴追加、プロジェクト構造にconstraints.py追記

## 結果
- 全モジュールのインポート・動作確認済み
- build_markdown() の出力が新フォーマットで正常動作
- PPTX生成が新フィールド込みで正常動作
- 制約カード生成が5セット・重複なしで動作確認済み
- 既存フィールドの後方互換性あり（新フィールドはすべてdefault=""）

## 残課題
- 実際のパイプライン実行による品質検証（API呼び出しを伴うため手動確認が必要）
- 制約カードのバリエーション拡充（現状各10種、将来的にはYAML外部化も検討可能）
