"""Generate the MAALTECH mascot icon used by the app and installer."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageOps


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = PROJECT_ROOT / "assets" / "maaltech_mascot_icon.png"
DEFAULT_OUTPUT = PROJECT_ROOT / "assets" / "app.ico"
ICON_SIZES = [
    (16, 16),
    (20, 20),
    (24, 24),
    (32, 32),
    (40, 40),
    (48, 48),
    (64, 64),
    (128, 128),
    (256, 256),
]


def build_icon(
    size: int = 1024,
    source_path: str | Path = DEFAULT_SOURCE,
) -> Image.Image:
    """Load and normalize the bundled MAALTECH mascot artwork."""
    source = Path(source_path)
    if not source.is_file():
        raise FileNotFoundError(
            f"Mascot icon source was not found: {source}\n"
            "Keep maaltech_mascot_icon.png in the project's assets folder."
        )

    with Image.open(source) as original:
        mascot = ImageOps.exif_transpose(original).convert("RGBA")

    # ImageOps.fit keeps custom replacement artwork square without stretching it.
    if mascot.size != (size, size):
        mascot = ImageOps.fit(
            mascot,
            (size, size),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
    return mascot


def generate_icon(
    source_path: str | Path = DEFAULT_SOURCE,
    output_path: str | Path = DEFAULT_OUTPUT,
) -> Path:
    """Write a multi-resolution Windows ICO from the mascot source artwork."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    image = build_icon(source_path=source_path)
    image.save(output, format="ICO", sizes=ICON_SIZES)
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the Polish Editor MAALTECH mascot Windows icon."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"Square PNG source artwork (default: {DEFAULT_SOURCE})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"ICO destination (default: {DEFAULT_OUTPUT})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = generate_icon(args.source, args.output)
    sizes = ", ".join(f"{width}x{height}" for width, height in ICON_SIZES)
    print(f"Generated {output}")
    print(f"Included Windows icon sizes: {sizes}")


if __name__ == "__main__":
    main()
