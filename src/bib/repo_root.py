from pathlib import Path

def _repo_root(start: Path | None = None) -> Path:
    """Find repo root by walking up parents until we see a marker like .git or pyproject.toml."""
    start = start or Path.cwd()
    for p in [start, *start.parents]:
        if (p / ".git").exists() or (p / "pyproject.toml").exists():
            return p
    # Fallback: you can still use __file__ if you want
    return Path(__file__).resolve().parents[2]

def repo_abs(relative_path: str) -> Path:
    """Convert a path relative to the repo root into an absolute path."""
    return _repo_root() / relative_path


def repo_rel(absolute_path: Path) -> str:
    """Convert an absolute path into a path relative to the repo root."""
    return str(absolute_path.relative_to(_repo_root()))
