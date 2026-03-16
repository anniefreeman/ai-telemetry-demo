import pytest


class _VersionInfo:
    major = 3
    minor = 9
    micro = 18

    def __lt__(self, other):
        return (self.major, self.minor, self.micro) < other


def test_launcher_rejects_python_39(monkeypatch):
    namespace = {}
    with open("/Users/annie.freeman/demos/ai-centre-demo/ai-centre-demo.py", "r", encoding="utf-8") as handle:
        exec(handle.read(), namespace)

    monkeypatch.setattr("sys.version_info", _VersionInfo())

    with pytest.raises(SystemExit) as exc_info:
        namespace["_ensure_supported_python"]()

    assert "Python 3.10+ is required" in str(exc_info.value)
