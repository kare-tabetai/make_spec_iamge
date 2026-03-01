# タスク: アーキテクチャドキュメント更新

**日時**: 2026-03-01
**ブランチ**: update/agent-architecture-doc

## 概要

`Docs/agent_architecture.md` を現在のアーキテクチャ（v0.2.0相当）に合わせて全面更新。
`Claude_PJ.md` にアーキテクチャ変更時のドキュメント更新ルールを追記。

## 変更内容

### agent_architecture.md の主な更新箇所

1. **エージェント構成の更新**: 7エージェント → 12ステップ（7トップレベル + BrainstormPipeline内6サブエージェント）
2. **BrainstormPipeline の新規記載**: ネストされたSequentialAgent構造（ScamperAgent, SixHatsAgent, ReverseAgent, MandalartAgent, ShiritoriAgent, BrainstormMergeAgent）
3. **Session State の更新**: scamper_output, sixhats_output, reverse_output, mandalart_output, shiritori_output の追加
4. **ログファイル構成の更新**: 7ファイル → 12ファイル（ブレスト5手法の個別ログ追加）
5. **ExpansionAgent のスキーマ修正**: target フィールド削除の反映
6. **ImagePrompt のスキーマ修正**: prompt_en → prompt への変更反映
7. **温度制御パターンの追記**: ブレストサブエージェント・CoreIdeaAgent の temperature=1.5 設定
8. **num_pitches_test の追記**: テストモード時の企画書数設定
9. **設計パターンの追加**: ネストされたパイプライン構造、温度制御による創造性の段階管理

### Claude_PJ.md の更新

- `Docs/agent_architecture.md` への参照を追加
- アーキテクチャ変更時にドキュメントを更新するルールを明文化
- 更新対象の変更種別を具体的に列挙

## 完了状態

- [x] agent_architecture.md 更新
- [x] Claude_PJ.md 更新
- [x] Steering ドキュメント作成
