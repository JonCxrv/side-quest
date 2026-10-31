"""Pastas usadas pelo side-quest, tanto rodando com Python quanto pelo .exe."""
import sys
from pathlib import Path

# No .exe, os arquivos ficam ao lado do executável. Rodando com Python, ao lado do código.
APP_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent

BUILD = APP_DIR / "build"
TEMPLATES = APP_DIR / "templates"
