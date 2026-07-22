
import unittest
import importlib.util
from unittest.mock import patch

try:
    import guidance  # noqa: F401

    HAS_RUNTIME_DEPS = importlib.util.find_spec("varname") is not None
except Exception:
    HAS_RUNTIME_DEPS = False

if HAS_RUNTIME_DEPS:
    from Noema import (
        Bool,
        Float,
        Int,
        ListOf,
        Noema,
        LLM,
        Paragraph,
        Sentence,
        SemPy,
        Subject,
        Word,
    )


@unittest.skipUnless(HAS_RUNTIME_DEPS, "guidance and varname are not installed")
class TestNoema(unittest.TestCase):
    def test_public_api_imports(self):
        self.assertIs(Word.return_type, str)
        self.assertIs(Int.return_type, int)
        self.assertIs(Float.return_type, float)
        self.assertIs(Bool.return_type, bool)
        self.assertIs(Sentence.return_type, str)
        self.assertIs(Paragraph.return_type, str)

    def test_subject_requires_initial_model(self):
        with self.assertRaisesRegex(Exception, "llm path"):
            Subject.shared()

    def test_generators_can_reference_existing_variables(self):
        reference = Sentence(var="existing_step")
        self.assertEqual(str(reference), "#EXISTING_STEP:")

    def test_listof_parses_bulleted_and_numbered_lines(self):
        response = "1. Identify the word.\n- Count each letter.\n* Return the counts.\n"
        self.assertEqual(
            ListOf._parse_lines(response),
            ["Identify the word.", "Count each letter.", "Return the counts."],
        )
        self.assertEqual(ListOf._infer_count("List 4 improvements"), 4)

    def test_decorator_requires_docstring(self):
        def missing_docstring():
            return None

        wrapped = Noema(missing_docstring)
        with self.assertRaisesRegex(ValueError, "docstring"):
            wrapped()

    def test_decorator_can_declare_llm_path(self):
        class FakeSubject:
            def __init__(self):
                self.llm = ""
                self.entered = []
                self.exited = []

            def enter_function(self, *args):
                self.entered.append(args)

            def exit_function(self, value):
                self.exited.append(value)

        fake_subject = FakeSubject()

        with patch("Noema.llm.Subject.configure_shared", return_value=fake_subject) as configure_shared:
            with patch("Noema.noesis_wrapper.Subject.shared", return_value=fake_subject) as shared:

                @Noema("model-a.gguf", context_size=2048)
                def declared_model_task():
                    """Do the task with the declared model."""
                    return "ok"

                self.assertEqual(declared_model_task(), "ok")
            configure_shared.assert_called_once_with(
                "model-a.gguf",
                context_size=2048,
                verbose=False,
                write_graph=False,
                n_gpu_layers=-1,
                enable_monitoring=None,
                suppress_startup_logs=None,
            )
            shared.assert_called_once_with()
            self.assertEqual(len(fake_subject.entered), 1)
            self.assertEqual(fake_subject.exited, ["ok"])

    def test_decorator_can_declare_llm_object(self):
        class FakeSubject:
            def __init__(self):
                self.llm = ""
                self.entered = []
                self.exited = []

            def enter_function(self, *args):
                self.entered.append(args)

            def exit_function(self, value):
                self.exited.append(value)

        fake_subject = FakeSubject()
        llm = LLM("model-b.gguf", context_size=1024, verbose=True)

        with patch("Noema.llm.Subject.configure_shared", return_value=fake_subject) as configure_shared:
            with patch("Noema.noesis_wrapper.Subject.shared", return_value=fake_subject):

                @Noema(llm)
                def declared_llm_task():
                    """Do the task with the declared LLM."""
                    return "ok"

                self.assertEqual(declared_llm_task(), "ok")

        configure_shared.assert_called_once_with(
            "model-b.gguf",
            context_size=1024,
            verbose=True,
            write_graph=False,
            n_gpu_layers=-1,
            enable_monitoring=None,
            suppress_startup_logs=None,
        )
        self.assertEqual(len(fake_subject.entered), 1)
        self.assertEqual(fake_subject.exited, ["ok"])

    def test_semantic_python_letter_count_fallback(self):
        sempy = SemPy("Count the occurrence of letters in a word")
        self.assertEqual(
            sempy._deterministic_fallback("strawberry"),
            {"s": 1, "t": 1, "r": 3, "a": 1, "w": 1, "b": 1, "e": 1, "y": 1},
        )
    
    # Test Horizon creation
    # Test var creation and storage
    # Test Sentence creation
    # Test Int creation
    # Test Float creation
    # Test Bool creation
    # Test Select creation
    # Test IF/ELSE
    # Test Sentence creation from var
    # Test Int creation from var
    # Test Float creation from var
    # Test Bool creation from var
    # Test Select creation from var
    # Test IF/ELSE from var
    # Ajouter un SelectOneOrMore
    
if __name__ == '__main__':
    unittest.main()
