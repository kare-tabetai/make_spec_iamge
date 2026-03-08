"""Pydantic スキーマ定義 - エージェント間通信用JSONモデル"""

from typing import Optional
from pydantic import BaseModel, Field


# ────────────────────────────────────────────────────────────────
# WebResearchAgent の出力
# ────────────────────────────────────────────────────────────────

class ResearchItem(BaseModel):
    """調査結果の1件"""
    topic: str = Field(..., description="調査トピック")
    summary: str = Field(..., description="要約内容")
    key_insights: list[str] = Field(default_factory=list, description="重要なインサイト")
    source_hints: list[str] = Field(default_factory=list, description="情報ソースのヒント")


class ResearchOutput(BaseModel):
    """WebResearchAgent の出力"""
    original_topic: str = Field(..., description="元のトピック")
    research_items: list[ResearchItem] = Field(..., description="調査結果リスト")
    market_context: str = Field(..., description="市場・トレンドの文脈")
    related_games: list[str] = Field(default_factory=list, description="関連する既存ゲームタイトル")
    pain_points: list[str] = Field(default_factory=list, description="プレイヤーの不満点・レビュー批判")


# ────────────────────────────────────────────────────────────────
# BrainstormAgent の出力
# ────────────────────────────────────────────────────────────────

class BrainstormIdea(BaseModel):
    """ブレインストーミングの1アイデア"""
    idea: str = Field(..., description="アイデアの内容")
    method: str = Field(..., description="使用したアイデア発散手法 (SCAMPER, 6 Hats など)")
    rationale: str = Field(..., description="なぜこのアイデアが面白いか・既存ゲームとの違い")
    is_convention_breaking: bool = Field(default=False, description="ゲームの常識を覆すアイデアか")


class FilteredIdea(BaseModel):
    """品質フィルタリングで除外されたアイデア"""
    idea: str = Field(..., description="除外されたアイデアの内容")
    method: str = Field(..., description="使用した手法")
    exclusion_reason: str = Field(..., description="除外理由")


class BrainstormOutput(BaseModel):
    """BrainstormAgent の出力"""
    theme: str = Field(..., description="ブレインストーミングのテーマ")
    ideas: list[BrainstormIdea] = Field(..., description="発散したアイデアリスト")
    cross_connections: list[str] = Field(default_factory=list, description="アイデア間の意外な組み合わせ")
    filtered_ideas: list[FilteredIdea] = Field(default_factory=list, description="品質フィルタリングで除外されたアイデア")


class MandalartOutput(BaseModel):
    """マンダラート2段階展開の出力"""
    center_word: str = Field(..., description="中心テーマ")
    stage1_words: list[str] = Field(..., description="1段階目: テーマから連想した8つの関連語")
    stage2_expansions: dict[str, list[str]] = Field(default_factory=dict, description="2段階目: 各関連語から展開した8語")
    all_expanded_words: list[str] = Field(default_factory=list, description="全展開語（最大64語）")
    selected_hints: list[str] = Field(default_factory=list, description="ランダム選出したヒント語（8語）")
    ideas: list[BrainstormIdea] = Field(default_factory=list, description="ヒント語から生成したアイデア")


# ────────────────────────────────────────────────────────────────
# CoreIdeaAgent の出力
# ────────────────────────────────────────────────────────────────

class CoreGameIdea(BaseModel):
    """ゲームの具体的なコアアイデア"""
    id: str = Field(..., description="アイデアID (例: idea_001)")
    title: str = Field(..., description="仮タイトル")
    genre: str = Field(..., description="ゲームジャンル")
    core_experience: str = Field(..., description="コア体験（UX的に何が独自か）")
    target_player: str = Field(..., description="ターゲットプレイヤー像")
    core_mechanic: str = Field(..., description="主要なゲームメカニクス")
    unique_selling_point: str = Field(..., description="差別化ポイント（USP）")
    concept_statement: str = Field(..., description="「誰が・どんな体験・どんな感情」を一文で")
    innovation_score: float = Field(..., ge=1, le=10, description="既存ゲームとの差別化度（AI自己評価 1-10）")


class CoreIdeasOutput(BaseModel):
    """CoreIdeaAgent の出力"""
    ideas: list[CoreGameIdea] = Field(..., description="コアアイデアリスト")
    diversity_notes: str = Field(..., description="多様性を確保するために意識した点")


# ────────────────────────────────────────────────────────────────
# EvaluationAgent の出力
# ────────────────────────────────────────────────────────────────

class CoreExperienceAxes(BaseModel):
    """コア体験の4軸分類"""
    operation: str = Field(..., description="操作感の軸 (アクション/ストラテジー/パズル/物語体験/その他)")
    emotion: str = Field(..., description="感情目標の軸 (達成感/驚き/共感/リラックス/スリル/その他)")
    playstyle: str = Field(..., description="プレイスタイルの軸 (ソロ/協力/競争/観客/その他)")
    timescale: str = Field(..., description="時間スケールの軸 (数分/数時間/継続的/その他)")


