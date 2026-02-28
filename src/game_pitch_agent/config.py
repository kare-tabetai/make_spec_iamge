"""config.yaml 読み込みモジュール"""

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel


class ModelsConfig(BaseModel):
    inference_prod: str
    inference_test: str
    image_generation_prod: str
    image_generation_test: str


class GenerationConfig(BaseModel):
    num_pitches: int = 3
    min_ideas_multiplier: int = 2
    image_width: int = 1024
    image_height: int = 512


class OutputConfig(BaseModel):
    directory: str = "output"


class AppConfig(BaseModel):
    mode: Literal["test", "prod"] = "test"
    models: ModelsConfig
    generation: GenerationConfig
    output: OutputConfig

    @property
    def inference_model(self) -> str:
        if self.mode == "prod":
            return self.models.inference_prod
        return self.models.inference_test

    @property
    def image_model(self) -> str:
        if self.mode == "prod":
            return self.models.image_generation_prod
        return self.models.image_generation_test


def load_config(config_path: str | None = None, mode_override: str | None = None) -> AppConfig:
    """
    config.yaml を読み込んで AppConfig を返す。

    Args:
        config_path: 設定ファイルのパス（Noneの場合はプロジェクトルートの config.yaml を使用）
        mode_override: モードの上書き（"test" | "prod"）
    """
    if config_path is None:
        # プロジェクトルートの config.yaml を探す
        current = Path(__file__).parent
        for _ in range(5):
            candidate = current / "config.yaml"
            if candidate.exists():
                config_path = str(candidate)
                break
            current = current.parent
        else:
            raise FileNotFoundError("config.yaml が見つかりません")

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    models_raw = raw.get("models", {})
    generation_raw = raw.get("generation", {})
    output_raw = raw.get("output", {})

    models = ModelsConfig(
        inference_prod=models_raw.get("inference", {}).get("prod", "gemini-2.5-pro-preview-05-06"),
        inference_test=models_raw.get("inference", {}).get("test", "gemini-2.0-flash-lite"),
        image_generation_prod=models_raw.get("image_generation", {}).get("prod", "gemini-2.0-flash-preview-image-generation"),
        image_generation_test=models_raw.get("image_generation", {}).get("test", "gemini-2.0-flash-preview-image-generation"),
    )

    config = AppConfig(
        mode=raw.get("mode", "test"),
        models=models,
        generation=GenerationConfig(**generation_raw) if generation_raw else GenerationConfig(),
        output=OutputConfig(**output_raw) if output_raw else OutputConfig(),
    )

    if mode_override:
        config = config.model_copy(update={"mode": mode_override})

    return config
