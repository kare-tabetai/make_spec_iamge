"""Gemini 画像生成ツール - google-genai SDK を使用"""

import base64
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def generate_pitch_image(
    prompt: str,
    output_path: str,
    model_name: str = "gemini-2.0-flash-preview-image-generation",
    width: int = 1024,
    height: int = 512,
) -> str:
    """
    Gemini 画像生成モデルを使ってペラ1企画書画像を生成・保存する。

    Args:
        prompt: 画像生成プロンプト（英語推奨）
        output_path: 保存先パス (.png)
        model_name: 使用する画像生成モデル名
        width: 画像幅（ピクセル）
        height: 画像高さ（ピクセル）

    Returns:
        保存先パス（成功）またはエラーメッセージ
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY 環境変数が設定されていません")

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        # 画像生成リクエスト
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        # レスポンスから画像データを抽出
        image_data = None
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_data = part.inline_data.data
                break

        if image_data is None:
            raise RuntimeError("画像データがレスポンスに含まれていませんでした")

        # PNG として保存
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        # バイナリデータ（base64エンコードされている場合はデコード）
        if isinstance(image_data, str):
            image_bytes = base64.b64decode(image_data)
        else:
            image_bytes = image_data

        # Pillow でサイズ調整してPNG保存
        from PIL import Image
        import io

        img = Image.open(io.BytesIO(image_bytes))

        # 指定サイズにリサイズ（アスペクト比を維持せず固定サイズ）
        if img.size != (width, height):
            img = img.resize((width, height), Image.LANCZOS)

        img.save(str(output_path_obj), "PNG")
        logger.info(f"画像を保存しました: {output_path_obj}")
        return str(output_path_obj)

    except Exception as e:
        logger.error(f"画像生成エラー: {e}")
        raise
