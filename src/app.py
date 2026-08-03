"""CustomTkinter graphical interface for MAALTECH Polish Editor."""

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageOps
from tkinterdnd2 import DND_FILES, TkinterDnD

from src import __version__
from src.processing import (
    ImageMetadata,
    PolishSettings,
    ProcessingReport,
    polish_image,
    save_processed_image,
)


APP_NAME = "MAALTECH Polish Editor"
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg",
                        ".png", ".webp", ".bmp", ".tif", ".tiff"}
FILE_TYPES = [
    ("Image files", "*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff"),
    ("JPEG", "*.jpg *.jpeg"),
    ("PNG", "*.png"),
    ("WebP", "*.webp"),
    ("All files", "*.*"),
]
TRANSPARENT_FILE_TYPES = [
    ("PNG with transparency", "*.png"),
    ("WebP with transparency", "*.webp"),
    ("JPEG on white background", "*.jpg *.jpeg"),
    ("All files", "*.*"),
]


def resource_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return base / relative


def enable_windows_dpi_awareness() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


class PolishEditorApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self) -> None:
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        self.title(f"{APP_NAME} {__version__}")
        self.geometry("1180x760")
        self.minsize(980, 680)
        icon_path = resource_path("assets/app.ico")
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass

        self.input_path: Path | None = None
        self.original_image: Image.Image | None = None
        self.processed_image: Image.Image | None = None
        self.metadata: ImageMetadata | None = None
        self.report: ProcessingReport | None = None
        self.preview_ctk_image: ctk.CTkImage | None = None
        self.is_processing = False

        self._build_ui()
        self._set_empty_preview()
        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<Drop>>", self._handle_drop)

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, corner_radius=0,
                              height=78, fg_color=("#F3F7F6", "#101715"))
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title_group = ctk.CTkFrame(header, fg_color="transparent")
        title_group.grid(row=0, column=0, padx=28, pady=16, sticky="w")
        ctk.CTkLabel(
            title_group,
            text="MAALTECH POLISH EDITOR",
            font=ctk.CTkFont(size=25, weight="bold"),
            text_color=("#0A5947", "#58D5B4"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_group,
            text="Natural-looking local image refinement",
            font=ctk.CTkFont(size=12),
            text_color=("#4D625D", "#94A9A3"),
        ).pack(anchor="w")

        ctk.CTkButton(
            header,
            text="Open image",
            width=126,
            height=38,
            corner_radius=10,
            command=self.open_image,
        ).grid(row=0, column=1, padx=28, pady=18)

        workspace = ctk.CTkFrame(self, fg_color="transparent")
        workspace.grid(row=1, column=0, padx=20, pady=(20, 12), sticky="nsew")
        workspace.grid_columnconfigure(0, weight=1)
        workspace.grid_columnconfigure(1, minsize=320)
        workspace.grid_rowconfigure(0, weight=1)

        preview_card = ctk.CTkFrame(workspace, corner_radius=16)
        preview_card.grid(row=0, column=0, padx=(0, 16), sticky="nsew")
        preview_card.grid_columnconfigure(0, weight=1)
        preview_card.grid_rowconfigure(1, weight=1)

        preview_top = ctk.CTkFrame(preview_card, fg_color="transparent")
        preview_top.grid(row=0, column=0, padx=18, pady=(16, 8), sticky="ew")
        preview_top.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            preview_top,
            text="Preview",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        self.preview_mode = ctk.CTkSegmentedButton(
            preview_top,
            values=["Before", "After"],
            width=190,
            command=lambda _value: self._refresh_preview(),
        )
        self.preview_mode.grid(row=0, column=2, sticky="e")
        self.preview_mode.set("Before")

        self.preview_label = ctk.CTkLabel(
            preview_card,
            text="",
            corner_radius=12,
            fg_color=("#DFE8E5", "#0B100F"),
        )
        self.preview_label.grid(
            row=1, column=0, padx=18, pady=8, sticky="nsew")
        self.preview_label.bind("<Configure>", self._preview_resized)

        self.image_info_label = ctk.CTkLabel(
            preview_card,
            text="No image selected",
            anchor="w",
            font=ctk.CTkFont(size=12),
            text_color=("#52615D", "#8FA09B"),
        )
        self.image_info_label.grid(
            row=2, column=0, padx=20, pady=(6, 16), sticky="ew")

        controls = ctk.CTkScrollableFrame(
            workspace, width=310, corner_radius=16)
        controls.grid(row=0, column=1, sticky="nsew")
        controls.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            controls,
            text="Adjustments",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, padx=18, pady=(18, 4), sticky="w")
        ctk.CTkLabel(
            controls,
            text="Tune the finish before processing.",
            font=ctk.CTkFont(size=12),
            text_color=("#52615D", "#8FA09B"),
        ).grid(row=1, column=0, padx=18, pady=(0, 18), sticky="w")

        self.strength_label = ctk.CTkLabel(
            controls, text="Polish strength  ·  78%", anchor="w")
        self.strength_label.grid(row=2, column=0, padx=18, sticky="ew")
        self.strength_slider = ctk.CTkSlider(
            controls,
            from_=0,
            to=100,
            number_of_steps=100,
            command=self._strength_changed,
        )
        self.strength_slider.set(78)
        self.strength_slider.grid(
            row=3, column=0, padx=18, pady=(6, 18), sticky="ew")

        self.texture_label = ctk.CTkLabel(
            controls, text="Texture retention  ·  25%", anchor="w")
        self.texture_label.grid(row=4, column=0, padx=18, sticky="ew")
        self.texture_slider = ctk.CTkSlider(
            controls,
            from_=0,
            to=100,
            number_of_steps=100,
            command=self._texture_changed,
        )
        self.texture_slider.set(25)
        self.texture_slider.grid(
            row=5, column=0, padx=18, pady=(6, 18), sticky="ew")

        self.face_only_var = ctk.BooleanVar(value=True)
        self.fallback_var = ctk.BooleanVar(value=True)
        self.tone_var = ctk.BooleanVar(value=True)
        self.background_var = ctk.StringVar(value="Keep")
        ctk.CTkCheckBox(
            controls,
            text="Limit processing to detected faces",
            variable=self.face_only_var,
            command=self._face_mode_changed,
        ).grid(row=6, column=0, padx=18, pady=8, sticky="w")
        self.fallback_checkbox = ctk.CTkCheckBox(
            controls,
            text="Use skin tones if no face is found",
            variable=self.fallback_var,
        )
        self.fallback_checkbox.grid(
            row=7, column=0, padx=18, pady=8, sticky="w")
        ctk.CTkCheckBox(
            controls,
            text="Apply gentle finishing adjustments",
            variable=self.tone_var,
        ).grid(row=8, column=0, padx=18, pady=8, sticky="w")

        ctk.CTkLabel(
            controls,
            text="Background",
            anchor="w",
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=9, column=0, padx=18, pady=(18, 6), sticky="ew")
        self.background_selector = ctk.CTkSegmentedButton(
            controls,
            values=["Keep", "Remove"],
            variable=self.background_var,
        )
        self.background_selector.grid(row=10, column=0, padx=18, sticky="ew")
        ctk.CTkLabel(
            controls,
            text="Remove creates transparency; save as PNG or WebP.",
            wraplength=270,
            justify="left",
            font=ctk.CTkFont(size=11),
            text_color=("#687873", "#7E918B"),
        ).grid(row=11, column=0, padx=18, pady=(6, 0), sticky="w")

        ctk.CTkFrame(controls, height=1, fg_color=("#CBD8D4", "#2A3733"))\
            .grid(row=12, column=0, padx=18, pady=18, sticky="ew")

        self.process_button = ctk.CTkButton(
            controls,
            text="Polish image",
            height=44,
            corner_radius=10,
            state="disabled",
            command=self.process_image,
        )
        self.process_button.grid(
            row=13, column=0, padx=18, pady=(0, 10), sticky="ew")
        self.save_button = ctk.CTkButton(
            controls,
            text="Save as…",
            height=40,
            corner_radius=10,
            fg_color=("#D9E5E1", "#273530"),
            hover_color=("#C8D8D3", "#32443E"),
            text_color=("#173A31", "#E3F0EC"),
            state="disabled",
            command=self.save_as,
        )
        self.save_button.grid(row=14, column=0, padx=18,
                              pady=(0, 10), sticky="ew")
        ctk.CTkButton(
            controls,
            text="Reset adjustments",
            height=34,
            fg_color="transparent",
            hover_color=("#E3ECE9", "#24302D"),
            text_color=("#275C4E", "#7FE1C6"),
            command=self.reset_adjustments,
        ).grid(row=15, column=0, padx=18, pady=(0, 18), sticky="ew")

        ctk.CTkLabel(
            controls,
            text="Images are processed entirely on this computer.",
            wraplength=270,
            justify="left",
            font=ctk.CTkFont(size=11),
            text_color=("#687873", "#7E918B"),
        ).grid(row=16, column=0, padx=18, pady=(8, 18), sticky="w")

        status = ctk.CTkFrame(self, fg_color="transparent")
        status.grid(row=2, column=0, padx=24, pady=(0, 14), sticky="ew")
        status.grid_columnconfigure(0, weight=1)
        self.status_label = ctk.CTkLabel(
            status,
            text="Ready",
            anchor="w",
            font=ctk.CTkFont(size=12),
        )
        self.status_label.grid(row=0, column=0, sticky="ew")
        self.progress_bar = ctk.CTkProgressBar(
            status, width=190, mode="indeterminate")
        self.progress_bar.grid(row=0, column=1, padx=(16, 0))
        self.progress_bar.grid_remove()

    def _set_empty_preview(self) -> None:
        empty = Image.new("RGB", (920, 620), "#111815")
        draw = ImageDraw.Draw(empty)
        cx, cy = empty.width // 2, empty.height // 2
        draw.rounded_rectangle(
            (cx - 55, cy - 55, cx + 55, cy + 55), radius=24, fill="#173D33")
        draw.line((cx - 24, cy, cx + 24, cy), fill="#67D5B7", width=7)
        draw.line((cx, cy - 24, cx, cy + 24), fill="#67D5B7", width=7)
        draw.text((cx, cy + 82), "Drop an image here or choose Open image",
                  fill="#A6B7B1", anchor="mm")
        self._display_image(empty)

    def _preview_resized(self, _event=None) -> None:
        if self.original_image is not None:
            self.after_idle(self._refresh_preview)

    def _display_image(self, image: Image.Image) -> None:
        available_width = max(320, self.preview_label.winfo_width() - 28)
        available_height = max(260, self.preview_label.winfo_height() - 28)
        display = image.copy()
        if display.mode == "RGBA":
            display = self._composite_transparency(display)
        display.thumbnail((available_width, available_height),
                          Image.Resampling.LANCZOS)
        self.preview_ctk_image = ctk.CTkImage(
            light_image=display.convert("RGB"),
            dark_image=display.convert("RGB"),
            size=display.size,
        )
        self.preview_label.configure(image=self.preview_ctk_image, text="")

    @staticmethod
    def _composite_transparency(image: Image.Image) -> Image.Image:
        tile = 20
        background = Image.new("RGB", image.size, "#D9DEDC")
        draw = ImageDraw.Draw(background)
        for y in range(0, image.height, tile):
            for x in range(0, image.width, tile):
                if (x // tile + y // tile) % 2:
                    draw.rectangle((x, y, x + tile, y + tile), fill="#BFC8C5")
        background.paste(image, mask=image.getchannel("A"))
        return background

    def _refresh_preview(self) -> None:
        selected = self.preview_mode.get()
        if selected == "After" and self.processed_image is not None:
            self._display_image(self.processed_image)
        elif self.original_image is not None:
            self._display_image(self.original_image)

    def _handle_drop(self, event) -> None:
        try:
            paths = self.tk.splitlist(event.data)
        except Exception:
            paths = [event.data.strip("{}")]
        if paths:
            self.load_image(Path(paths[0]))

    def open_image(self) -> None:
        selected = filedialog.askopenfilename(
            title="Open image", filetypes=FILE_TYPES)
        if selected:
            self.load_image(Path(selected))

    def load_image(self, path: Path) -> None:
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            messagebox.showerror(
                APP_NAME, "Please choose a JPG, PNG, WebP, BMP, or TIFF image.")
            return
        try:
            with Image.open(path) as source:
                source.load()
                self.original_image = ImageOps.exif_transpose(source).copy()
        except Exception as exc:
            messagebox.showerror(
                APP_NAME, f"The image could not be opened.\n\n{exc}")
            return

        self.input_path = path
        self.processed_image = None
        self.metadata = None
        self.report = None
        self.preview_mode.set("Before")
        self.process_button.configure(state="normal")
        self.save_button.configure(state="disabled")
        self.image_info_label.configure(
            text=f"{path.name}  ·  {self.original_image.width} × {self.original_image.height}px"
        )
        self.status_label.configure(
            text="Image loaded — adjust settings or select Polish image")
        self._refresh_preview()

    def _strength_changed(self, value: float) -> None:
        self.strength_label.configure(
            text=f"Polish strength  ·  {round(value)}%")

    def _texture_changed(self, value: float) -> None:
        self.texture_label.configure(
            text=f"Texture retention  ·  {round(value)}%")

    def _face_mode_changed(self) -> None:
        self.fallback_checkbox.configure(
            state="normal" if self.face_only_var.get() else "disabled")

    def reset_adjustments(self) -> None:
        self.strength_slider.set(78)
        self.texture_slider.set(25)
        self._strength_changed(78)
        self._texture_changed(25)
        self.face_only_var.set(True)
        self.fallback_var.set(True)
        self.tone_var.set(True)
        self.background_var.set("Keep")
        self._face_mode_changed()

    def process_image(self) -> None:
        if self.input_path is None or self.is_processing:
            return
        settings = PolishSettings(
            strength=self.strength_slider.get() / 100.0,
            texture=self.texture_slider.get() / 100.0,
            face_only=self.face_only_var.get(),
            fallback_to_image=self.fallback_var.get(),
            healthy_tone=self.tone_var.get(),
            remove_background=self.background_var.get() == "Remove",
        )
        self.is_processing = True
        self.process_button.configure(state="disabled", text="Processing…")
        self.save_button.configure(state="disabled")
        self.progress_bar.grid()
        self.progress_bar.start()
        worker = threading.Thread(
            target=self._process_worker,
            args=(self.input_path, settings),
            daemon=True,
        )
        worker.start()

    def _process_worker(self, path: Path, settings: PolishSettings) -> None:
        try:
            image, report, metadata = polish_image(
                path,
                settings=settings,
                progress=lambda message: self.after(
                    0, self.status_label.configure, {"text": message}),
            )
            self.after(0, self._processing_finished, image, report, metadata)
        except Exception as exc:
            self.after(0, self._processing_failed, str(exc))

    def _processing_finished(
        self,
        image: Image.Image,
        report: ProcessingReport,
        metadata: ImageMetadata,
    ) -> None:
        self.processed_image = image
        self.report = report
        self.metadata = metadata
        self.is_processing = False
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        self.process_button.configure(state="normal", text="Polish image")
        self.save_button.configure(state="normal")
        self.preview_mode.set("After")
        self._refresh_preview()

        if report.regions_processed == 0:
            if report.background_removed:
                summary = "No face was detected, so skin polishing was skipped."
            else:
                summary = "No face was detected, so the original image was left unchanged."
        elif report.used_full_image_fallback:
            summary = "Finished using skin-tone fallback (no frontal face was detected)."
        elif report.faces_detected:
            count = report.faces_detected
            summary = f"Finished — {count} face{'s' if count != 1 else ''} detected."
        else:
            summary = "Finished processing visible skin tones."
        if report.background_removed:
            summary = f"{summary.rstrip('.')} — background removed."
        self.status_label.configure(text=summary)

    def _processing_failed(self, error: str) -> None:
        self.is_processing = False
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        self.process_button.configure(state="normal", text="Polish image")
        self.status_label.configure(text="Processing failed")
        messagebox.showerror(
            APP_NAME, f"The image could not be processed.\n\n{error}")

    def save_as(self) -> None:
        if self.processed_image is None or self.input_path is None:
            return
        background_removed = bool(
            self.report and self.report.background_removed)
        if background_removed:
            default_suffix = ".png"
            default_name = f"{self.input_path.stem}_skin_polished_no_background.png"
            save_types = TRANSPARENT_FILE_TYPES
        else:
            default_suffix = self.input_path.suffix.lower()
            default_name = f"{self.input_path.stem}_skin_polished{default_suffix}"
            save_types = FILE_TYPES
        destination = filedialog.asksaveasfilename(
            title="Save polished image",
            initialdir=str(self.input_path.parent),
            initialfile=default_name,
            defaultextension=default_suffix,
            filetypes=save_types,
        )
        if not destination:
            return
        try:
            save_processed_image(self.processed_image,
                                 destination, self.metadata, quality=98)
            self.status_label.configure(text=f"Saved: {destination}")
            messagebox.showinfo(
                APP_NAME, f"Your polished image was saved to:\n\n{destination}")
        except Exception as exc:
            messagebox.showerror(
                APP_NAME, f"The image could not be saved.\n\n{exc}")


def main() -> None:
    enable_windows_dpi_awareness()
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("green")
    app = PolishEditorApp()
    if len(sys.argv) > 1:
        candidate = Path(os.path.abspath(sys.argv[1]))
        if candidate.exists():
            app.after(150, app.load_image, candidate)
    app.mainloop()
