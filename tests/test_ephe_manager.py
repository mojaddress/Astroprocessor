"""Менеджер эфемерид: состояние, возможности, целостность, загрузка, отмена."""
import io
import urllib.request

import pytest

from astro_core import ephe_manager as em


def _item(payload: bytes, strict: bool = True) -> em.EpheFile:
    return em.EpheFile("test.se1", "тестовый файл",
                       em.blob_sha1(payload), len(payload), strict=strict)


class _FakeResponse:
    def __init__(self, payload):
        self._stream = io.BytesIO(payload)
        self.headers = {"Content-Length": str(len(payload))}

    def read(self, size=-1):
        return self._stream.read(size)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _serve(monkeypatch, payload):
    monkeypatch.setattr(urllib.request, "urlopen",
                        lambda url, timeout=None: _FakeResponse(payload))


def test_blob_sha1_matches_git_formula():
    payload = b"hello"
    assert em.blob_sha1(payload) == "b6fc4c620b67d95f953a5c1c1230aaab5db5a1b0"


def test_status_all_missing(tmp_path):
    entries = em.status(tmp_path)
    assert len(entries) == len(em.FILES)
    assert all(entry["state"] == "missing" for entry in entries)


def test_capabilities_degraded_when_missing(tmp_path):
    caps = em.capabilities(em.status(tmp_path))
    assert caps == {"high_precision_planets": False,
                    "chiron_and_asteroids": False,
                    "fictitious_points": False}


def test_inspect_ok_for_matching_content(tmp_path):
    payload = b"correct-content"
    (tmp_path / "test.se1").write_bytes(payload)
    entry = em.inspect_file(_item(payload), tmp_path)
    assert entry["state"] == "ok"
    assert entry["size"] == len(payload)


def test_inspect_changed_for_strict_mismatch(tmp_path):
    (tmp_path / "test.se1").write_bytes(b"other")
    entry = em.inspect_file(_item(b"expected", strict=True), tmp_path)
    assert entry["state"] == "changed"


def test_inspect_variant_for_non_strict_mismatch(tmp_path):
    (tmp_path / "test.se1").write_bytes(b"other")
    entry = em.inspect_file(_item(b"expected", strict=False), tmp_path)
    assert entry["state"] == "variant"


def test_summary_reports_missing_and_incomplete(tmp_path):
    info = em.summary(tmp_path)
    assert info["complete"] is False
    assert len(info["missing"]) == len(em.FILES)
    assert info["folder"] == str(tmp_path)


def test_fetch_writes_verified_file(tmp_path, monkeypatch):
    payload = b"payload-for-fetch"
    _serve(monkeypatch, payload)
    path = em.fetch(_item(payload), tmp_path)
    assert path.read_bytes() == payload
    assert not list(tmp_path.glob("*.part"))


def test_fetch_rejects_strict_mismatch(tmp_path, monkeypatch):
    _serve(monkeypatch, b"wrong")
    with pytest.raises(em.EpheIntegrityError):
        em.fetch(_item(b"expected", strict=True), tmp_path)
    assert not (tmp_path / "test.se1").exists()


def test_fetch_accepts_non_strict_mismatch(tmp_path, monkeypatch):
    _serve(monkeypatch, b"variant-content")
    path = em.fetch(_item(b"expected", strict=False), tmp_path)
    assert path.read_bytes() == b"variant-content"


def test_fetch_accept_upstream_flag(tmp_path, monkeypatch):
    _serve(monkeypatch, b"new-upstream")
    path = em.fetch(_item(b"old", strict=True), tmp_path, accept_upstream=True)
    assert path.read_bytes() == b"new-upstream"


def test_cancel_aborts_fetch(tmp_path, monkeypatch):
    _serve(monkeypatch, b"data")

    def cancel():
        raise RuntimeError("cancelled")

    with pytest.raises(RuntimeError):
        em.fetch(_item(b"data"), tmp_path, cancel=cancel)
    assert not (tmp_path / "test.se1").exists()


def test_progress_reported(tmp_path, monkeypatch):
    payload = b"x" * 200000
    _serve(monkeypatch, payload)
    seen = []
    em.fetch(_item(payload), tmp_path, progress=lambda p, m: seen.append(p))
    assert seen and seen[-1] == 100


def test_download_missing_skips_present(tmp_path, monkeypatch):
    _serve(monkeypatch, b"any")
    first = em.FILES[0]
    (tmp_path / first.name).write_bytes(b"placeholder")
    report = em.download_missing(tmp_path, accept_upstream=True)
    assert first.name in report["downloaded"] or first.name in report["skipped"]
    assert isinstance(report["failed"], dict)


def test_download_unknown_name_raises(tmp_path):
    with pytest.raises(KeyError):
        em.download("no-such-file.se1", folder=tmp_path)


def test_resolve_folder_respects_settings(tmp_path):
    assert em.resolve_folder(settings={"ephe_path": str(tmp_path)}) == tmp_path
    assert em.resolve_folder(folder=str(tmp_path)) == tmp_path
