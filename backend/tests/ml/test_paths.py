"""The repo-root depth used to be hard-coded in five modules; pin it in one test instead.

These assert *anchors*, not existence. ``.local/`` is untracked and absent on a fresh
clone, so asserting that MODELS_DIR exists would fail CI for the wrong reason.
"""

from pathlib import Path

import pytest

from ml import paths


class TestAnchors:
    def test_repo_root_is_the_directory_holding_backend(self):
        assert (paths.REPO_ROOT / "backend").is_dir()

    def test_backend_dir_is_where_pyproject_lives(self):
        assert (paths.BACKEND_DIR / "pyproject.toml").is_file()

    def test_ml_dir_is_this_package(self):
        assert (paths.ML_DIR / "paths.py").is_file()

    def test_local_dir_sits_beside_backend_not_inside_it(self):
        """Anything under backend/ risks being swept into a deploy."""
        assert paths.LOCAL_DIR.parent == paths.REPO_ROOT
        assert paths.BACKEND_DIR not in paths.LOCAL_DIR.parents


class TestTrackedFilesResolve:
    """Paths to files that are in git must actually land on them."""

    def test_questions(self):
        assert paths.QUESTIONS_PATH.is_file()

    def test_eval_dataset(self):
        assert paths.EVAL_DATASET_PATH.is_file()

    def test_results_dir(self):
        assert paths.RESULTS_DIR.is_dir()


class TestGeneratedPathsAreAnchoredNotAsserted:
    """Generated artifacts may be absent; only their location is fixed."""

    @pytest.mark.parametrize(
        "path",
        [paths.TRAIN_PATH, paths.VAL_PATH, paths.PHRASINGS_PATH],
    )
    def test_lives_in_the_data_dir(self, path: Path):
        assert path.parent == paths.DATA_DIR

    @pytest.mark.parametrize("path", [paths.MODELS_DIR, paths.LLAMA_BIN_DIR, paths.LLAMA_SRC_DIR])
    def test_lives_in_the_local_dir(self, path: Path):
        assert path.parent == paths.LOCAL_DIR


class TestLlamaExe:
    def test_prefers_the_pinned_build_over_path(self, tmp_path: Path):
        """A system llama.cpp of another version would not match the recorded rows."""
        pinned = tmp_path / "llama-quantize.exe"
        pinned.write_text("")
        (tmp_path / "llama-quantize").write_text("")
        assert paths.llama_exe("llama-quantize", tmp_path).parent == tmp_path

    def test_falls_back_to_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(paths.shutil, "which", lambda name: "/usr/bin/" + name)
        assert paths.llama_exe("llama-server", tmp_path) == Path("/usr/bin/llama-server")

    def test_missing_binary_is_fatal_and_names_both_places_looked(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setattr(paths.shutil, "which", lambda name: None)
        with pytest.raises(SystemExit) as excinfo:
            paths.llama_exe("llama-imatrix", tmp_path)
        message = str(excinfo.value)
        assert "llama-imatrix" in message
        assert str(tmp_path) in message
        assert "PATH" in message

    def test_defaults_to_the_pinned_bin_dir(self, monkeypatch: pytest.MonkeyPatch):
        """Omitting bin_dir looks in .local/bin, not the cwd.

        Uses a name no build ships, because a real one resolves on any machine that has
        actually run the pipeline — which is where this test would otherwise pass or fail
        depending on the developer.
        """
        monkeypatch.setattr(paths.shutil, "which", lambda name: None)
        with pytest.raises(SystemExit) as excinfo:
            paths.llama_exe("llama-not-a-real-binary")
        assert str(paths.LLAMA_BIN_DIR) in str(excinfo.value)
