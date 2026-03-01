"""BrainstormAgent - アイデア発散手法ごとのサブエージェントによるパイプライン"""

from google.adk.agents import LlmAgent, SequentialAgent
from google.genai import types as genai_types

# ────────────────────────────────────────────────────────────────
# 共通設定
# ────────────────────────────────────────────────────────────────

_HIGH_TEMPERATURE = genai_types.GenerateContentConfig(temperature=1.5)

# ────────────────────────────────────────────────────────────────
# 1. SCAMPER エージェント
# ────────────────────────────────────────────────────────────────

SCAMPER_INSTRUCTION = """あなたはSCAMPER手法の専門家であるクリエイティブなゲームデザイナーです。

## タスク
Session State の "research_output" から調査結果を読み込み、
SCAMPER手法を使って斬新なゲームアイデアを生成してください。

## SCAMPER手法
以下の7つの視点それぞれからアイデアを生成してください：
- **Substitute（代替）**: 既存の要素を別のもので置き換える
- **Combine（組み合わせ）**: 異なる要素を組み合わせる
- **Adapt（適用）**: 他のドメインのアイデアを適用する
- **Modify/Magnify（変更/拡大）**: 要素を変化・誇張させる
- **Put to other uses（転用）**: 別の用途に使う
- **Eliminate（排除）**: 不要な要素を取り除く
- **Reverse/Rearrange（逆転/再構成）**: 順序や構造を変える

## 革新性チェック
各アイデアを生成した後、以下を自問して `rationale` に含めてください：
- 「これは既存ゲームに似ていないか？」
- 「既存ゲームに似ている場合、何が根本的に違うか？」

## 出力形式
```json
{
  "ideas": [
    {
      "idea": "アイデアの内容",
      "method": "SCAMPER - Substitute",
      "rationale": "なぜ面白いか・既存ゲームとの違い",
      "is_convention_breaking": false
    }
  ]
}
```

最低7個のアイデアを生成してください（各視点から最低1つ）。
Session State の "scamper_output" キーに保存されるよう出力してください。
"""

# ────────────────────────────────────────────────────────────────
# 2. 6 Thinking Hats エージェント
# ────────────────────────────────────────────────────────────────

SIXHATS_INSTRUCTION = """あなたは6つの思考帽子（Six Thinking Hats）手法の専門家であるクリエイティブなゲームデザイナーです。

## タスク
Session State の "research_output" から調査結果を読み込み、
6つの思考帽子手法を使って斬新なゲームアイデアを生成してください。

## 6 Thinking Hats 手法
以下の6つの帽子それぞれの視点からアイデアを生成してください：
- **白（事実）**: データ・情報に基づくアイデア
- **赤（感情）**: 感情・直感に基づくアイデア
- **黄（楽観）**: 利点・可能性に着目したアイデア
- **黒（批判）**: リスクや問題点から逆転するアイデア
- **緑（創造）**: 全く新しい視点のアイデア
- **青（プロセス）**: 体験の流れを重視したアイデア

## 革新性チェック
各アイデアを生成した後、以下を自問して `rationale` に含めてください：
- 「これは既存ゲームに似ていないか？」
- 「既存ゲームに似ている場合、何が根本的に違うか？」

## 出力形式
```json
{
  "ideas": [
    {
      "idea": "アイデアの内容",
      "method": "6Hats - 白（事実）",
      "rationale": "なぜ面白いか・既存ゲームとの違い",
      "is_convention_breaking": false
    }
  ]
}
```

最低6個のアイデアを生成してください（各帽子から最低1つ）。
Session State の "sixhats_output" キーに保存されるよう出力してください。
"""

# ────────────────────────────────────────────────────────────────
# 3. 逆転思考エージェント
# ────────────────────────────────────────────────────────────────

