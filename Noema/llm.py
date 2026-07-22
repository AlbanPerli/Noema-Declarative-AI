import atexit
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .Subject import Subject


_current_runtime = None
_fast_exit_installed = False
_fast_exit_code = 0
_previous_excepthook = None


def current_runtime():
    if _current_runtime is None:
        raise Exception("You must declare an LLM with @Noema(llm) before generating values.")
    return _current_runtime


def close_current_runtime():
    global _current_runtime
    if _current_runtime is not None:
        try:
            if hasattr(_current_runtime, "close"):
                _current_runtime.close()
        finally:
            _current_runtime = None


def _install_fast_exit_hook():
    global _fast_exit_installed, _previous_excepthook
    if _fast_exit_installed:
        return

    _previous_excepthook = sys.excepthook

    def record_unhandled_exception(exc_type, exc_value, traceback):
        global _fast_exit_code
        _fast_exit_code = 1
        _previous_excepthook(exc_type, exc_value, traceback)

    def fast_exit():
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(_fast_exit_code)

    sys.excepthook = record_unhandled_exception
    atexit.register(fast_exit)
    _fast_exit_installed = True


@dataclass(frozen=True)
class LLM:
    model_path: str | Path
    context_size: int = 512 * 8
    verbose: bool = False
    write_graph: bool = False
    n_gpu_layers: int = -1
    enable_monitoring: bool | None = None
    suppress_startup_logs: bool | None = None
    fast_exit: bool = False
    llama_cpp_kwargs: dict = field(default_factory=dict)

    def activate(self):
        global _current_runtime
        if self.fast_exit:
            _install_fast_exit_hook()

        _current_runtime = Subject.configure_shared(
            self.model_path,
            context_size=self.context_size,
            verbose=self.verbose,
            write_graph=self.write_graph,
            n_gpu_layers=self.n_gpu_layers,
            enable_monitoring=self.enable_monitoring,
            suppress_startup_logs=self.suppress_startup_logs,
            **self.llama_cpp_kwargs,
        )
        return _current_runtime
