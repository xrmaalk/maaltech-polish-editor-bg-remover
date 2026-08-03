"""Local image-processing engine used by Polish Editor."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import threading
from typing import Callable

import cv2 as cv
import numpy as np
from PIL import Image, ImageChops, ImageEnhance, ImageOps


ProgressCallback = Callable[[str], None]
BACKGROUND_MODEL = "u2net_human_seg"
_BACKGROUND_SESSION = None
_BACKGROUND_SESSION_LOCK = threading.Lock()


@dataclass(frozen=True)
class PolishSettings:
    """Controls for one processing run."""

    strength: float = 0.78
    texture: float = 0.25
    face_only: bool = True
    fallback_to_image: bool = True
    healthy_tone: bool = True
    remove_background: bool = False

    def normalized(self) -> "PolishSettings":
        return PolishSettings(
            strength=float(np.clip(self.strength, 0.0, 1.0)),
            texture=float(np.clip(self.texture, 0.0, 1.0)),
            face_only=bool(self.face_only),
            fallback_to_image=bool(self.fallback_to_image),
            healthy_tone=bool(self.healthy_tone),
            remove_background=bool(self.remove_background),
        )


@dataclass(frozen=True)
class ProcessingReport:
    faces_detected: int
    regions_processed: int
    used_full_image_fallback: bool
    background_removed: bool = False


@dataclass
class ImageMetadata:
    exif: Image.Exif | None = None
    icc_profile: bytes | None = None


def guided_filter(guide: np.ndarray, src: np.ndarray, radius: int, eps: float) -> np.ndarray:
    """Apply a fast edge-preserving guided filter to an 8-bit image."""
    guide_f = guide.astype(np.float32) / 255.0
    src_f = src.astype(np.float32) / 255.0
    kernel = (max(3, radius), max(3, radius))

    mean_i = cv.boxFilter(guide_f, -1, kernel)
    mean_p = cv.boxFilter(src_f, -1, kernel)
    mean_ip = cv.boxFilter(guide_f * src_f, -1, kernel)
    covariance = mean_ip - mean_i * mean_p

    mean_ii = cv.boxFilter(guide_f * guide_f, -1, kernel)
    variance = mean_ii - mean_i * mean_i
    a = covariance / (variance + eps)
    b = mean_p - a * mean_i

    mean_a = cv.boxFilter(a, -1, kernel)
    mean_b = cv.boxFilter(b, -1, kernel)
    filtered = mean_a * guide_f + mean_b
    return np.clip(filtered * 255.0, 0, 255).astype(np.uint8)


def _skin_mask(face: np.ndarray) -> np.ndarray:
    """Build a softly feathered skin-tone mask using two color spaces."""
    hsv = cv.cvtColor(face, cv.COLOR_BGR2HSV)
    ycrcb = cv.cvtColor(face, cv.COLOR_BGR2YCrCb)

    hsv_mask = cv.inRange(
        hsv,
        np.array([0, 12, 35], dtype=np.uint8),
        np.array([35, 210, 255], dtype=np.uint8),
    )
    ycrcb_mask = cv.inRange(
        ycrcb,
        np.array([0, 125, 65], dtype=np.uint8),
        np.array([255, 185, 145], dtype=np.uint8),
    )
    mask = cv.bitwise_and(hsv_mask, ycrcb_mask)
    mask = cv.morphologyEx(mask, cv.MORPH_OPEN, np.ones((3, 3), np.uint8))
    mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    return cv.GaussianBlur(mask, (21, 21), 0)


def _guided_filter_scaled(region: np.ndarray, radius: int, eps: float) -> np.ndarray:
    """Limit peak memory while retaining the original output dimensions."""
    height, width = region.shape[:2]
    longest = max(height, width)
    if longest <= 1800:
        return guided_filter(region, region, radius, eps)

    scale = 1800.0 / longest
    smaller = cv.resize(region, None, fx=scale, fy=scale, interpolation=cv.INTER_AREA)
    reduced_radius = max(7, round(radius * scale))
    filtered = guided_filter(smaller, smaller, reduced_radius, eps)
    return cv.resize(filtered, (width, height), interpolation=cv.INTER_CUBIC)


def _polish_region(region: np.ndarray, settings: PolishSettings) -> np.ndarray:
    radius = int(round(13 + settings.strength * 22))
    eps = 0.055 - settings.strength * 0.03
    smooth = _guided_filter_scaled(region, radius=radius, eps=max(0.015, eps))
    mask = _skin_mask(region).astype(np.float32) / 255.0
    alpha = mask * settings.strength

    result = np.empty_like(region)
    for channel in range(3):
        original_channel = region[:, :, channel].astype(np.float32)
        smooth_channel = smooth[:, :, channel].astype(np.float32)
        result[:, :, channel] = np.clip(
            original_channel * (1.0 - alpha) + smooth_channel * alpha,
            0,
            255,
        ).astype(np.uint8)

    # Restore signed high-frequency information only where the mask applies.
    low_frequency = cv.GaussianBlur(region, (3, 3), 0).astype(np.int16)
    details = region.astype(np.int16) - low_frequency
    detail_weight = (settings.texture * mask)[:, :, None]
    restored = result.astype(np.float32) + details.astype(np.float32) * detail_weight
    return np.clip(restored, 0, 255).astype(np.uint8)


def _detect_faces(gray: np.ndarray) -> list[tuple[int, int, int, int]]:
    cascade_path = cv.data.haarcascades + "haarcascade_frontalface_default.xml"
    cascade = cv.CascadeClassifier(cascade_path)
    if cascade.empty():
        return []
    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.06,
        minNeighbors=5,
        minSize=(100, 100),
    )
    return [tuple(int(value) for value in face) for face in faces]


def _get_background_session():
    """Create and cache the local rembg inference session."""
    global _BACKGROUND_SESSION
    if _BACKGROUND_SESSION is not None:
        return _BACKGROUND_SESSION

    with _BACKGROUND_SESSION_LOCK:
        if _BACKGROUND_SESSION is None:
            try:
                from rembg import new_session

                _BACKGROUND_SESSION = new_session(BACKGROUND_MODEL)
            except Exception as exc:
                raise RuntimeError(
                    "The background-removal model could not be prepared. "
                    "The first use requires an internet connection so the model can be "
                    "downloaded; later uses run locally.\n\n"
                    f"Technical detail: {type(exc).__name__}: {exc}"
                ) from exc
    return _BACKGROUND_SESSION


def _remove_background(image: Image.Image) -> Image.Image:
    """Return an RGBA image with its background converted to transparency."""
    try:
        from rembg import remove
    except ImportError as exc:
        raise RuntimeError(
            "The packaged background-removal engine could not be loaded. Rebuild "
            "Polish Editor with build_windows.bat.\n\n"
            f"Technical detail: {type(exc).__name__}: {exc}"
        ) from exc

    session = _get_background_session()
    result = remove(image.convert("RGB"), session=session)
    if not isinstance(result, Image.Image):
        raise RuntimeError("The background remover returned an unsupported result.")
    return result.convert("RGBA")


def background_dependency_report() -> str:
    """Import the frozen background stack without downloading a model."""
    import cv2
    import numpy
    import onnxruntime
    import PIL
    import pymatting
    import scipy
    import skimage
    from rembg import new_session, remove
    from rembg.sessions.u2net_human_seg import U2netHumanSegSession

    # Keep explicit references so frozen-build analyzers retain the imports.
    assert callable(new_session)
    assert callable(remove)
    assert U2netHumanSegSession.name() == BACKGROUND_MODEL
    return (
        f"rembg background stack OK; onnxruntime={onnxruntime.__version__}; "
        f"opencv={cv2.__version__}; numpy={numpy.__version__}; "
        f"pillow={PIL.__version__}; scipy={scipy.__version__}; "
        f"skimage={skimage.__version__}; pymatting={pymatting.__version__}"
    )


def polish_image(
    input_path: str | Path,
    settings: PolishSettings | None = None,
    progress: ProgressCallback | None = None,
) -> tuple[Image.Image, ProcessingReport, ImageMetadata]:
    """Load and polish an image without writing it to disk."""
    settings = (settings or PolishSettings()).normalized()
    notify = progress or (lambda _message: None)
    notify("Loading image…")

    with Image.open(input_path) as source:
        source.load()
        transposed = ImageOps.exif_transpose(source)
        alpha = transposed.getchannel("A") if "A" in transposed.getbands() else None
        rgb_image = transposed.convert("RGB")
        exif = source.getexif()
        if 274 in exif:  # Orientation is already applied by exif_transpose.
            del exif[274]
        metadata = ImageMetadata(
            exif=exif if len(exif) else None,
            icc_profile=source.info.get("icc_profile"),
        )

    rgb = np.asarray(rgb_image)
    bgr = cv.cvtColor(rgb, cv.COLOR_RGB2BGR)
    gray = cv.cvtColor(bgr, cv.COLOR_BGR2GRAY)

    notify("Detecting faces…")
    faces = _detect_faces(gray) if settings.face_only else []
    used_fallback = False
    if settings.face_only and faces:
        regions = faces
    elif settings.face_only and not settings.fallback_to_image:
        regions = []
    else:
        regions = [(0, 0, bgr.shape[1], bgr.shape[0])]
        used_fallback = settings.face_only and not faces

    for index, (x, y, width, height) in enumerate(regions, start=1):
        notify(f"Polishing region {index} of {len(regions)}…")
        # Include nearby skin without extending outside the image.
        pad_x = round(width * 0.08) if settings.face_only and faces else 0
        pad_y = round(height * 0.10) if settings.face_only and faces else 0
        x1, y1 = max(0, x - pad_x), max(0, y - pad_y)
        x2 = min(bgr.shape[1], x + width + pad_x)
        y2 = min(bgr.shape[0], y + height + pad_y)
        region = bgr[y1:y2, x1:x2]
        if region.size:
            bgr[y1:y2, x1:x2] = _polish_region(region, settings)

    notify("Applying finishing adjustments…")
    output = Image.fromarray(cv.cvtColor(bgr, cv.COLOR_BGR2RGB))
    if settings.healthy_tone:
        output = ImageEnhance.Brightness(output).enhance(1.02)
        output = ImageEnhance.Contrast(output).enhance(1.03)
        output = ImageEnhance.Color(output).enhance(1.02)
        output = ImageEnhance.Sharpness(output).enhance(1.08)

    if settings.remove_background:
        notify("Removing background… First use may download the local model.")
        output = _remove_background(output)

    if alpha is not None:
        if output.mode == "RGBA":
            output.putalpha(ImageChops.multiply(output.getchannel("A"), alpha))
        else:
            output.putalpha(alpha)

    return output, ProcessingReport(
        faces_detected=len(faces),
        regions_processed=len(regions),
        used_full_image_fallback=used_fallback,
        background_removed=settings.remove_background,
    ), metadata


def save_processed_image(
    image: Image.Image,
    output_path: str | Path,
    metadata: ImageMetadata | None = None,
    quality: int = 95,
) -> None:
    """Save a processed image with format-appropriate options."""
    destination = Path(output_path)
    extension = destination.suffix.lower()
    quality = int(np.clip(quality, 70, 100))
    kwargs: dict[str, object] = {}

    if metadata:
        if metadata.exif is not None and extension in {".jpg", ".jpeg", ".webp", ".tif", ".tiff"}:
            kwargs["exif"] = metadata.exif
        if metadata.icc_profile:
            kwargs["icc_profile"] = metadata.icc_profile

    output = image
    if extension in {".jpg", ".jpeg"}:
        if output.mode == "RGBA":
            background = Image.new("RGB", output.size, "white")
            background.paste(output, mask=output.getchannel("A"))
            output = background
        else:
            output = output.convert("RGB")
        kwargs.update(quality=quality, optimize=True, subsampling=0)
    elif extension == ".webp":
        kwargs.update(quality=quality, method=6)
    elif extension == ".png":
        kwargs.update(compress_level=6)

    destination.parent.mkdir(parents=True, exist_ok=True)
    output.save(destination, **kwargs)
