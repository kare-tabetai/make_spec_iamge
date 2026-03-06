"""ランダム制約カード - ブレスト段階の多様性を向上させる制約定義"""

import random

# 各カテゴリから1つずつランダムに選ばれ、ブレストエージェントに注入される
GENRE_CONSTRAINTS = [
    "RPGの視点で考えよ",
    "パズルゲームの視点で考えよ",
    "リズムゲームの視点で考えよ",
    "ホラーゲームの視点で考えよ",
    "スポーツゲームの視点で考えよ",
    "シミュレーションの視点で考えよ",
    "ローグライクの視点で考えよ",
    "ビジュアルノベルの視点で考えよ",
    "タワーディフェンスの視点で考えよ",
    "サンドボックスの視点で考えよ",
]

EMOTION_CONSTRAINTS = [
    "「懐かしさ」をコア感情にせよ",
    "「驚き」をコア感情にせよ",
    "「切なさ」をコア感情にせよ",
    "「爽快感」をコア感情にせよ",
    "「恐怖」をコア感情にせよ",
    "「達成感」をコア感情にせよ",
    "「好奇心」をコア感情にせよ",
    "「笑い」をコア感情にせよ",
    "「癒し」をコア感情にせよ",
    "「緊張感」をコア感情にせよ",
]

MECHANIC_CONSTRAINTS = [
    "物理演算を使わないこと",
    "テキスト入力をメインにすること",
    "ワンボタン操作で遊べること",
    "時間制限を中心にすること",
    "協力プレイ前提で考えること",
    "非対称対戦を取り入れること",
    "自動生成されるマップを前提にすること",
    "音声・音楽をメカニクスの中心にすること",
    "デッキ構築要素を入れること",
    "プレイヤーの選択が不可逆であること",
]

TARGET_CONSTRAINTS = [
    "60歳以上の高齢者向け",
    "5歳以下の幼児とその親向け",
    "通勤中の社会人向け（1プレイ3分以内）",
    "ゲーム初心者・普段ゲームをしない人向け",
    "配信者・実況者向け",
    "カップル・友人同士で遊ぶ人向け",
    "競技性を求めるハードコアゲーマー向け",
    "クリエイター・アーティスト向け",
    "教育目的で使いたい教師・保護者向け",
    "長距離移動中の旅行者向け",
]


def generate_constraint_cards(num_agents: int = 5) -> list[dict[str, str]]:
    """各ブレストエージェント用にランダムな制約カードセットを生成する。

    各エージェントには異なるカテゴリの制約が1つずつ割り当てられる。
    同一カテゴリで重複しないよう可能な限り分散させる。

    Args:
        num_agents: ブレストエージェントの数

    Returns:
        各エージェント用の制約辞書のリスト
    """
    # 各カテゴリからnum_agents個をシャッフルして選択（重複なし）
    genres = random.sample(GENRE_CONSTRAINTS, min(num_agents, len(GENRE_CONSTRAINTS)))
    emotions = random.sample(EMOTION_CONSTRAINTS, min(num_agents, len(EMOTION_CONSTRAINTS)))
    mechanics = random.sample(MECHANIC_CONSTRAINTS, min(num_agents, len(MECHANIC_CONSTRAINTS)))
    targets = random.sample(TARGET_CONSTRAINTS, min(num_agents, len(TARGET_CONSTRAINTS)))

    cards = []
    for i in range(num_agents):
        cards.append({
            "genre_constraint": genres[i],
            "emotion_constraint": emotions[i],
            "mechanic_constraint": mechanics[i],
            "target_constraint": targets[i],
        })
    return cards
