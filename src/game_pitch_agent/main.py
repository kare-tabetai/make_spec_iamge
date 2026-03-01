"""CLIエントリーポイント - argparse によるコマンドライン操作"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from .config import load_config
from .pipeline import run_pipeline, setup_logging, setup_output_directory, extract_json_from_state
from .tools.image_gen import generate_pitch_image

logger = logging.getLogger(__name__)


def build_markdown(pitch: dict, image_path: str | None = None) -> str:
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
    return "\n".join(lines)


def save_pitch_files(
    pitch_dir: Path,
    pitch: dict,
    image_prompt: dict | None,
    config,
    pitch_num: int,
) -> dict:
    """企画書ファイル（markdown, json, png）を保存する"""
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

    # 画像生成
    image_path = None
    if image_prompt:
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
        if prompt_text:
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
                image_path = str(image_file)
                logger.info(f"画像保存完了: {image_file}")
            except Exception as e:
                logger.error(f"画像生成失敗: {e}")
        else:
            logger.warning("画像プロンプトが空です")
    else:
        logger.warning(f"アイデア {idea_id} に対応する画像プロンプトが見つかりません")

    # Markdown保存
    md_path = pitch_dir / "pitch.md"
    markdown_content = build_markdown(pitch, image_path=str(image_file.name) if image_path else None)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    logger.info(f"Markdown保存: {md_path}")

    return {
        "idea_id": idea_id,
        "title": title,
        "json_path": str(json_path),
        "markdown_path": str(md_path),
        "image_path": image_path,
    }


async def async_main(args: argparse.Namespace) -> int:
    """メイン処理（非同期）"""
    # 設定読み込み
    config_path = args.config if hasattr(args, "config") and args.config else None
    mode_override = args.mode if hasattr(args, "mode") and args.mode else None
    language_override = args.language if hasattr(args, "language") and args.language else None
    config = load_config(config_path=config_path, mode_override=mode_override, language_override=language_override)

    # num_pitches の上書き
    if hasattr(args, "num_pitches") and args.num_pitches:
        config.generation.num_pitches = args.num_pitches

    topic = args.topic

    # 出力ディレクトリ設定
    output_dir = setup_output_directory(config, topic)

    # ログ設定
    setup_logging(output_dir)

    logger.info("=" * 60)
    logger.info("ゲーム企画書生成AIエージェントシステム 起動")
    logger.info(f"  トピック: {topic}")
    logger.info(f"  モード: {config.mode}")
    logger.info(f"  推論モデル: {config.inference_model}")
    logger.info(f"  画像生成モデル: {config.image_model}")
    logger.info(f"  生成枚数: {config.generation.num_pitches}")
    logger.info(f"  画像言語: {config.generation.language}")
    logger.info("=" * 60)

    # リクエスト情報をログ出力
    request_info = {
        "timestamp": datetime.now().isoformat(),
        "topic": topic,
        "mode": config.mode,
        "inference_model": config.inference_model,
        "image_model": config.image_model,
        "num_pitches": config.generation.num_pitches,
        "language": config.generation.language,
    }
    request_info_path = output_dir / "request_info.json"
    with open(request_info_path, "w", encoding="utf-8") as f:
        json.dump(request_info, f, ensure_ascii=False, indent=2)
    logger.info(f"リクエスト情報保存: {request_info_path}")

    # GOOGLE_API_KEY 確認
    if not os.environ.get("GOOGLE_API_KEY"):
        logger.error("GOOGLE_API_KEY 環境変数が設定されていません")
        return 1

    # パイプライン実行
    try:
        results = await run_pipeline(topic=topic, config=config, output_dir=output_dir)
    except Exception as e:
        logger.error(f"パイプライン実行エラー: {e}", exc_info=True)
        return 1

    # 結果の保存
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
        )
        saved_files.append(files)

    # サマリー出力
    logger.info("\n" + "=" * 60)
    logger.info("完了！")
    logger.info(f"出力ディレクトリ: {output_dir}")
    for files in saved_files:
        status = "✓" if files.get("image_path") else "△（画像なし）"
        logger.info(f"  {status} {files['title']}")
        logger.info(f"    - JSON: {files['json_path']}")
        logger.info(f"    - Markdown: {files['markdown_path']}")
        if files.get("image_path"):
            logger.info(f"    - Image: {files['image_path']}")
    logger.info("=" * 60)

    return 0


def main() -> None:
    """CLIエントリーポイント"""
    # プロジェクトルートの .env を環境変数に読み込む
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="ゲーム企画書生成AIエージェントシステム",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # テストモードで実行（デフォルト）
  uv run game-pitch --topic "お題:「不自由」"

  # 本番モードで実行
  uv run game-pitch --topic "..." --mode prod

  # 生成枚数を指定
  uv run game-pitch --topic "..." --num-pitches 5
        """,
    )
    parser.add_argument(
        "--topic",
        required=True,
        help="ゲームアイデアのトピック（例: 'お題:「不自由」'）",
    )
    parser.add_argument(
        "--mode",
        choices=["test", "prod"],
        default=None,
        help="実行モード (test: 安価なモデル / prod: 高精度モデル)",
    )
    parser.add_argument(
        "--num-pitches",
        type=int,
        default=None,
        help="生成する企画書の枚数（デフォルト: config.yaml の設定値）",
    )
    parser.add_argument(
        "--language",
        choices=["ja", "en"],
        default=None,
        help="企画書画像の言語 (ja: 日本語 / en: 英語)（デフォルト: config.yaml の設定値）",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="設定ファイルのパス（デフォルト: プロジェクトルートの config.yaml）",
    )

    args = parser.parse_args()

    exit_code = asyncio.run(async_main(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
