"""Polish Editor desktop application entry point."""

import sys
from pathlib import Path

def run_background_self_test() -> int:
    """Verify that the frozen EXE contains the complete rembg stack."""
    log_path = Path.cwd() / "PolishEditor_background_self_test.log"
    try:
        from src.processing import background_dependency_report

        report = background_dependency_report()
        if log_path.exists():
            log_path.unlink()
        print(report)
        return 0
    except Exception as exc:
        message = f"{type(exc).__name__}: {exc}"
        try:
            log_path.write_text(message, encoding="utf-8")
        except OSError:
            pass
        print(message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    if "--self-test-background" in sys.argv:
        raise SystemExit(run_background_self_test())

    # Import the GUI only for a normal launch. This lets the frozen-build
    # self-test validate rembg without requiring a display or Tcl/Tk startup.
    from src.app import main

    main()