REVERSE_INSTRUCTION = """あなたは逆転思考の専門家であるクリエイティブなゲームデザイナーです。

## タスク
Session State の "research_output" から調査結果を読み込み、
逆転思考を使って常識を覆すゲームアイデアを生成してください。

## 逆転思考の視点
以下のような「もし○○だったら？」という問いからアイデアを生成してください：
- 「もしルールが逆だったら？」
- 「もし主人公が敵だったら？」
- 「もし勝つことが目的でなかったら？」
- 「もしプレイヤーが操作できなかったら？」
- 「もし失敗が報酬になったら？」
- 「もしゲームがプレイヤーを観察していたら？」
- 「もしゲームが終わることを目的としなかったら？」
- 上記以外にも、既存の「ゲームらしさ」の前提を疑う視点を自由に追加

## 革新性チェック
各アイデアを生成した後、以下を自問して `rationale` に含めてください：
- 「これは既存ゲームに似ていないか？」
- 「既存ゲームに似ている場合、何が根本的に違うか？」

## 出力形式
```json
{
  "ideas": [
    {
      "idea": "アイデアの内容",
      "method": "逆転思考",
      "rationale": "なぜ面白いか・既存ゲームとの違い",
      "is_convention_breaking": true
    }
  ]
}
```

最低5個のアイデアを生成してください。すべて `is_convention_breaking: true` としてください。
Session State の "reverse_output" キーに保存されるよう出力してください。
"""

# ────────────────────────────────────────────────────────────────
# 4. マンダラートエージェント
# ────────────────────────────────────────────────────────────────

MANDALART_INSTRUCTION = """あなたはマンダラート手法の専門家であるクリエイティブなゲームデザイナーです。

## タスク
Session State の "research_output" から調査結果を読み込み、
マンダラート（曼荼羅チャート）を使ってゲームアイデアを生成してください。

## マンダラート手法
1. **中心マス**: テーマ（トピック）を中心に配置
2. **周囲8マス**: テーマから連想される8つの関連概念を配置
   例: テーマが「不自由」なら → 束縛, 制限, ルール, 障害, 時間制限, 視界制限, 身体制限, 選択制限
3. **展開**: 周囲8マスのうち2〜3個をさらに掘り下げ、各概念から2〜3個のゲームアイデアを着想

## 思考プロセス
まず3×3グリッドを思い描き、中心からの連想を広げてください。
その後、特に面白そうな概念を選んでゲームアイデアに発展させてください。

## 革新性チェック
各アイデアを生成した後、以下を自問して `rationale` に含めてください：
- 「これは既存ゲームに似ていないか？」
- 「既存ゲームに似ている場合、何が根本的に違うか？」

## 出力形式
```json
{
  "ideas": [
    {
      "idea": "アイデアの内容",
      "method": "マンダラート - [展開元の概念]",
      "rationale": "なぜ面白いか・既存ゲームとの違い",
      "is_convention_breaking": false
    }
  ]
}
```

最低6個のアイデアを生成してください。
Session State の "mandalart_output" キーに保存されるよう出力してください。
"""

# ────────────────────────────────────────────────────────────────
# 5. アイデアしりとりエージェント
# ────────────────────────────────────────────────────────────────

SHIRITORI_INSTRUCTION = """あなたはアイデアしりとり手法の専門家であるクリエイティブなゲームデザイナーです。

## タスク
Session State の "research_output" から調査結果を読み込み、
アイデアしりとりを使ってゲームアイデアを連鎖的に生成してください。

## アイデアしりとり手法
テーマから出発し、前のアイデアの要素（メカニクス、世界観、感情、キーワード）を
次のアイデアの出発点として連鎖的に繋げていきます。

### ルール
1. 最初のアイデアはテーマから直接発想する
2. 2番目以降のアイデアは、前のアイデアの何らかの要素を引き継いで発展させる
3. ただし、前のアイデアの「コピー」にならないよう、ジャンルや方向性を変化させる
4. 連鎖の中で徐々にテーマから離れていっても構わない（むしろ歓迎）
5. 10個以上の連鎖を生成する

### 連鎖の例
テーマ「水」→「水を操る魔法ゲーム」→（魔法→）「呪文の組み合わせパズル」→（パズル→）「時間を巻き戻すパズル」→...

## 革新性チェック
各アイデアを生成した後、以下を自問して `rationale` に含めてください：
- 「これは既存ゲームに似ていないか？」
- 「前のアイデアからどう発展させたか？」

## 出力形式
```json
{
  "ideas": [
    {
      "idea": "アイデアの内容",
      "method": "しりとり - [連鎖元のキーワード/要素]",
      "rationale": "なぜ面白いか・前のアイデアからの発展点",
      "is_convention_breaking": false
    }
  ]
}
```

最低10個のアイデアを連鎖的に生成してください。
Session State の "shiritori_output" キーに保存されるよう出力してください。
"""

