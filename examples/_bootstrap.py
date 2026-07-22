import os
import sys
import warnings
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VENV_RELATIVE_PYTHON = "Scripts/python.exe" if os.name == "nt" else "bin/python"
VENV_CANDIDATES = [
    PROJECT_ROOT / ".venv-metal" / VENV_RELATIVE_PYTHON,
    PROJECT_ROOT / ".venv" / VENV_RELATIVE_PYTHON,
]


def _same_executable(left, right):
    return Path(left).resolve() == Path(right).resolve()


def _preferred_python():
    configured_python = os.environ.get("NOEMA_PYTHON")
    if configured_python:
        configured_path = Path(configured_python).expanduser()
        if configured_path.exists():
            return configured_path

    for candidate in VENV_CANDIDATES:
        if candidate.exists():
            return candidate

    return None


TARGET_PYTHON = _preferred_python()


if (
    sys.argv
    and sys.argv[0].endswith(".py")
    and TARGET_PYTHON is not None
    and not _same_executable(sys.executable, TARGET_PYTHON)
    and os.environ.get("NOEMA_DISABLE_VENV_REEXEC") != "1"
):
    os.execv(str(TARGET_PYTHON), [str(TARGET_PYTHON), *sys.argv])

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

warnings.filterwarnings(
    "ignore",
    message=r"Chat template .*",
    category=UserWarning,
    module=r"guidance\.models\._engine\._tokenizer",
)