class IdeaScore(BaseModel):
    """アイデアの評価スコア"""
    idea_id: str = Field(..., description="評価対象のアイデアID")
    novelty: float = Field(..., ge=0, le=10, description="斬新さ (0-10)")
    clarity: float = Field(..., ge=0, le=10, description="明確さ・わかりやすさ (0-10)")
    fun_factor: float = Field(..., ge=0, le=10, description="ぱっと見て面白そうか (0-10)")
    feasibility: float = Field(..., ge=0, le=10, description="実現可能性 (0-10)")
    topic_relevance: float = Field(..., ge=0, le=10, description="テーマ関連度 (0-10)")
    total_score: float = Field(..., ge=0, le=50, description="合計スコア (0-50)")
    weighted_score: float = Field(..., ge=0, le=10, description="重み付きスコア (斬新さ×0.35+明確さ×0.2+面白さ×0.2+実現可能性×0.1+テーマ関連度×0.15)")
    core_experience_axes: CoreExperienceAxes = Field(..., description="コア体験の4軸分類")
    evaluation_comment: str = Field(..., description="プロのゲームデザイナー視点の評価コメント")
    selected: bool = Field(default=False, description="最終選定されたか")


class EvaluationOutput(BaseModel):
    """EvaluationAgent の出力"""
    scores: list[IdeaScore] = Field(..., description="全アイデアのスコアリスト")
    selected_idea_ids: list[str] = Field(..., description="選定されたアイデアIDリスト")
    selection_rationale: str = Field(..., description="選定理由（多様性の観点を含む）")


# ────────────────────────────────────────────────────────────────
# ExpansionAgent の出力
# ────────────────────────────────────────────────────────────────

class GameCycle(BaseModel):
    """ゲームサイクル（ループ）"""
    trigger: str = Field(default="", description="アクションを起こすきっかけ・動機")
    main_action: str = Field(..., description="メインアクション")
    short_term_reward: str = Field(..., description="短期的な報酬")
    long_term_reward: str = Field(..., description="中長期的な報酬")
    escalation: str = Field(default="", description="繰り返すごとにエスカレートする要素")


class ExpandedPitch(BaseModel):
    """展開されたペラ1企画書の内容"""
    idea_id: str = Field(..., description="元のコアアイデアID")
    title: str = Field(..., description="ゲームタイトル")
    catchcopy: str = Field(..., description="キャッチコピー")
    concept: str = Field(..., description="ゲームコンセプト（目的地・感情）")
    overview: str = Field(..., description="ゲーム概要")
    genre: str = Field(..., description="ジャンル")
    platform: str = Field(..., description="想定プラットフォーム")
    core_mechanic: str = Field(..., description="コアメカニクス（遊びの仕組み）")
    game_cycle: GameCycle = Field(..., description="ゲームサイクル")
    art_style: str = Field(..., description="アートスタイル・ビジュアル方針")
    usp: str = Field(..., description="独自の売り（USP）")
    feasibility_note: str = Field(..., description="実現可能性に関する補足")
    play_scene: str = Field(default="", description="プレイシーン描写（30-50文字の具体的ワンシーン）")
    elevator_pitch: str = Field(default="", description="エレベーターピッチ（[作品A] meets [作品B] 形式）")
    emotional_curve: str = Field(default="", description="感情曲線（プレイ開始〜1時間の感情変化）")
    target_player: str = Field(default="", description="ターゲットプレイヤー像")
    camera_perspective: str = Field(default="", description="ゲーム視点（2D横スクロール/2D見下ろし/TPS/FPS/アイソメトリック等）")


class ExpandedIdeasOutput(BaseModel):
    """ExpansionAgent の出力"""
    pitches: list[ExpandedPitch] = Field(..., description="展開された企画書リスト")


# ────────────────────────────────────────────────────────────────
# ImagePromptAgent の出力
# ────────────────────────────────────────────────────────────────

class ImagePrompt(BaseModel):
    """画像生成プロンプト"""
    idea_id: str = Field(..., description="対応するコアアイデアID")
    title: str = Field(..., description="対応するゲームタイトル")
    prompt: str = Field(..., description="画像生成プロンプト（指示言語に従って記述）")
    layout_description: str = Field(..., description="レイアウトの説明")
    art_style_notes: str = Field(..., description="アートスタイルの補足")


class ImagePromptsOutput(BaseModel):
    """ImagePromptAgent の出力"""
    image_prompts: list[ImagePrompt] = Field(..., description="画像生成プロンプトリスト")


# ────────────────────────────────────────────────────────────────
# 最終出力ドキュメント
# ────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────
# CritiqueAgent の出力
# ────────────────────────────────────────────────────────────────

