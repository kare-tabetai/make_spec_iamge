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

from .agents import (
    create_google_research_agent,
    create_ddg_research_agent,
    create_brainstorm_pipeline,
    create_core_idea_agent,
    create_evaluation_agent,
    create_expansion_agent,
    create_image_prompt_agent,
)
from .config import AppConfig

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
) -> dict[str, Any]:
    """
    パイプラインを実行してすべての結果を返す。

    Args:
        topic: ゲームアイデアのトピック
        config: アプリ設定
        output_dir: 出力ディレクトリ
        skip_image: Trueの場合、画像プロンプト生成エージェントをスキップ

    Returns:
        パイプラインの実行結果
    """
    model = config.inference_model
    num_pitches = config.generation.num_pitches
    min_ideas = num_pitches * config.generation.min_ideas_multiplier

    logger.info(f"パイプライン開始: topic='{topic}', model={model}, num_pitches={num_pitches}")
    logger.info(f"出力ディレクトリ: {output_dir}")

    # エージェント作成
    agents = [
        create_google_research_agent(model),
        create_ddg_research_agent(model),
        create_brainstorm_pipeline(model),
        create_core_idea_agent(model),
        create_evaluation_agent(model),
        create_expansion_agent(model),
    ]
    if not skip_image:
        agents.append(create_image_prompt_agent(model, language=config.generation.language))
    else:
        logger.info("画像生成スキップ: ImagePromptAgent を除外します")

    # SequentialAgent（パイプライン）構築
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

    # パイプライン実行
    logger.info("パイプライン実行中...")
    message = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=f"ゲームトピック: {topic}")],
    )

    final_state = {}
    async for event in runner.run_async(
        user_id="user",
        session_id=session_id,
        new_message=message,
    ):
        if event.is_final_response():
            logger.info("パイプライン完了")

    # 最終セッション状態を取得
    final_session = await session_service.get_session(
        app_name="game_pitch_agent",
        user_id="user",
        session_id=session_id,
    )
    final_state = final_session.state if final_session else {}

    logger.info(f"Session State キー: {list(final_state.keys())}")

    # 各エージェントの結果をログに保存
    agent_logs = [
        (1, "google_research", "google_research_output"),
        (2, "ddg_research", "research_output"),
        (3, "brainstorm_scamper", "scamper_output"),
        (4, "brainstorm_sixhats", "sixhats_output"),
        (5, "brainstorm_reverse", "reverse_output"),
        (6, "brainstorm_mandalart", "mandalart_output"),
        (7, "brainstorm_shiritori", "shiritori_output"),
        (8, "brainstorm", "brainstorm_output"),
        (9, "core_idea", "core_ideas_output"),
        (10, "evaluation", "evaluation_output"),
        (11, "expansion", "expanded_ideas_output"),
    ]
    if not skip_image:
        agent_logs.append((12, "image_prompt", "image_prompts_output"))

    results = {}
    for step_num, agent_name, state_key in agent_logs:
        data = extract_json_from_state(final_state, state_key)
        if data:
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

    return results


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
