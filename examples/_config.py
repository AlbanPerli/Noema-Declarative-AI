import os
from pathlib import Path


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


def env_verbose(default="1"):
    return _env_flag("NOEMA_VERBOSE", default)


def env_context_size(default="4096"):
    return int(os.environ.get("NOEMA_CONTEXT_SIZE", default))


def env_n_gpu_layers(default="-1"):
    return int(os.environ.get("NOEMA_N_GPU_LAYERS", default))


def env_enable_monitoring(default="0"):
    return _env_flag("NOEMA_ENABLE_MONITORING", default)


def env_suppress_startup_logs(default="1"):
    return _env_flag("NOEMA_SUPPRESS_STARTUP_LOGS", default)


def env_fast_exit(default="1"):
    return _env_flag("NOEMA_FAST_EXIT", default)
