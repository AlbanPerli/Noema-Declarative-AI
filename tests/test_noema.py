
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
        Select,
        SelectOrNone,
        Sentence,
        SemPy,
        Word,
    )
    from Noema.information import Information
    from Noema.llm import close_current_runtime, current_runtime


@unittest.skipUnless(HAS_RUNTIME_DEPS, "guidance and varname are not installed")
class TestNoema(unittest.TestCase):
    def test_public_api_imports(self):
        self.assertIs(Word.return_type, str)
        self.assertIs(Int.return_type, int)
        self.assertIs(Float.return_type, float)
        self.assertIs(Bool.return_type, bool)
        self.assertIs(Sentence.return_type, str)
        self.assertIs(Paragraph.return_type, str)

    def test_llm_defaults_leave_room_for_nested_examples(self):
        llm = LLM("model.gguf")
        self.assertEqual(llm.context_size, 8192)
        self.assertTrue(llm.flash_attn)
        self.assertFalse(llm.enable_monitoring)
        self.assertTrue(llm.safe_native_cleanup)

    def test_text_generators_have_token_limits(self):
        self.assertEqual(Sentence.max_tokens, 36)
        self.assertEqual(Paragraph.max_tokens, 80)
        self.assertLess(Word.max_tokens, Sentence.max_tokens)
        self.assertIsNone(Sentence.regex)
        self.assertIsNone(Paragraph.regex)
        self.assertEqual(Sentence.stop_regex, r"[.!?]")
        self.assertEqual(Paragraph.stop_regex, r"[.!?]")
        self.assertTrue(Sentence.save_stop_text)
        self.assertTrue(Paragraph.save_stop_text)

    def test_text_generation_uses_stop_without_natural_language_regex(self):
        class FakeRuntime:
            def __init__(self):
                self.llm = FakeModel()
                self.verbose = False

            def generation_kwargs(self, max_tokens=None):
                return {"max_tokens": max_tokens, "temperature": 0.1}

            def reasoning_prelude(self):
                return ""

            def append_to_chain(self, value):
                pass

        class FakeModel:
            def __add__(self, value):
                return self

            def __getitem__(self, name):
                if name == "response_stop_text":
                    return "."
                return "A direct sentence"

        fake_runtime = FakeRuntime()

        with patch("Noema.Generator.current_runtime", return_value=fake_runtime):
            with patch("Noema.Generator.gen", return_value="A direct sentence.") as mocked_gen:
                sentence = Sentence("Analyse the comment")

        self.assertEqual(sentence.value, "A direct sentence.")
        self.assertNotIn("regex", mocked_gen.call_args.kwargs)
        self.assertEqual(mocked_gen.call_args.kwargs["stop_regex"], r"[.!?]")
        self.assertEqual(mocked_gen.call_args.kwargs["save_stop_text"], "response_stop_text")

    def test_structured_generation_does_not_pass_empty_stop_list(self):
        class FakeRuntime:
            def __init__(self):
                self.llm = FakeModel()
                self.verbose = False

            def generation_kwargs(self, max_tokens=None):
                return {"max_tokens": max_tokens, "temperature": 0.1}

            def reasoning_prelude(self):
                return ""

            def append_to_chain(self, value):
                pass

        class FakeModel:
            def __add__(self, value):
                return self

            def __getitem__(self, name):
                return "Label"

        fake_runtime = FakeRuntime()

        with patch("Noema.Generator.current_runtime", return_value=fake_runtime):
            with patch("Noema.Generator.gen", return_value="Label") as mocked_gen:
                word = Word("Choose a label")

        self.assertEqual(word.value, "Label")
        self.assertIn("regex", mocked_gen.call_args.kwargs)
        self.assertNotIn("stop", mocked_gen.call_args.kwargs)

    def test_llm_can_disable_reasoning(self):
        llm = LLM("model.gguf", reasoning="off")
        self.assertEqual(llm.reasoning, "off")

    def test_subject_normalizes_reasoning_and_builds_disable_prompt(self):
        from Noema.Subject import Subject

        with patch("Noema.Subject.models.LlamaCpp"):
            subject = Subject("model-reasoning.gguf", reasoning=False)

        self.assertEqual(subject.reasoning, "off")
        self.assertIn("Reasoning mode: off", subject.reasoning_instructions())
        self.assertEqual(subject.reasoning_prelude(), "<think>\n\n</think>\n\n")

    def tearDown(self):
        try:
            close_current_runtime()
        except Exception:
            pass
        try:
            from Noema.Subject import Subject

            Subject.close_shared()
        except Exception:
            pass

    def test_runtime_requires_initial_llm(self):
        with self.assertRaisesRegex(Exception, "declare an LLM"):
            current_runtime()

    def test_generators_can_reference_existing_variables(self):
        reference = Sentence(var="existing_step")
        self.assertEqual(str(reference), "#EXISTING_STEP:")

    def test_information_verbose_omits_missing_hint(self):
        class FakeRuntime:
            def __init__(self):
                self.llm = ""
                self.verbose = True
                self.chain = []

            def append_to_chain(self, value):
                self.chain.append(value)

        with patch("Noema.information.current_runtime", return_value=FakeRuntime()):
            with patch("builtins.print") as mocked_print:
                info = Information("hello")

        self.assertEqual(info.noema, "hello")
        printed = mocked_print.call_args.args[0]
        self.assertNotIn("(None)", printed)

    def test_information_can_be_called_without_assignment(self):
        class FakeRuntime:
            def __init__(self):
                self.llm = ""
                self.verbose = False
                self.chain = []

            def append_to_chain(self, value):
                self.chain.append(value)

        fake_runtime = FakeRuntime()

        with patch("Noema.information.current_runtime", return_value=fake_runtime):
            Information("hello")

        self.assertEqual(fake_runtime.chain[0]["value"], "hello")
        self.assertIn("#INFORMATION_", fake_runtime.llm)

    def test_select_rejects_empty_options_before_runtime_lookup(self):
        with self.assertRaisesRegex(ValueError, "at least one option"):
            Select("Choose", options=[])

    def test_select_or_none_does_not_mutate_options(self):
        class FakeRuntime:
            def __init__(self):
                self.llm = FakeModel()
                self.verbose = False
                self.chain = []

            def append_to_chain(self, value):
                self.chain.append(value)

        class FakeModel:
            def __add__(self, value):
                return self

            def __getitem__(self, name):
                return "None"

        options = ["alpha"]

        with patch("Noema.selectors.current_runtime", return_value=FakeRuntime()):
            with patch("Noema.selectors.select", return_value="selected"):
                choice = SelectOrNone("Choose optionally", options=options)

        self.assertIsNone(choice.value)
        self.assertEqual(options, ["alpha"])

    def test_code_generator_does_not_print_outside_verbose_mode(self):
        from Noema.code_gen import CodeGenerator

        class FakeRuntime:
            def __init__(self):
                self.llm = FakeModel()
                self.verbose = False

            def generation_kwargs(self, max_tokens=None):
                return {"max_tokens": max_tokens}

            def reasoning_prelude(self):
                return ""

        class FakeModel:
            def __add__(self, value):
                return self

            def __getitem__(self, name):
                return "print('hello')"

        with patch("Noema.code_gen.current_runtime", return_value=FakeRuntime()):
            with patch("Noema.code_gen.gen", return_value="generated"):
                with patch("builtins.print") as mocked_print:
                    code = CodeGenerator("Write hello")

        self.assertEqual(code.value, "print('hello')")
        mocked_print.assert_not_called()

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

    def test_noesis_prompt_uses_neutral_instruction_format(self):
        from Noema.noesis_wrapper import NoesisBuilder

        prompt = NoesisBuilder("You are helpful.", []).build()

        self.assertIn("NOEMA INSTRUCTIONS:", prompt)
        self.assertNotIn("[INST]", prompt)
        self.assertNotIn("[/INST]", prompt)

    def test_noesis_prompt_can_disable_reasoning(self):
        from Noema.noesis_wrapper import NoesisBuilder

        prompt = NoesisBuilder("You are helpful.", [], "Reasoning mode: off.").build()

        self.assertIn("Reasoning mode: off.", prompt)

    def test_decorator_can_declare_llm_path(self):
        class FakeRuntime:
            def __init__(self):
                self.llm = ""
                self.entered = []
                self.exited = []

            def enter_function(self, *args):
                self.entered.append(args)

            def exit_function(self, value):
                self.exited.append(value)

            def reasoning_instructions(self):
                return ""

        fake_runtime = FakeRuntime()

        with patch("Noema.llm.Subject.configure_shared", return_value=fake_runtime) as configure_shared:
            with patch("Noema.llm._install_fast_exit_exception_hook"):
                with patch("Noema.llm._install_fast_exit_shutdown_hook"):

                    @Noema("model-a.gguf", context_size=2048)
                    def declared_model_task():
                        """Do the task with the declared model."""
                        return "ok"

                    self.assertEqual(declared_model_task(), "ok")
            configure_shared.assert_called_once_with(
                "model-a.gguf",
                context_size=2048,
                verbose=True,
                write_graph=False,
                n_gpu_layers=-1,
                flash_attn=True,
                enable_monitoring=False,
                suppress_startup_logs=True,
                safe_native_cleanup=True,
                temperature=0.1,
                top_p=0.8,
                top_k=40,
                min_p=None,
                repetition_penalty=1.25,
                reasoning="auto",
            )
            self.assertEqual(len(fake_runtime.entered), 1)
            self.assertEqual(fake_runtime.exited, ["ok"])

    def test_decorator_can_declare_llm_object(self):
        class FakeRuntime:
            def __init__(self):
                self.llm = ""
                self.entered = []
                self.exited = []

            def enter_function(self, *args):
                self.entered.append(args)

            def exit_function(self, value):
                self.exited.append(value)

            def reasoning_instructions(self):
                return ""

        fake_runtime = FakeRuntime()
        llm = LLM("model-b.gguf", context_size=1024, verbose=True)

        with patch("Noema.llm.Subject.configure_shared", return_value=fake_runtime) as configure_shared:
            with patch("Noema.llm._install_fast_exit_exception_hook"):
                with patch("Noema.llm._install_fast_exit_shutdown_hook"):

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
            flash_attn=True,
            enable_monitoring=False,
            suppress_startup_logs=True,
            safe_native_cleanup=True,
            temperature=0.1,
            top_p=0.8,
            top_k=40,
            min_p=None,
            repetition_penalty=1.25,
            reasoning="auto",
        )
        self.assertEqual(len(fake_runtime.entered), 1)
        self.assertEqual(fake_runtime.exited, ["ok"])

    def test_llm_fast_exit_installs_exception_hook_before_runtime_and_shutdown_hook_after(self):
        fake_runtime = type("FakeRuntime", (), {"llm": ""})()
        llm = LLM("model-c.gguf", fast_exit=True)
        calls = []

        def configure_shared(*args, **kwargs):
            calls.append("runtime")
            return fake_runtime

        def install_exception_hook():
            calls.append("exception")

        def install_shutdown_hook():
            calls.append("shutdown")

        with patch("Noema.llm.Subject.configure_shared", side_effect=configure_shared):
            with patch("Noema.llm._install_fast_exit_exception_hook", side_effect=install_exception_hook):
                with patch("Noema.llm._install_fast_exit_shutdown_hook", side_effect=install_shutdown_hook):
                    self.assertIs(llm.activate(), fake_runtime)

        self.assertEqual(calls, ["exception", "runtime", "shutdown"])

    def test_llm_fast_exit_does_not_install_shutdown_hook_when_runtime_fails(self):
        llm = LLM("model-e.gguf", fast_exit=True)

        with patch("Noema.llm.Subject.configure_shared", side_effect=RuntimeError("failed")):
            with patch("Noema.llm._install_fast_exit_exception_hook") as install_exception_hook:
                with patch("Noema.llm._install_fast_exit_shutdown_hook") as install_shutdown_hook:
                    with self.assertRaisesRegex(RuntimeError, "failed"):
                        llm.activate()

        install_exception_hook.assert_called_once_with()
        install_shutdown_hook.assert_not_called()

    def test_llm_fast_exit_can_be_disabled(self):
        fake_runtime = type("FakeRuntime", (), {"llm": ""})()
        llm = LLM("model-f.gguf", fast_exit=False)

        with patch("Noema.llm.Subject.configure_shared", return_value=fake_runtime):
            with patch("Noema.llm._install_fast_exit_exception_hook") as install_exception_hook:
                with patch("Noema.llm._install_fast_exit_shutdown_hook") as install_shutdown_hook:
                    self.assertIs(llm.activate(), fake_runtime)

        install_exception_hook.assert_not_called()
        install_shutdown_hook.assert_not_called()

    def test_subject_initialization_error_mentions_llama_cpp_context(self):
        from Noema.Subject import Subject

        with patch("Noema.Subject.models.LlamaCpp", side_effect=ValueError("Failed to create llama_context")):
            with self.assertRaisesRegex(RuntimeError, "flash_attn: True"):
                Subject("model-d.gguf", n_gpu_layers=-1)

    def test_subject_passes_flash_attention_to_llama_cpp(self):
        from Noema.Subject import Subject

        with patch("Noema.Subject.models.LlamaCpp") as llama_cpp:
            Subject("model-g.gguf", flash_attn=False)

        self.assertFalse(llama_cpp.call_args.kwargs["flash_attn"])

    def test_subject_passes_sampling_params_to_guidance(self):
        from Noema.Subject import Subject

        with patch("Noema.Subject.models.LlamaCpp") as llama_cpp:
            subject = Subject(
                "model-i.gguf",
                temperature=0.1,
                top_p=0.75,
                top_k=20,
                repetition_penalty=1.25,
            )

        self.assertEqual(subject.generation_kwargs(12), {"max_tokens": 12, "temperature": 0.1})
        self.assertEqual(
            llama_cpp.call_args.kwargs["sampling_params"],
            {"top_p": 0.75, "top_k": 20, "repetition_penalty": 1.25},
        )

    def test_subject_close_skips_native_cleanup_by_default(self):
        from Noema.Subject import Subject

        with patch("Noema.Subject.models.LlamaCpp") as llama_cpp:
            subject = Subject("model-h.gguf")

        subject.close()

        llama_cpp.return_value.close.assert_not_called()
        self.assertIsNone(subject.llm)

    def test_comment_classifier_keeps_modern_model_defaults(self):
        with open("examples/comment_classifier.py", encoding="utf-8") as example:
            content = example.read()

        self.assertNotIn("flash_attn=False", content)
        self.assertNotIn("enable_monitoring=True", content)

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
