#!/usr/bin/env python3
"""Create a clean venv, install Noema, and verify runtime dependencies."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
import textwrap
import venv
from pathlib import Path


CHECK_CODE = r"""
import inspect
from importlib.metadata import version

import guidance
import llama_cpp
import varname
from guidance import gen, select, substring
from guidance import models

import Noema
from Noema import Bool, Float, Int, Paragraph, Sentence, Subject, Word

assert tuple(map(int, version("guidance").split(".")[:2])) >= (0, 3)
assert tuple(map(int, version("llama-cpp-python").split(".")[:2])) >= (0, 3)
assert tuple(map(int, version("varname").split(".")[:2])) >= (0, 13)

signature = inspect.signature(models.LlamaCpp)
assert "model" in signature.parameters
assert "llama_cpp_kwargs" in signature.parameters

assert callable(gen)
assert callable(select)
assert callable(substring)
assert Word.return_type is str
assert Int.return_type is int
assert Float.return_type is float
assert Bool.return_type is bool
assert Sentence.return_type is str
assert Paragraph.return_type is str
assert str(Sentence(var="previous_step")) == "#PREVIOUS_STEP:"

try:
    Subject.shared()
except Exception as exc:
    assert "llm path" in str(exc)
else:
    raise AssertionError("Subject.shared() should require an initialized model")

print("Noema installation check passed")
print("guidance", version("guidance"))
print("llama-cpp-python", version("llama-cpp-python"))
print("varname", version("varname"))
"""


def run(command: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--keep-venv",
        action="store_true",
        help="Do not delete the temporary virtual environment after the check.",
    )
    parser.add_argument(
        "--venv",
        type=Path,
        help="Virtual environment path. Defaults to a temporary directory.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    venv_dir = args.venv or Path(tempfile.mkdtemp(prefix="noema-install-venv-"))
    created_temp = args.venv is None

    try:
        if not venv_dir.exists() or not any(venv_dir.iterdir()):
            print(f"Creating virtual environment: {venv_dir}", flush=True)
            venv.EnvBuilder(with_pip=True, clear=False).create(venv_dir)

        python = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
        run([str(python), "-m", "pip", "install", str(repo_root)])
        run([str(python), "-c", textwrap.dedent(CHECK_CODE)])
    finally:
        if created_temp and not args.keep_venv:
            shutil.rmtree(venv_dir, ignore_errors=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