class CritiqueFeedback(BaseModel):
    """企画書1件に対する批評"""
    idea_id: str = Field(..., description="対象のアイデアID")
    concept_mechanic_alignment: float = Field(..., ge=1, le=10, description="コンセプトとメカニクスの整合性 (1-10)")
    game_cycle_concreteness: float = Field(..., ge=1, le=10, description="ゲームサイクルの具体性 (1-10)")
    catchcopy_originality: float = Field(..., ge=1, le=10, description="キャッチコピーの独自性 (1-10)")
    usp_differentiation: float = Field(..., ge=1, le=10, description="USPの差別化力 (1-10)")
    topic_relevance: float = Field(..., ge=1, le=10, description="トピック関連度 (1-10)")
    overall_score: float = Field(..., ge=1, le=10, description="総合スコア (5軸の平均)")
    feedback: str = Field(..., description="具体的な改善点")


class CritiqueOutput(BaseModel):
    """CritiqueAgent の出力"""
    critiques: list[CritiqueFeedback] = Field(..., description="各企画書への批評リスト")


class PitchEvaluation(BaseModel):
    """企画書の詳細評価結果（事後評価用）"""
    idea_id: str = Field(..., description="アイデアID")
    title: str = Field(..., description="ゲームタイトル")
    topic: str = Field(..., description="評価対象のトピック")
    # 固定16評価軸 (0-10)
    concept_novelty: float = Field(..., ge=0, le=10, description="コンセプトの斬新さ")
    core_mechanic_novelty: float = Field(..., ge=0, le=10, description="コアメカニクスの斬新さ")
    mechanic_intuitiveness: float = Field(..., ge=0, le=10, description="メカニクスが直感的か")
    feasibility: float = Field(..., ge=0, le=10, description="実現可能性")
    theme_concept_relevance: float = Field(..., ge=0, le=10, description="テーマ×コンセプト関連度")
    theme_art_style_relevance: float = Field(..., ge=0, le=10, description="テーマ×アートスタイル関連度")
    design_coherence: float = Field(..., ge=0, le=10, description="設計の一貫性（テーマ・コンセプト・メカニクス）")
    art_style_concept_coherence: float = Field(..., ge=0, le=10, description="アートスタイル×コンセプト整合性")
    mechanic_art_style_coherence: float = Field(..., ge=0, le=10, description="メカニクス×アートスタイル整合性")
    first_impression_hook: float = Field(..., ge=0, le=10, description="第一印象のインパクト")
    elevator_pitch_clarity: float = Field(..., ge=0, le=10, description="一言で伝わる力")
    game_cycle_quality: float = Field(..., ge=0, le=10, description="ゲームサイクルの質")
    thematic_mechanic_unity: float = Field(..., ge=0, le=10, description="テーマとメカニクスの一体感")
    game_feel: float = Field(..., ge=0, le=10, description="手触り・ジュース感")
    risk_reward_depth: float = Field(..., ge=0, le=10, description="リスクとリターン・駆け引きの深み")
    overall_fun: float = Field(..., ge=0, le=10, description="全体の面白さ")
    # 集計
    summary: str = Field(..., description="総合評価コメント")


# ────────────────────────────────────────────────────────────────
# OverviewEvaluation - 俯瞰評価
# ────────────────────────────────────────────────────────────────

class DiversityScores(BaseModel):
    """全pitch間の多様性スコア"""
    concept_diversity: float = Field(..., ge=0, le=10, description="コンセプトの多様性")
    mechanic_diversity: float = Field(..., ge=0, le=10, description="メカニクスの多様性")
    genre_diversity: float = Field(..., ge=0, le=10, description="ジャンルの多様性")
    art_style_diversity: float = Field(..., ge=0, le=10, description="アートスタイルの多様性")
    world_setting_diversity: float = Field(..., ge=0, le=10, description="世界観・設定の多様性")
    target_player_diversity: float = Field(..., ge=0, le=10, description="ターゲット層の多様性")
    overall_diversity: float = Field(..., ge=0, le=10, description="全体的な多様性")


class PitchRanking(BaseModel):
    """推薦順位の1エントリ"""
    rank: int = Field(..., description="順位")
    idea_id: str = Field(..., description="アイデアID")
    title: str = Field(..., description="ゲームタイトル")
    avg_score: float = Field(..., description="16軸評価の平均スコア")
    overall_fun: float = Field(..., description="overall_funスコア")
    strengths: str = Field(..., description="この企画の強み（50文字程度）")


class OverviewEvaluation(BaseModel):
    """全pitchを俯瞰した比較評価"""
    topic: str = Field(..., description="お題名")
    pitch_count: int = Field(..., description="評価対象のpitch数")
    generated_at: str = Field(..., description="生成日時（ISO 8601）")
    axis_averages: dict[str, float] = Field(..., description="16軸の全pitch平均値")
    diversity_scores: DiversityScores = Field(..., description="多様性スコア")
    pitch_rankings: list[PitchRanking] = Field(..., description="推薦順位")
    summary: str = Field(..., description="全体を俯瞰した総合コメント")


class PitchDocument(BaseModel):
    """最終的なペラ1企画書ドキュメント"""
    idea_id: str
    title: str
    pitch: ExpandedPitch
    image_prompt: ImagePrompt
    image_path: Optional[str] = None
    markdown_path: Optional[str] = None
    json_path: Optional[str] = None
