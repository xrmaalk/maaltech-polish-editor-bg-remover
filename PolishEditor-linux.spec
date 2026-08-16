# -*- mode: python ; coding: utf-8 -*-
# Linux / ChromeOS (Crostini) build of MAALTECH Polish Editor
from pathlib import Path

from PyInstaller.utils.hooks import (
    collect_all,
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
    copy_metadata,
)

project_root = Path(SPECPATH)

# Data files
datas = collect_data_files("customtkinter")
datas += collect_data_files("tkinterdnd2")
datas += collect_data_files("onnxruntime")
datas += copy_metadata("pymatting")

# Include both icon formats (PNG is preferred on Linux)
datas += [(str(project_root / "assets" / "maaltech_mascot_icon.png"), "assets")]
datas += [(str(project_root / "assets" / "app.ico"), "assets")]

binaries = collect_dynamic_libs("onnxruntime")

# Full rembg collection (same rationale as Windows)
rembg_datas, rembg_binaries, rembg_hiddenimports = collect_all("rembg")
rembg_hiddenimports = [
    name
    for name in rembg_hiddenimports
    if not name.startswith(("rembg.cli", "rembg.commands"))
]
datas += rembg_datas
binaries += rembg_binaries

hiddenimports = [
    "PIL._tkinter_finder",
    "jsonschema",
    "onnxruntime",
    "pooch",
    "pymatting",
    "pymatting.alpha.estimate_alpha_cf",
    "pymatting.foreground.estimate_foreground_ml",
    "pymatting.util.util",
    "rembg",
    "rembg.bg",
    "rembg.session_factory",
    "rembg.sessions",
    "rembg.sessions.base",
    "rembg.sessions.u2net_human_seg",
    "scipy",
    "scipy.ndimage",
    "skimage",
    "skimage.morphology",
    "tqdm",
]
hiddenimports += rembg_hiddenimports
hiddenimports += collect_submodules("scipy._external.array_api_compat")

a = Analysis(
    [str(project_root / "Polish_Editor.py")],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest"],
    noarchive=False,
    module_collection_mode={"pymatting": "py"},
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="PolishEditor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                    # safer with ONNX Runtime native libs
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                # no terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Linux desktops prefer the .desktop Icon= entry; this is a fallback
    icon=str(project_root / "assets" / "maaltech_mascot_icon.png"),
)