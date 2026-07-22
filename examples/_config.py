import os
import sys
from pathlib import Path

from Noema import Subject


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _env_flag(name, default):
    value = os.environ.get(name, default)
    return value not in {"0", "false", "False"}


def model_path(default_filename):
    configured_path = os.environ.get("NOEMA_MODEL_PATH")
    if configured_path:
        path = Path(configured_path).expanduser()
        if not path.is_absolute():
            path = PROJECT_ROOT / path
    else:
        default_path = Path(default_filename).expanduser()
        if default_path.suffix == ".gguf" and (default_path.is_absolute() or default_path.parent != Path(".")):
            path = default_path if default_path.is_absolute() else PROJECT_ROOT / default_path
        else:
            model_dir = Path(os.environ.get("NOEMA_MODEL_DIR", "../Models")).expanduser()
            if not model_dir.is_absolute():
                model_dir = PROJECT_ROOT / model_dir
            path = model_dir / default_filename

    if not path.exists():
        raise SystemExit(
            "No GGUF model found for this example.\n"
            f"Expected: {path}\n"
            "Set NOEMA_MODEL_PATH to a .gguf file, or NOEMA_MODEL_DIR to a directory "
            "containing the example model."
        )

    return path


def create_subject(default_filename, **kwargs):
    verbose = _env_flag("NOEMA_VERBOSE", "1")
    kwargs.setdefault("context_size", int(os.environ.get("NOEMA_CONTEXT_SIZE", "4096")))
    kwargs.setdefault("n_gpu_layers", int(os.environ.get("NOEMA_N_GPU_LAYERS", "-1")))
    kwargs.setdefault("enable_monitoring", _env_flag("NOEMA_ENABLE_MONITORING", "0"))
    kwargs.setdefault("suppress_startup_logs", _env_flag("NOEMA_SUPPRESS_STARTUP_LOGS", "1"))
    return Subject(str(model_path(default_filename)), verbose=verbose, **kwargs)


def run_example(main):
    try:
        main()
    except BaseException:
        Subject.close_shared()
        raise
    else:
        Subject.close_shared()
        sys.stdout.flush()
        sys.stderr.flush()
        if _env_flag("NOEMA_EXAMPLE_FAST_EXIT", "1"):
            os._exit(0)
