from pathlib import Path

import numpy as np
from PIL import Image

import src.processing as processing
from src.processing import (
    PolishSettings,
    background_dependency_report,
    guided_filter,
    polish_image,
    save_processed_image,
)


def test_guided_filter_preserves_dimensions() -> None:
    source = np.full((40, 60, 3), 128, dtype=np.uint8)
    result = guided_filter(source, source, radius=9, eps=0.03)
    assert result.shape == source.shape
    assert result.dtype == np.uint8


def test_processing_and_png_alpha_round_trip(tmp_path: Path) -> None:
    source = Image.new("RGBA", (180, 160), (180, 130, 105, 210))
    input_path = tmp_path / "input.png"
    output_path = tmp_path / "output.png"
    source.save(input_path)

    result, report, metadata = polish_image(
        input_path,
        PolishSettings(face_only=False, strength=0.5, texture=0.2),
    )
    assert result.size == source.size
    assert result.mode == "RGBA"
    assert report.regions_processed == 1

    save_processed_image(result, output_path, metadata)
    with Image.open(output_path) as saved:
        assert saved.mode == "RGBA"
        assert saved.getchannel("A").getextrema() == (210, 210)


def test_background_removal_option_creates_transparency(tmp_path: Path, monkeypatch) -> None:
    source = Image.new("RGB", (180, 160), (180, 130, 105))
    input_path = tmp_path / "portrait.jpg"
    source.save(input_path)

    def fake_remove_background(image: Image.Image) -> Image.Image:
        result = image.convert("RGBA")
        alpha = Image.new("L", image.size, 255)
        alpha.putpixel((0, 0), 0)
        result.putalpha(alpha)
        return result

    monkeypatch.setattr(processing, "_remove_background", fake_remove_background)
    result, report, _metadata = polish_image(
        input_path,
        PolishSettings(
            face_only=False,
            healthy_tone=False,
            remove_background=True,
        ),
    )

    assert result.mode == "RGBA"
    assert result.getchannel("A").getpixel((0, 0)) == 0
    assert report.background_removed is True


def test_background_dependencies_import_without_model_download() -> None:
    report = background_dependency_report()
    assert "rembg background stack OK" in report
    assert "onnxruntime=" in report
