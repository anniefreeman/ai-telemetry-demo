import sys


MIN_PYTHON = (3, 10)


def _ensure_supported_python() -> None:
    if sys.version_info < MIN_PYTHON:
        version = f"{sys.version_info.major}.{sys.version_info.minor}"
        required = ".".join(str(part) for part in MIN_PYTHON)
        raise SystemExit(
            f"Python {required}+ is required for this CLI because the OpenAI Agents SDK "
            f"does not support Python {version}. Re-run with Python {required}+."
        )


if __name__ == "__main__":
    _ensure_supported_python()
    from sustainable_fashion_advisor.cli import app

    app()
