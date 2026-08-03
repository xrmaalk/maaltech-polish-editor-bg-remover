# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import (
    collect_all,
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
    copy_metadata,
)


project_root = Path(SPECPATH)
datas = collect_data_files("customtkinter")
datas += collect_data_files("tkinterdnd2")
datas += collect_data_files("onnxruntime")
datas += copy_metadata("pymatting")
datas += [(str(project_root / "assets" / "app.ico"), "assets")]
binaries = collect_dynamic_libs("onnxruntime")

# Rembg selects its model session dynamically. Static import analysis alone can
# omit the top-level package or session modules from a one-file executable, so
# collect the complete package, including distribution metadata.
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
# SciPy 1.18 imports this NumPy-compatibility namespace dynamically. Its nested
# fft/linalg modules are otherwise missed by PyInstaller's static analysis.
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
    # PyMatting uses Numba functions with cache=True. Keeping these modules as
    # real .py files gives Numba a valid source locator inside a one-file build.
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
    # Avoid compressing ONNX Runtime native libraries; this is more reliable on Windows.
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[str(project_root / "assets" / "app.ico")],
    version=str(project_root / "version_info.txt"),
)
