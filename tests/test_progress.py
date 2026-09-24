"""Tests for local progress persistence."""

from nvim_quest.progress.store import ProgressStore, default_save_path


def test_default_save_lives_next_to_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert default_save_path().parent.resolve() == tmp_path.resolve()
    assert default_save_path().name == "nvim-quest-save.json"


def test_record_roundtrip(tmp_path):
    store = ProgressStore(path=tmp_path / "save.json")
    store.record("navigation_character_01", "Mastery", 26)
    reloaded = ProgressStore(path=tmp_path / "save.json")
    assert reloaded.progress.best_ranks["navigation_character_01"] == "Mastery"
    assert "navigation_character_01" in reloaded.progress.completed
