import os
import sys
import warnings
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON = PROJECT_ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _same_executable(left, right):
    return Path(left).absolute() == Path(right).absolute()


if (
    sys.argv
    and sys.argv[0].endswith(".py")
    and VENV_PYTHON.exists()
    and not _same_executable(sys.executable, VENV_PYTHON)
    and os.environ.get("NOEMA_DISABLE_VENV_REEXEC") != "1"
):
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), *sys.argv])

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

warnings.filterwarnings(
    "ignore",
    message=r"Chat template .*",
    category=UserWarning,
    module=r"guidance\.models\._engine\._tokenizer",
)
