"""Stdlib-only test suite. Run:  python -m unittest discover tests -v"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Make the repo root importable when tests run from any cwd.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# anthropic may not be installed in CI's lint matrix; skip the suite if not.
try:
    import blender_gen as bg  # noqa: E402
except ModuleNotFoundError as exc:  # pragma: no cover — CI without anthropic
    raise unittest.SkipTest(f"blender_gen import failed ({exc})") from exc

import agent_seo  # noqa: E402


class TestAutoModel(unittest.TestCase):
    """_pick_model heuristic across providers."""

    def test_short_edit_goes_haiku_on_anthropic(self):
        self.assertEqual(bg._pick_model("add a torus", "claude-opus-4-7"),
                         "claude-haiku-4-5-20251001")

    def test_short_edit_goes_chat_on_deepseek(self):
        self.assertEqual(bg._pick_model("add a torus", "deepseek-chat", "deepseek"),
                         "deepseek-chat")

    def test_long_scene_goes_opus_on_anthropic(self):
        long = "build " + "foo " * 25
        self.assertEqual(bg._pick_model(long, "claude-sonnet-4-6"), "claude-opus-4-7")

    def test_long_scene_goes_pro_on_gemini(self):
        long = "build " + "foo " * 25
        self.assertEqual(bg._pick_model(long, "gemini-2.5-flash", "gemini"), "gemini-2.5-pro")

    def test_medium_prompt_keeps_default(self):
        self.assertEqual(bg._pick_model("spinning gold torus on pedestal", "x"), "x")


class TestProviders(unittest.TestCase):
    """Provider table structural invariants."""

    def test_each_provider_has_default_in_its_models(self):
        for prov, cfg in bg.PROVIDERS.items():
            self.assertIn(cfg["default_model"], cfg["models"], f"{prov} default missing")

    def test_each_provider_declares_key_env(self):
        for prov, cfg in bg.PROVIDERS.items():
            self.assertTrue(cfg.get("key_env"), f"{prov} missing key_env")

    def test_all_models_have_pricing(self):
        for cfg in bg.PROVIDERS.values():
            for m in cfg["models"]:
                self.assertIn(m, bg.PRICING, f"PRICING missing {m}")


class TestCostEstimate(unittest.TestCase):
    def test_estimate_cost_unknown_model_returns_none(self):
        class U:
            input_tokens = 10
            output_tokens = 5
            cache_read_input_tokens = 0
            cache_creation_input_tokens = 0
        self.assertIsNone(bg._estimate_cost(U(), "nonexistent-model"))

    def test_estimate_cost_opus_known_values(self):
        class U:
            input_tokens = 1_000_000
            output_tokens = 1_000_000
            cache_read_input_tokens = 0
            cache_creation_input_tokens = 0
        # opus rates: (15, 75, 1.5, 18.75) -> 15 + 75 = 90.0
        self.assertAlmostEqual(bg._estimate_cost(U(), "claude-opus-4-7"), 90.0, places=3)


class TestHistoryRoundtrip(unittest.TestCase):
    def test_log_and_read_jsonl(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "h.jsonl"
            bg._log_history(str(p), "m", "prompt-1", "script-1", rating=5)
            bg._log_history(str(p), "m", "prompt-2", "script-2", rating=None)
            rows = bg._read_history_jsonl(str(p))
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["rating"], 5)
            self.assertNotIn("rating", rows[1])


class TestSceneDiff(unittest.TestCase):
    def test_object_names_extracted_safely(self):
        s = json.dumps({"objects": [{"name": "Cube"}, {"name": "Lamp"}, {}]})
        self.assertEqual(bg._scene_object_names(s), {"Cube", "Lamp"})

    def test_object_names_empty_on_bad_input(self):
        self.assertEqual(bg._scene_object_names("not json"), set())
        self.assertEqual(bg._scene_object_names("[]"), set())


class TestAgentSEO(unittest.TestCase):
    def test_renders_valid_agents_json(self):
        m = agent_seo.AgentManifest(
            name="t", human="T", summary="S",
            repository="https://example.com/x", entry_point="e.py",
            capabilities=[agent_seo.Capability(id="c", summary="s", command="t c")],
        )
        payload = json.loads(agent_seo.render_agents_json(m))
        self.assertEqual(payload["schema_version"], "v1")
        self.assertEqual(payload["runtime"]["native_extensions"], False)
        self.assertEqual(payload["capabilities"][0]["id"], "c")

    def test_write_all_creates_four_files(self):
        m = agent_seo.AgentManifest(name="t", human="T", summary="S",
                                     repository="https://example.com/x", entry_point="e.py")
        with tempfile.TemporaryDirectory() as d:
            written = agent_seo.write_all(m, d)
            names = [p.name for p in written]
            self.assertIn("llms.txt", names)
            self.assertIn("llms-full.txt", names)
            self.assertIn("AGENTS.md", names)
            self.assertTrue((Path(d) / ".well-known" / "agents.json").exists())


class TestDocsInSync(unittest.TestCase):
    """Guard against docs drifting out of sync with the CLI surface."""

    def test_agents_json_lists_all_providers(self):
        p = Path(__file__).resolve().parent.parent / ".well-known" / "agents.json"
        payload = json.loads(p.read_text())
        self.assertEqual(payload["schema_version"], "v1")

    def test_version_stamped_everywhere(self):
        root = Path(__file__).resolve().parent.parent
        pyproj = (root / "pyproject.toml").read_text()
        self.assertIn(bg.__version__, pyproj,
                      f"pyproject.toml version != blender_gen __version__ ({bg.__version__})")


if __name__ == "__main__":
    unittest.main()