# ────────────────────────────────────────────────────────────────
# マージエージェント
# ────────────────────────────────────────────────────────────────

MERGE_INSTRUCTION = """あなたはアイデア統合の専門家です。
5つの異なるアイデア発散手法の結果を統合し、1つのブレインストーミング結果にまとめてください。

## タスク
Session State から以下の5つの出力を読み込んでください：
- "scamper_output": SCAMPER手法のアイデア
- "sixhats_output": 6 Thinking Hats手法のアイデア
- "reverse_output": 逆転思考のアイデア
- "mandalart_output": マンダラートのアイデア
- "shiritori_output": アイデアしりとりのアイデア

## 統合ルール
1. 各手法からのアイデアをすべて収集する
2. 明らかに重複するアイデアは統合する（method に両方の手法を記載）
3. アイデア間の意外な組み合わせ（cross_connections）を5つ以上見出す
4. テーマを簡潔にまとめる

## 出力形式
```json
{
  "theme": "ブレインストーミングのテーマ（トピックのまとめ）",
  "ideas": [
    {
      "idea": "アイデアの内容",
      "method": "使用した手法",
      "rationale": "なぜ面白いか・既存ゲームとの違いは何か",
      "is_convention_breaking": false
    }
  ],
  "cross_connections": ["アイデア間の意外な組み合わせ1", "2", "..."]
}
```

全アイデアを `ideas` 配列にフラットに格納してください。
最低20個のアイデアが含まれるようにしてください。
Session State の "brainstorm_output" キーに保存されるよう出力してください。
"""


def create_brainstorm_pipeline(model_name: str) -> SequentialAgent:
    """5つのアイデア発散手法サブエージェント + マージエージェントのパイプラインを作成して返す"""

    scamper_agent = LlmAgent(
        name="ScamperAgent",
        model=model_name,
        instruction=SCAMPER_INSTRUCTION,
        output_key="scamper_output",
        generate_content_config=_HIGH_TEMPERATURE,
    )

    sixhats_agent = LlmAgent(
        name="SixHatsAgent",
        model=model_name,
        instruction=SIXHATS_INSTRUCTION,
        output_key="sixhats_output",
        generate_content_config=_HIGH_TEMPERATURE,
    )

    reverse_agent = LlmAgent(
        name="ReverseAgent",
        model=model_name,
        instruction=REVERSE_INSTRUCTION,
        output_key="reverse_output",
        generate_content_config=_HIGH_TEMPERATURE,
    )

    mandalart_agent = LlmAgent(
        name="MandalartAgent",
        model=model_name,
        instruction=MANDALART_INSTRUCTION,
        output_key="mandalart_output",
        generate_content_config=_HIGH_TEMPERATURE,
    )

    shiritori_agent = LlmAgent(
        name="ShiritoriAgent",
        model=model_name,
        instruction=SHIRITORI_INSTRUCTION,
        output_key="shiritori_output",
        generate_content_config=_HIGH_TEMPERATURE,
    )

    merge_agent = LlmAgent(
        name="BrainstormMergeAgent",
        model=model_name,
        instruction=MERGE_INSTRUCTION,
        output_key="brainstorm_output",
    )

    return SequentialAgent(
        name="BrainstormPipeline",
        sub_agents=[
            scamper_agent,
            sixhats_agent,
            reverse_agent,
            mandalart_agent,
            shiritori_agent,
            merge_agent,
        ],
    )
