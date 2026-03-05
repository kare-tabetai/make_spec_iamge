"""CLIエントリーポイント - argparse によるコマンドライン操作"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from .config import AppConfig, load_config
from .pipeline import run_pipeline, run_image_prompt_for_pitch, setup_logging, setup_output_directory, extract_json_from_state
from .tools.image_gen import generate_pitch_image
from .tools.pptx_render import render_pitch_pptx

logger = logging.getLogger(__name__)


def build_markdown(pitch: dict, image_path: str | None = None, pptx_path: str | None = None) -> str:
    """企画書の内容をMarkdown形式に変換する"""
    game_cycle = pitch.get("game_cycle", {})
    lines = [
        f"# {pitch.get('title', '無題')}",
        "",
        f"> {pitch.get('catchcopy', '')}",
        "",
        "---",
        "",
        "## コンセプト",
        pitch.get("concept", ""),
        "",
        "## ゲーム概要",
        pitch.get("overview", ""),
        "",
        f"**ジャンル**: {pitch.get('genre', '')}",
        f"**プラットフォーム**: {pitch.get('platform', '')}",
        "",
        "## コアメカニクス",
        pitch.get("core_mechanic", ""),
        "",
        "## ゲームサイクル",
        f"- **メインアクション**: {game_cycle.get('main_action', '')}",
        f"- **短期的な報酬**: {game_cycle.get('short_term_reward', '')}",
        f"- **中長期的な報酬**: {game_cycle.get('long_term_reward', '')}",
        "",
        "## アートスタイル",
        pitch.get("art_style", ""),
        "",
        "## 差別化ポイント（USP）",
        pitch.get("usp", ""),
        "",
        "## 実現可能性",
        pitch.get("feasibility_note", ""),
    ]
    if image_path:
        lines += [
            "",
            "---",
            "",
            "## ペラ1企画書画像",
            f"![{pitch.get('title', '')}]({image_path})",
        ]
    if pptx_path:
        lines += [
            "",
            "---",
            "",
            "## ペラ1企画書（PPTX）",
            f"[PowerPoint企画書]({pptx_path})",
        ]
    return "\n".join(lines)


def render_pitch_image(pitch_dir: Path, pitch: dict, image_prompt: dict, config: AppConfig) -> str | None:
    """企画書ディレクトリに対して画像生成 + Markdown再生成を行う

    Returns:
        生成された画像のパス文字列、または失敗時は None
    """
    title = pitch.get("title", "無題")
    prompt_text = image_prompt.get("prompt", "")
    layout_desc = image_prompt.get("layout_description", "")
    # layout_description にはテキスト仕様（日本語含む）が含まれるため結合する
    if layout_desc:
        prompt_text = f"{prompt_text} Layout: {layout_desc}"
    # --language ja の場合はタイトル・キャッチコピーを明示的に追記
    if config.generation.language == "ja":
        ja_title = pitch.get("title", "")
        ja_catchcopy = pitch.get("catchcopy", "")
        text_parts = []
        if ja_title:
            text_parts.append(f"title: '{ja_title}'")
        if ja_catchcopy:
            text_parts.append(f"tagline: '{ja_catchcopy}'")
        if text_parts:
            prompt_text += " Japanese text to render in the image: " + ", ".join(text_parts) + ". Render Japanese characters accurately."
    if not prompt_text:
        logger.warning("画像プロンプトが空です")
        return None

    image_file = pitch_dir / "pitch_image.png"
    try:
        logger.info(f"画像生成中: {title}")
        generate_pitch_image(
            prompt=prompt_text,
            output_path=str(image_file),
            model_name=config.image_model,
            width=config.generation.image_width,
            height=config.generation.image_height,
        )
        logger.info(f"画像保存完了: {image_file}")
    except Exception as e:
        logger.error(f"画像生成失敗: {e}", exc_info=True)
        return None

    # Markdown再生成（画像参照付き）
    md_path = pitch_dir / "pitch.md"
    markdown_content = build_markdown(pitch, image_path=image_file.name)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    logger.info(f"Markdown再生成: {md_path}")

    return str(image_file)


def render_pitch_pptx_file(pitch_dir: Path, pitch: dict, image_path: str | None = None) -> str | None:
    """企画書ディレクトリに対して PPTX 生成 + Markdown再生成を行う

    Returns:
        生成された PPTX のパス文字列、または失敗時は None
    """
    title = pitch.get("title", "無題")
    pptx_file = pitch_dir / "pitch.pptx"

    # 既存の画像があれば埋め込む
    embed_image = None
    if image_path and Path(image_path).exists():
        embed_image = image_path
    else:
        candidate = pitch_dir / "pitch_image.png"
        if candidate.exists():
            embed_image = str(candidate)

    try:
        logger.info(f"PPTX生成中: {title}")
        render_pitch_pptx(
            pitch=pitch,
            output_path=str(pptx_file),
            image_path=embed_image,
        )
    except Exception as e:
        logger.error(f"PPTX生成失敗: {e}", exc_info=True)
        return None

    # Markdown再生成（PPTX参照付き、既存画像があればそれも含む）
    md_path = pitch_dir / "pitch.md"
    existing_image = Path(embed_image).name if embed_image else None
    markdown_content = build_markdown(pitch, image_path=existing_image, pptx_path=pptx_file.name)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    logger.info(f"Markdown再生成: {md_path}")

    return str(pptx_file)


def save_pitch_files(
    pitch_dir: Path,
    pitch: dict,
    image_prompt: dict | None,
    config: AppConfig,
    pitch_num: int,
    skip_image: bool = False,
    render_format: str = "image",
) -> dict:
    """企画書ファイル（markdown, json, png/pptx）を保存する"""
    idea_id = pitch.get("idea_id", f"idea_{pitch_num:03d}")
    title = pitch.get("title", f"企画書{pitch_num}")

    # 出力ディレクトリ作成
    pitch_dir.mkdir(parents=True, exist_ok=True)

    # JSON保存
    json_path = pitch_dir / "pitch.json"
    pitch_data = {
        "idea_id": idea_id,
        "title": title,
        "pitch": pitch,
        "image_prompt": image_prompt,
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(pitch_data, f, ensure_ascii=False, indent=2)
    logger.info(f"JSON保存: {json_path}")

    image_path = None
    pptx_path = None

    if render_format == "pptx":
        # PPTX生成（画像生成不要）
        pptx_path = render_pitch_pptx_file(pitch_dir, pitch)
    elif skip_image:
        logger.info("画像生成スキップ（--no-image 指定）")
    elif image_prompt:
        image_path = render_pitch_image(pitch_dir, pitch, image_prompt, config)
    else:
        logger.warning(f"アイデア {idea_id} に対応する画像プロンプトが見つかりません")

    # Markdown保存（画像/PPTXが生成されなかった場合のみ。生成済みの場合は各render関数で保存済み）
    if image_path is None and pptx_path is None:
        md_path = pitch_dir / "pitch.md"
        markdown_content = build_markdown(pitch)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        logger.info(f"Markdown保存: {md_path}")

    return {
        "idea_id": idea_id,
        "title": title,
        "json_path": str(json_path),
        "markdown_path": str(pitch_dir / "pitch.md"),
        "image_path": image_path,
        "pptx_path": pptx_path,
    }


def _log_summary(saved_files: list[dict], output_dir: Path, skip_image: bool = False, render_format: str = "image") -> None:
    """生成結果のサマリーをログ出力する"""
    logger.info("\n" + "=" * 60)
    logger.info("完了！")
    logger.info(f"出力ディレクトリ: {output_dir}")
    for files in saved_files:
        if render_format == "pptx":
            status = "✓（PPTX）" if files.get("pptx_path") else "△（PPTX失敗）"
        elif skip_image:
            status = "○（画像スキップ）"
        elif files.get("image_path"):
            status = "✓"
        else:
            status = "△（画像なし）"
        logger.info(f"  {status} {files['title']}")
        logger.info(f"    - JSON: {files['json_path']}")
        logger.info(f"    - Markdown: {files['markdown_path']}")
        if files.get("image_path"):
            logger.info(f"    - Image: {files['image_path']}")
        if files.get("pptx_path"):
            logger.info(f"    - PPTX: {files['pptx_path']}")
    logger.info("=" * 60)


def _load_config_for_render(args: argparse.Namespace, output_dir: Path) -> AppConfig:
    """render用設定: request_info.jsonの値をデフォルトにし、CLI引数で上書き"""
    request_info_path = output_dir / "request_info.json"

    original_mode = None
    original_language = None

    if request_info_path.exists():
        with open(request_info_path, "r", encoding="utf-8") as f:
            request_info = json.load(f)
        original_mode = request_info.get("mode")
        original_language = request_info.get("language")
        logger.info(f"request_info.json から設定を読み込み: mode={original_mode}, language={original_language}")

    # CLI引数があればそちらを優先
    mode_override = getattr(args, "mode", None) or original_mode
    language_override = getattr(args, "language", None) or original_language
    config_path = getattr(args, "config", None)

    return load_config(
        config_path=config_path,
        mode_override=mode_override,
        language_override=language_override,
    )


async def async_generate(args: argparse.Namespace) -> int:
    """generate サブコマンド: テキストパイプライン（Steps 1-11）のみ実行"""
    if not os.environ.get("GOOGLE_API_KEY"):
        logger.error("GOOGLE_API_KEY 環境変数が設定されていません")
        return 1

    config_path = getattr(args, "config", None)
    mode_override = getattr(args, "mode", None)
    config = load_config(config_path=config_path, mode_override=mode_override)

    if getattr(args, "num_pitches", None):
        config.generation.num_pitches = args.num_pitches

    topic = args.topic
    output_dir = setup_output_directory(config, topic)
    setup_logging(output_dir)

    logger.info("=" * 60)
    logger.info("ゲーム企画書生成AIエージェントシステム [generate]")
    logger.info(f"  トピック: {topic}")
    logger.info(f"  モード: {config.mode}")
    logger.info(f"  推論モデル: {config.inference_model}")
    logger.info(f"  生成枚数: {config.generation.num_pitches}")
    logger.info(f"  画像生成: スキップ（generateモード）")
    logger.info("=" * 60)

    # リクエスト情報保存
    request_info = {
        "timestamp": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "command": "generate",
        "topic": topic,
        "mode": config.mode,
        "inference_model": config.inference_model,
        "image_model": config.image_model,
        "num_pitches": config.generation.num_pitches,
        "language": config.generation.language,
        "skip_image": True,
    }
    request_info_path = output_dir / "request_info.json"
    with open(request_info_path, "w", encoding="utf-8") as f:
        json.dump(request_info, f, ensure_ascii=False, indent=2)
    logger.info(f"リクエスト情報保存: {request_info_path}")

    # パイプライン実行（skip_image=True → Steps 1-11のみ）
    try:
        results = await run_pipeline(topic=topic, config=config, output_dir=output_dir, skip_image=True)
    except Exception as e:
        logger.error(f"パイプライン実行エラー: {e}", exc_info=True)
        return 1

    expanded_output = results.get("expanded_ideas_output", {})
    if not expanded_output:
        logger.error("企画書の展開結果が取得できませんでした")
        return 1

    pitches = expanded_output.get("pitches", [])
    logger.info(f"\n企画書を {len(pitches)} 件保存します...")

    saved_files = []
    for i, pitch in enumerate(pitches, 1):
        pitch_dir = output_dir / f"pitch_{i}"
        logger.info(f"\n--- 企画書 {i}/{len(pitches)}: {pitch.get('title', '無題')} ---")
        files = save_pitch_files(
            pitch_dir=pitch_dir,
            pitch=pitch,
            image_prompt=None,
            config=config,
            pitch_num=i,
            skip_image=True,
        )
        saved_files.append(files)

    _log_summary(saved_files, output_dir, skip_image=True)
    logger.info(f"出力ディレクトリ: {output_dir}")
    logger.info(f"画像生成するには: game-pitch render --dir {output_dir}")

    return 0


async def async_render(args: argparse.Namespace) -> int:
    """render サブコマンド: 既存の企画書出力から画像/PPTX生成"""
    render_format = getattr(args, "format", "image")

    # PPTX形式はAPI不要
    if render_format != "pptx" and not os.environ.get("GOOGLE_API_KEY"):
        logger.error("GOOGLE_API_KEY 環境変数が設定されていません")
        return 1

    output_dir = Path(args.dir)
    if not output_dir.exists():
        logger.error(f"出力ディレクトリが見つかりません: {output_dir}")
        return 1

    config = _load_config_for_render(args, output_dir)
    setup_logging(output_dir)

    logger.info("=" * 60)
    logger.info("ゲーム企画書生成AIエージェントシステム [render]")
    logger.info(f"  対象ディレクトリ: {output_dir}")
    logger.info(f"  出力形式: {render_format}")
    logger.info(f"  モード: {config.mode}")
    if render_format == "image":
        logger.info(f"  画像生成モデル: {config.image_model}")
        logger.info(f"  画像言語: {config.generation.language}")
    logger.info(f"  強制再生成: {getattr(args, 'force', False)}")
    logger.info("=" * 60)

    # pitch_*/pitch.json を発見
    pitch_dirs = sorted(output_dir.glob("pitch_*"))
    if not pitch_dirs:
        logger.error(f"企画書ディレクトリが見つかりません: {output_dir}/pitch_*")
        return 1

    force = getattr(args, "force", False)
    rendered_count = 0

    for pitch_dir in pitch_dirs:
        json_path = pitch_dir / "pitch.json"
        if not json_path.exists():
            logger.warning(f"pitch.json が見つかりません: {json_path}")
            continue

        with open(json_path, "r", encoding="utf-8") as f:
            pitch_data = json.load(f)

        pitch = pitch_data.get("pitch", {})
        image_prompt = pitch_data.get("image_prompt")
        title = pitch.get("title", "無題")

        if render_format == "pptx":
            # PPTX生成
            existing_pptx = pitch_dir / "pitch.pptx"
            if existing_pptx.exists() and not force:
                logger.info(f"スキップ（PPTXあり）: {title}")
                continue

            logger.info(f"\n--- PPTX生成: {title} ({pitch_dir.name}) ---")
            result = render_pitch_pptx_file(pitch_dir, pitch)
            if result:
                rendered_count += 1
        else:
            # 画像生成（既存ロジック）
            if (pitch_dir / "pitch_image.png").exists() and not force:
                logger.info(f"スキップ（画像あり）: {title}")
                continue

            logger.info(f"\n--- レンダリング: {title} ({pitch_dir.name}) ---")

            # image_prompt が無い or --force → ImagePromptAgent実行
            if image_prompt is None or force:
                logger.info("ImagePromptAgent を実行中...")
                image_prompt = await run_image_prompt_for_pitch(pitch, config)
                if image_prompt is None:
                    logger.warning(f"画像プロンプト生成失敗: {title}")
                    continue
                # pitch.json を更新
                pitch_data["image_prompt"] = image_prompt
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(pitch_data, f, ensure_ascii=False, indent=2)
                logger.info("pitch.json にimage_promptを保存")

            # 画像生成 + Markdown再生成
            result = render_pitch_image(pitch_dir, pitch, image_prompt, config)
            if result:
                rendered_count += 1

    # render_history をrequest_info.jsonに追記
    request_info_path = output_dir / "request_info.json"
    if request_info_path.exists():
        with open(request_info_path, "r", encoding="utf-8") as f:
            request_info = json.load(f)
    else:
        request_info = {}

    render_history = request_info.get("render_history", [])
    render_history.append({
        "timestamp": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "format": render_format,
        "language": config.generation.language,
        "image_model": config.image_model if render_format == "image" else None,
        "force": force,
        "rendered_count": rendered_count,
    })
    request_info["render_history"] = render_history
    with open(request_info_path, "w", encoding="utf-8") as f:
        json.dump(request_info, f, ensure_ascii=False, indent=2)

    logger.info("\n" + "=" * 60)
    logger.info(f"レンダリング完了: {rendered_count}/{len(pitch_dirs)} 件 ({render_format})")
    logger.info("=" * 60)

    return 0


async def async_full(args: argparse.Namespace) -> int:
    """full サブコマンド: テキスト生成＋画像/PPTX生成をまとめて実行（従来の動作と同等）"""
    render_format = getattr(args, "format", "image")

    # PPTX形式はAPI不要だが、テキスト生成パイプラインにはAPIが必要
    if not os.environ.get("GOOGLE_API_KEY"):
        logger.error("GOOGLE_API_KEY 環境変数が設定されていません")
        return 1

    config_path = getattr(args, "config", None)
    mode_override = getattr(args, "mode", None)
    language_override = getattr(args, "language", None)
    config = load_config(config_path=config_path, mode_override=mode_override, language_override=language_override)

    if getattr(args, "num_pitches", None):
        config.generation.num_pitches = args.num_pitches

    topic = args.topic
    skip_image = getattr(args, "no_image", False)
    # PPTX形式の場合はStep12（ImagePromptAgent）をスキップ
    if render_format == "pptx":
        skip_image = True
    output_dir = setup_output_directory(config, topic)
    setup_logging(output_dir)

    logger.info("=" * 60)
    logger.info("ゲーム企画書生成AIエージェントシステム [full]")
    logger.info(f"  トピック: {topic}")
    logger.info(f"  モード: {config.mode}")
    logger.info(f"  出力形式: {render_format}")
    logger.info(f"  推論モデル: {config.inference_model}")
    if render_format == "image":
        logger.info(f"  画像生成モデル: {config.image_model}")
        logger.info(f"  画像言語: {config.generation.language}")
    logger.info(f"  生成枚数: {config.generation.num_pitches}")
    logger.info(f"  画像生成: {'スキップ' if skip_image else '有効'}")
    logger.info("=" * 60)

    # リクエスト情報保存
    request_info = {
        "timestamp": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "command": "full",
        "topic": topic,
        "mode": config.mode,
        "render_format": render_format,
        "inference_model": config.inference_model,
        "image_model": config.image_model,
        "num_pitches": config.generation.num_pitches,
        "language": config.generation.language,
        "skip_image": skip_image,
    }
    request_info_path = output_dir / "request_info.json"
    with open(request_info_path, "w", encoding="utf-8") as f:
        json.dump(request_info, f, ensure_ascii=False, indent=2)
    logger.info(f"リクエスト情報保存: {request_info_path}")

    # パイプライン実行
    try:
        results = await run_pipeline(topic=topic, config=config, output_dir=output_dir, skip_image=skip_image)
    except Exception as e:
        logger.error(f"パイプライン実行エラー: {e}", exc_info=True)
        return 1

    expanded_output = results.get("expanded_ideas_output", {})
    image_prompts_output = results.get("image_prompts_output", {})

    if not expanded_output:
        logger.error("企画書の展開結果が取得できませんでした")
        return 1

    pitches = expanded_output.get("pitches", [])
    image_prompts = image_prompts_output.get("image_prompts", []) if image_prompts_output else []

    # 画像プロンプトをアイデアIDでインデックス化
    prompt_by_idea = {p.get("idea_id"): p for p in image_prompts}

    logger.info(f"\n企画書を {len(pitches)} 件生成します...")

    saved_files = []
    for i, pitch in enumerate(pitches, 1):
        idea_id = pitch.get("idea_id", f"idea_{i:03d}")
        image_prompt = prompt_by_idea.get(idea_id)
        pitch_dir = output_dir / f"pitch_{i}"

        logger.info(f"\n--- 企画書 {i}/{len(pitches)}: {pitch.get('title', '無題')} ---")
        files = save_pitch_files(
            pitch_dir=pitch_dir,
            pitch=pitch,
            image_prompt=image_prompt,
            config=config,
            pitch_num=i,
            skip_image=skip_image,
            render_format=render_format,
        )
        saved_files.append(files)

    _log_summary(saved_files, output_dir, skip_image=skip_image, render_format=render_format)

    return 0


def main() -> None:
    """CLIエントリーポイント"""
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="ゲーム企画書生成AIエージェントシステム",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # テキスト生成のみ（画像なし）
  uv run game-pitch generate --topic "お題:「不自由」"

  # 既存の出力から画像生成
  uv run game-pitch render --dir output/20260301_120000_xxx

  # フルパイプライン（テキスト＋画像）
  uv run game-pitch full --topic "お題:「不自由」"

  # フルパイプライン（画像スキップ）
  uv run game-pitch full --topic "お題:「不自由」" --no-image
        """,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- generate サブコマンド ---
    gen_parser = subparsers.add_parser(
        "generate",
        help="アイデア生成→Markdown企画書出力（画像なし）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    gen_parser.add_argument("--topic", required=True, help="ゲームアイデアのトピック")
    gen_parser.add_argument("--mode", choices=["test", "prod"], default=None, help="実行モード")
    gen_parser.add_argument("--num-pitches", type=int, default=None, help="生成する企画書の枚数")
    gen_parser.add_argument("--config", default=None, help="設定ファイルのパス")

    # --- render サブコマンド ---
    render_parser = subparsers.add_parser(
        "render",
        help="既存の企画書から画像生成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    render_parser.add_argument("--dir", required=True, help="対象の出力ディレクトリ")
    render_parser.add_argument("--format", choices=["image", "pptx"], default="image", help="出力形式 (default: image)")
    render_parser.add_argument("--mode", choices=["test", "prod"], default=None, help="実行モード")
    render_parser.add_argument("--language", choices=["ja", "en"], default=None, help="画像の言語")
    render_parser.add_argument("--force", action="store_true", help="既存画像/PPTXを上書き再生成")
    render_parser.add_argument("--config", default=None, help="設定ファイルのパス")

    # --- full サブコマンド ---
    full_parser = subparsers.add_parser(
        "full",
        help="テキスト生成＋画像生成をまとめて実行",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    full_parser.add_argument("--topic", required=True, help="ゲームアイデアのトピック")
    full_parser.add_argument("--format", choices=["image", "pptx"], default="image", help="出力形式 (default: image)")
    full_parser.add_argument("--mode", choices=["test", "prod"], default=None, help="実行モード")
    full_parser.add_argument("--num-pitches", type=int, default=None, help="生成する企画書の枚数")
    full_parser.add_argument("--language", choices=["ja", "en"], default=None, help="画像の言語")
    full_parser.add_argument("--no-image", action="store_true", help="画像生成をスキップ")
    full_parser.add_argument("--config", default=None, help="設定ファイルのパス")

    args = parser.parse_args()

    handlers = {
        "generate": async_generate,
        "render": async_render,
        "full": async_full,
    }
    handler = handlers[args.command]
    exit_code = asyncio.run(handler(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
