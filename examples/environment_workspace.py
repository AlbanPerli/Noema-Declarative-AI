import _bootstrap
from Noema import *
from _config import (
    env_context_size,
    env_fast_exit,
    env_n_gpu_layers,
    env_suppress_startup_logs,
    env_verbose,
    model_path,
)


llm = LLM(
    model_path("/Users/al/Documents/IA/Models/LLM/gemma4/gemma-4-E4B-it-Q4_K_M.gguf"),
    context_size=env_context_size(),
    n_gpu_layers=env_n_gpu_layers(),
    suppress_startup_logs=env_suppress_startup_logs(),
    verbose=env_verbose(),
    fast_exit=env_fast_exit(),
    reasoning="off",
)


class CommentWorkspace(NoemaEnvironment):
    comments = Memory(default_factory=list)
    labels = Memory(default_factory=dict)
    tone = Visible("concise and factual")

    @visible
    @property
    def comment_count(self):
        return len(self.comments)

    @tool
    def add_comment(self, comment: str):
        self.comments.append(comment)
        return {"count": len(self.comments)}

    @tool
    def label_comment(self, comment: str, label: str):
        self.labels[comment] = label
        return self.labels

    @tool
    def known_labels(self):
        return sorted(set(self.labels.values()))


def main():
    workspace = CommentWorkspace(llm=llm)
    answer = workspace(
        """
        Store this comment, classify it, and answer with a short synthesis:
        This llm is very good!
        """,
        max_tokens=80,
    )
    print(answer)


if __name__ == "__main__":
    main()
