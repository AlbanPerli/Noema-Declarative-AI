import atexit
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .Subject import Subject


_current_runtime = None
_fast_exit_exception_hook_installed = False
_fast_exit_shutdown_hook_installed = False
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


def _fast_exit():
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(_fast_exit_code)


def _install_fast_exit_exception_hook():
    global _fast_exit_exception_hook_installed, _previous_excepthook
    if _fast_exit_exception_hook_installed:
        return

    _previous_excepthook = sys.excepthook

    def record_unhandled_exception(exc_type, exc_value, traceback):
        global _fast_exit_code
        _fast_exit_code = 1
        _previous_excepthook(exc_type, exc_value, traceback)
        _fast_exit()

    sys.excepthook = record_unhandled_exception
    _fast_exit_exception_hook_installed = True


def _install_fast_exit_shutdown_hook():
    global _fast_exit_shutdown_hook_installed
    if _fast_exit_shutdown_hook_installed:
        return

    atexit.register(_fast_exit)
    _fast_exit_shutdown_hook_installed = True


@dataclass(frozen=True)
class LLM:
    model_path: str | Path
    context_size: int = 512 * 16
    verbose: bool = True
    write_graph: bool = False
    n_gpu_layers: int = -1
    flash_attn: bool = True
    enable_monitoring: bool | None = False
    suppress_startup_logs: bool | None = True
    safe_native_cleanup: bool = True
    fast_exit: bool = True
    temperature: float | None = 0.1
    top_p: float | None = 0.8
    top_k: int | None = 40
    min_p: float | None = None
    repetition_penalty: float | None = 1.25
    reasoning: bool | str | None = "auto"
    llama_cpp_kwargs: dict = field(default_factory=dict)

    def activate(self):
        global _current_runtime
        if self.fast_exit:
            _install_fast_exit_exception_hook()

        _current_runtime = Subject.configure_shared(
            self.model_path,
            context_size=self.context_size,
            verbose=self.verbose,
            write_graph=self.write_graph,
            n_gpu_layers=self.n_gpu_layers,
            flash_attn=self.flash_attn,
            enable_monitoring=self.enable_monitoring,
            suppress_startup_logs=self.suppress_startup_logs,
            safe_native_cleanup=self.safe_native_cleanup,
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            min_p=self.min_p,
            repetition_penalty=self.repetition_penalty,
            reasoning=self.reasoning,
            **self.llama_cpp_kwargs,
        )
        if self.fast_exit:
            _install_fast_exit_shutdown_hook()
        return _current_runtime
