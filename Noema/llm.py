from dataclasses import dataclass, field
from pathlib import Path

from .Subject import Subject


@dataclass(frozen=True)
class LLM:
    model_path: str | Path
    context_size: int = 512 * 8
    verbose: bool = False
    write_graph: bool = False
    n_gpu_layers: int = -1
    enable_monitoring: bool | None = None
    suppress_startup_logs: bool | None = None
    llama_cpp_kwargs: dict = field(default_factory=dict)

    def activate(self):
        return Subject.configure_shared(
            self.model_path,
            context_size=self.context_size,
            verbose=self.verbose,
            write_graph=self.write_graph,
            n_gpu_layers=self.n_gpu_layers,
            enable_monitoring=self.enable_monitoring,
            suppress_startup_logs=self.suppress_startup_logs,
            **self.llama_cpp_kwargs,
        )
