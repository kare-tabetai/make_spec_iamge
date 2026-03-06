"""パイプライン構築・実行・ログ管理モジュール"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from typing import Any

from google.adk.agents import SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from pydantic import ValidationError

from .agents import (
    create_google_research_agent,
    create_ddg_research_agent,
    create_brainstorm_pipeline,
    create_core_idea_agent,
    create_evaluation_agent,
    create_expansion_agent,
    create_image_prompt_agent,
    create_critique_agent,
)
from .config import AppConfig
from .schemas.models import (
    ResearchOutput,
    BrainstormOutput,
    CoreIdeasOutput,
    CritiqueOutput,
    EvaluationOutput,
    ExpandedIdeasOutput,
    ImagePromptsOutput,
    MandalartOutput,
)

logger = logging.getLogger(__name__)


def setup_output_directory(config: AppConfig, topic: str) -> Path:
    """実行ごとの出力ディレクトリを作成する"""
    timestamp = datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y%m%d_%H%M%S")
    # トピックをファイル名に使えるように整形
    safe_topic = "".join(c if c.isalnum() or c in "._- " else "_" for c in topic)
    safe_topic = safe_topic[:30].strip()
    dir_name = f"{timestamp}_{safe_topic}"
    output_dir = Path(config.output.directory) / dir_name
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "logs").mkdir(exist_ok=True)
    return output_dir


def setup_logging(output_dir: Path) -> logging.Logger:
    """ログ設定を行う"""
    log_format = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"

    # ルートロガー設定
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # コンソールハンドラ
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(console_handler)

    # セッションログファイル
    session_log_path = output_dir / "logs" / "session.log"
    file_handler = logging.FileHandler(str(session_log_path), encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(file_handler)

    return root_logger


def save_agent_log(output_dir: Path, step_num: int, agent_name: str, data: dict) -> None:
    """エージェントごとのログを保存する"""
    log_filename = f"{step_num:02d}_{agent_name.lower()}.log"
    log_path = output_dir / "logs" / log_filename
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.debug(f"エージェントログ保存: {log_path}")


def extract_json_from_state(state: dict, key: str) -> dict | list | None:
    """Session State からJSONデータを抽出する"""
    value = state.get(key)
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        cleaned = value.strip()

        # コードブロックの除去
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1]).strip()

        # 直接パース試行
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # テキスト内の最初の JSON オブジェクト/配列を検索
        decoder = json.JSONDecoder()
        for start_char in ["{", "["]:
            idx = cleaned.find(start_char)
            if idx >= 0:
                try:
                    result, _ = decoder.raw_decode(cleaned, idx)
                    return result
                except json.JSONDecodeError:
                    pass

        logger.warning(f"JSONデコードエラー (key={key}): {value[:200]}")
        return None
    return None


async def run_pipeline(
    topic: str,
    config: AppConfig,
    output_dir: Path,
    skip_image: bool = False,
    search_engine: str = "ddg",
) -> dict[str, Any]:
    """
    パイプラインを実行してすべての結果を返す。

    Args:
        topic: ゲームアイデアのトピック
        config: アプリ設定
        output_dir: 出力ディレクトリ
        skip_image: Trueの場合、画像プロンプト生成エージェントをスキップ
        search_engine: 検索エンジン ("ddg" or "google")

    Returns:
        パイプラインの実行結果
    """
    model = config.inference_model
    num_pitches = config.generation.num_pitches
    min_ideas = num_pitches * config.generation.min_ideas_multiplier

    logger.info(f"パイプライン開始: topic='{topic}', model={model}, num_pitches={num_pitches}")
    logger.info(f"出力ディレクトリ: {output_dir}")
    logger.info(f"検索エンジン: {search_engine}")

    # エージェント作成（メインパイプライン: Steps 1-11, ExpansionAgentまで）
    use_google = search_engine == "google"
    agents = []
    if use_google:
        agents.append(create_google_research_agent(model))
    agents += [
        create_ddg_research_agent(model, standalone=not use_google),
        create_brainstorm_pipeline(model),
        create_core_idea_agent(model),
        create_evaluation_agent(model),
        create_expansion_agent(model),
    ]

    if skip_image:
        logger.info("画像生成スキップ: ImagePromptAgent を除外します")

    # SequentialAgent（メインパイプライン）構築
    pipeline = SequentialAgent(
        name="GamePitchPipeline",
        sub_agents=agents,
    )

    # セッションサービスとランナーの設定
    session_service = InMemorySessionService()
    runner = Runner(
        agent=pipeline,
        app_name="game_pitch_agent",
        session_service=session_service,
    )

    # 初期セッション状態
    initial_state = {
        "topic": topic,
        "num_pitches": num_pitches,
        "min_ideas_count": min_ideas,
    }

    # セッション作成
    session = await session_service.create_session(
        app_name="game_pitch_agent",
        user_id="user",
        state=initial_state,
    )
    session_id = session.id

    # メインパイプライン実行（Steps 1-11）
    logger.info("メインパイプライン実行中 (Steps 1-11)...")
    message = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=f"ゲームトピック: {topic}")],
    )

    final_state = {}
    token_stats: list[dict] = []

    async for event in runner.run_async(
        user_id="user",
        session_id=session_id,
        new_message=message,
    ):
        # トークン使用量の収集
        if hasattr(event, "usage_metadata") and event.usage_metadata:
            meta = event.usage_metadata
            agent_name = getattr(event, "author", "unknown")
            token_stats.append({
                "agent": agent_name,
                "input_tokens": getattr(meta, "prompt_token_count", 0) or 0,
                "output_tokens": getattr(meta, "candidates_token_count", 0) or 0,
            })
        if event.is_final_response():
            logger.info("メインパイプライン完了")

    # 最終セッション状態を取得
    final_session = await session_service.get_session(
        app_name="game_pitch_agent",
        user_id="user",
        session_id=session_id,
    )
    final_state = final_session.state if final_session else {}

    # CritiqueAgent + リファインループ
    critique_threshold = config.generation.critique_threshold
    critique_max_reruns = config.generation.critique_max_reruns

    for rerun in range(critique_max_reruns):
        logger.info(f"CritiqueAgent 実行中 (ラウンド {rerun + 1})...")
        critique_result = await _run_single_agent(
            create_critique_agent(model),
            final_state,
            token_stats,
        )
        if critique_result:
            final_state["critique_output"] = critique_result

        critique_data = extract_json_from_state(final_state, "critique_output")
        if not critique_data:
            logger.warning("CritiqueAgent の出力を取得できませんでした。リファインをスキップします。")
            break

        # 最低スコアを確認
        critiques = critique_data.get("critiques", [])
        if not critiques:
            break

        min_score = min(c.get("overall_score", 10) for c in critiques)
        avg_score = sum(c.get("overall_score", 0) for c in critiques) / len(critiques)
        logger.info(f"CritiqueAgent スコア: 平均={avg_score:.1f}, 最低={min_score:.1f} (閾値={critique_threshold})")

        if avg_score >= critique_threshold:
            logger.info("品質基準を満たしました。リファインループを終了します。")
            break

        if rerun < critique_max_reruns - 1:
            # フィードバックをstateに注入してExpansionAgentを再実行
            feedback_text = "\n".join(
                f"- {c.get('idea_id', '?')}: {c.get('feedback', '')}" for c in critiques
            )
            final_state["critique_feedback"] = feedback_text
            logger.info(f"品質基準未達。ExpansionAgentを再実行します (リファイン {rerun + 2}/{critique_max_reruns})...")

            expansion_result = await _run_single_agent(
                create_expansion_agent(model),
                final_state,
                token_stats,
            )
            if expansion_result:
                final_state["expanded_ideas_output"] = expansion_result
        else:
            logger.info(f"最大リラン回数({critique_max_reruns})に到達。現在の結果で続行します。")

    # ImagePromptAgent実行（skip_imageでなければ）
    if not skip_image:
        logger.info("ImagePromptAgent 実行中...")
        image_prompt_result = await _run_single_agent(
            create_image_prompt_agent(model, language=config.generation.language),
            final_state,
            token_stats,
        )
        if image_prompt_result:
            final_state["image_prompts_output"] = image_prompt_result

    logger.info(f"Session State キー: {list(final_state.keys())}")

    # 各エージェントの結果をログに保存
    agent_logs = []
    step = 1
    if use_google:
        agent_logs.append((step, "google_research", "google_research_output"))
        step += 1
    agent_logs.append((step, "ddg_research", "research_output"))
    step += 1
    for name, key in [
        ("brainstorm_scamper", "scamper_output"),
        ("brainstorm_sixhats", "sixhats_output"),
        ("brainstorm_reverse", "reverse_output"),
        ("brainstorm_mandalart_stage1", "mandalart_stage1_output"),
        ("brainstorm_mandalart", "mandalart_output"),
        ("brainstorm_shiritori", "shiritori_output"),
        ("brainstorm", "brainstorm_output"),
        ("core_idea", "core_ideas_output"),
        ("evaluation", "evaluation_output"),
        ("expansion", "expanded_ideas_output"),
        ("critique", "critique_output"),
    ]:
        agent_logs.append((step, name, key))
        step += 1
    if not skip_image:
        agent_logs.append((step, "image_prompt", "image_prompts_output"))

    # Pydanticバリデーション用マッピング
    _VALIDATION_MAP = {
        "google_research_output": ResearchOutput,
        "research_output": ResearchOutput,
        "brainstorm_output": BrainstormOutput,
        "mandalart_output": MandalartOutput,
        "core_ideas_output": CoreIdeasOutput,
        "evaluation_output": EvaluationOutput,
        "expanded_ideas_output": ExpandedIdeasOutput,
        "critique_output": CritiqueOutput,
        "image_prompts_output": ImagePromptsOutput,
    }

    results = {}
    for step_num, agent_name, state_key in agent_logs:
        data = extract_json_from_state(final_state, state_key)
        if data:
            # Pydanticバリデーション（パイプラインは停止しない）
            model_class = _VALIDATION_MAP.get(state_key)
            if model_class and isinstance(data, dict):
                try:
                    model_class.model_validate(data)
                    logger.debug(f"バリデーション成功: {state_key}")
                except ValidationError as ve:
                    logger.warning(f"バリデーション警告 ({state_key}): {ve}")

            results[state_key] = data
            save_agent_log(
                output_dir,
                step_num,
                agent_name,
                {
                    "agent": agent_name,
                    "state_key": state_key,
                    "timestamp": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
                    "data": data,
                },
            )
            logger.info(f"✓ {agent_name} の結果を取得しました")
        else:
            logger.warning(f"✗ {agent_name} の結果が取得できませんでした (key={state_key})")
            # フォールバック: raw文字列を保存
            raw_value = final_state.get(state_key)
            if raw_value:
                save_agent_log(
                    output_dir,
                    step_num,
                    agent_name,
                    {
                        "agent": agent_name,
                        "state_key": state_key,
                        "timestamp": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
                        "raw": str(raw_value)[:5000],
                        "error": "JSONデコード失敗",
                    },
                )

    results["topic"] = topic
    results["config"] = {
        "mode": config.mode,
        "model": model,
        "num_pitches": num_pitches,
    }

    # トークン統計をまとめる
    stats = _aggregate_token_stats(token_stats)
    results["stats"] = stats

    return results


def _aggregate_token_stats(raw_stats: list[dict]) -> dict:
    """トークン使用量を集計する"""
    agent_totals: dict[str, dict] = {}
    for entry in raw_stats:
        name = entry["agent"]
        if name not in agent_totals:
            agent_totals[name] = {"agent": name, "input_tokens": 0, "output_tokens": 0, "total": 0}
        agent_totals[name]["input_tokens"] += entry["input_tokens"]
        agent_totals[name]["output_tokens"] += entry["output_tokens"]
        agent_totals[name]["total"] += entry["input_tokens"] + entry["output_tokens"]

    agents_list = list(agent_totals.values())
    total_input = sum(a["input_tokens"] for a in agents_list)
    total_output = sum(a["output_tokens"] for a in agents_list)

    return {
        "agents": agents_list,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "grand_total": total_input + total_output,
    }


async def _run_single_agent(
    agent,
    current_state: dict,
    token_stats: list[dict],
) -> dict | list | None:
    """単一エージェントを現在のstateで実行し、結果を返す。

    Args:
        agent: 実行するLlmAgent
        current_state: 現在のSession State
        token_stats: トークン統計の収集リスト（副作用で追記）

    Returns:
        エージェントのoutput_keyに対応するJSONデータ、またはNone
    """
    output_key = agent.output_key

    pipeline = SequentialAgent(
        name=f"{agent.name}OnlyPipeline",
        sub_agents=[agent],
    )

    session_service = InMemorySessionService()
    runner = Runner(
        agent=pipeline,
        app_name="game_pitch_agent",
        session_service=session_service,
    )

    session = await session_service.create_session(
        app_name="game_pitch_agent",
        user_id="user",
        state=dict(current_state),
    )

    message = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text="続行してください")],
    )

    async for event in runner.run_async(
        user_id="user",
        session_id=session.id,
        new_message=message,
    ):
        if hasattr(event, "usage_metadata") and event.usage_metadata:
            meta = event.usage_metadata
            agent_name = getattr(event, "author", "unknown")
            token_stats.append({
                "agent": agent_name,
                "input_tokens": getattr(meta, "prompt_token_count", 0) or 0,
                "output_tokens": getattr(meta, "candidates_token_count", 0) or 0,
            })
        if event.is_final_response():
            break

    final_session = await session_service.get_session(
        app_name="game_pitch_agent",
        user_id="user",
        session_id=session.id,
    )
    final_state = final_session.state if final_session else {}

    result = extract_json_from_state(final_state, output_key)
    if result:
        logger.info(f"✓ {agent.name} の結果を取得しました")
    else:
        logger.warning(f"✗ {agent.name} の結果が取得できませんでした (key={output_key})")
    return result


async def run_image_prompt_for_pitch(pitch: dict, config: AppConfig) -> dict | None:
    """単一の企画書に対してImagePromptAgentを実行し、image_promptを返す。

    Args:
        pitch: 企画書データ（expanded_ideas_output 内の1件分）
        config: アプリ設定

    Returns:
        image_prompt dict または None
    """
    model = config.inference_model
    agent = create_image_prompt_agent(model, language=config.generation.language)

    pipeline = SequentialAgent(
        name="ImagePromptOnlyPipeline",
        sub_agents=[agent],
    )

    session_service = InMemorySessionService()
    runner = Runner(
        agent=pipeline,
        app_name="game_pitch_agent",
        session_service=session_service,
    )

    # ImagePromptAgent は expanded_ideas_output キーから企画書データを読む
    initial_state = {
        "expanded_ideas_output": {"pitches": [pitch]},
    }

    session = await session_service.create_session(
        app_name="game_pitch_agent",
        user_id="user",
        state=initial_state,
    )

    message = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text="画像プロンプトを生成してください")],
    )

    async for event in runner.run_async(
        user_id="user",
        session_id=session.id,
        new_message=message,
    ):
        if event.is_final_response():
            break

    final_session = await session_service.get_session(
        app_name="game_pitch_agent",
        user_id="user",
        session_id=session.id,
    )
    final_state = final_session.state if final_session else {}

    image_prompts_output = extract_json_from_state(final_state, "image_prompts_output")
    if image_prompts_output:
        prompts = image_prompts_output.get("image_prompts", [])
        if prompts:
            return prompts[0]

    logger.warning("ImagePromptAgent から結果を取得できませんでした")
    return None
