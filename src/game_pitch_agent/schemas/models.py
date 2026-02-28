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


# ────────────────────────────────────────────────────────────────
# BrainstormAgent の出力
# ────────────────────────────────────────────────────────────────

class BrainstormIdea(BaseModel):
    """ブレインストーミングの1アイデア"""
    idea: str = Field(..., description="アイデアの内容")
    method: str = Field(..., description="使用したアイデア発散手法 (SCAMPER, 6 Hats など)")
    rationale: str = Field(..., description="なぜこのアイデアが面白いか")


class BrainstormOutput(BaseModel):
    """BrainstormAgent の出力"""
    theme: str = Field(..., description="ブレインストーミングのテーマ")
    ideas: list[BrainstormIdea] = Field(..., description="発散したアイデアリスト")
    cross_connections: list[str] = Field(default_factory=list, description="アイデア間の意外な組み合わせ")


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


class CoreIdeasOutput(BaseModel):
    """CoreIdeaAgent の出力"""
    ideas: list[CoreGameIdea] = Field(..., description="コアアイデアリスト")
    diversity_notes: str = Field(..., description="多様性を確保するために意識した点")


# ────────────────────────────────────────────────────────────────
# EvaluationAgent の出力
# ────────────────────────────────────────────────────────────────

class IdeaScore(BaseModel):
    """アイデアの評価スコア"""
    idea_id: str = Field(..., description="評価対象のアイデアID")
    novelty: float = Field(..., ge=0, le=10, description="斬新さ (0-10)")
    clarity: float = Field(..., ge=0, le=10, description="明確さ・わかりやすさ (0-10)")
    fun_factor: float = Field(..., ge=0, le=10, description="ぱっと見て面白そうか (0-10)")
    feasibility: float = Field(..., ge=0, le=10, description="実現可能性 (0-10)")
    total_score: float = Field(..., ge=0, le=40, description="合計スコア (0-40)")
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
    main_action: str = Field(..., description="メインアクション")
    short_term_reward: str = Field(..., description="短期的な報酬")
    long_term_reward: str = Field(..., description="中長期的な報酬")


class ExpandedPitch(BaseModel):
    """展開されたペラ1企画書の内容"""
    idea_id: str = Field(..., description="元のコアアイデアID")
    title: str = Field(..., description="ゲームタイトル")
    catchcopy: str = Field(..., description="キャッチコピー")
    concept: str = Field(..., description="ゲームコンセプト（目的地・感情）")
    overview: str = Field(..., description="ゲーム概要")
    target: str = Field(..., description="ターゲットプレイヤー（詳細なペルソナ）")
    genre: str = Field(..., description="ジャンル")
    platform: str = Field(..., description="想定プラットフォーム")
    core_mechanic: str = Field(..., description="コアメカニクス（遊びの仕組み）")
    game_cycle: GameCycle = Field(..., description="ゲームサイクル")
    art_style: str = Field(..., description="アートスタイル・ビジュアル方針")
    usp: str = Field(..., description="独自の売り（USP）")
    feasibility_note: str = Field(..., description="実現可能性に関する補足")


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
    prompt_en: str = Field(..., description="英語の画像生成プロンプト（詳細）")
    layout_description: str = Field(..., description="レイアウトの説明")
    art_style_notes: str = Field(..., description="アートスタイルの補足")


class ImagePromptsOutput(BaseModel):
    """ImagePromptAgent の出力"""
    image_prompts: list[ImagePrompt] = Field(..., description="画像生成プロンプトリスト")


# ────────────────────────────────────────────────────────────────
# 最終出力ドキュメント
# ────────────────────────────────────────────────────────────────

class PitchDocument(BaseModel):
    """最終的なペラ1企画書ドキュメント"""
    idea_id: str
    title: str
    pitch: ExpandedPitch
    image_prompt: ImagePrompt
    image_path: Optional[str] = None
    markdown_path: Optional[str] = None
    json_path: Optional[str] = None
