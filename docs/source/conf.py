"""Sphinx configuration for tranq documentation."""
import os
import sys
from pathlib import Path

# Add src/ to path so autodoc can import tranq
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

# -- Project information -----------------------------------------------------
project = "tranq"
copyright = "2026, RaptorVampire"
author = "RaptorVampire"
release = "1.1.0"
version = "1.1.0"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
    "sphinx_design",
]

templates_path = ["_templates"]
exclude_patterns = []
source_suffix = ".rst"
master_doc = "index"
language = "en"
pygments_style = "monokai"
todo_include_todos = True

# -- Autodoc -----------------------------------------------------------------
autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__,__call__,__enter__,__exit__,__aenter__,__aexit__",
    "undoc-members": False,
    "show-inheritance": True,
}
autosummary_generate = True

# -- Napoleon ----------------------------------------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True

# -- Intersphinx -------------------------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "asyncio": ("https://docs.python.org/3", None),
}

# -- Options for HTML output -------------------------------------------------
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_title = "tranq"
html_short_title = "tranq"
html_logo = None
html_favicon = None

html_theme_options = {
    "logo_only": False,
    "display_version": True,
    "prev_next_buttons_location": "both",
    "style_external_links": True,
    "collapse_navigation": False,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False,
    "canonical_url": "https://tranq.readthedocs.io/",
}

html_context = {
    "display_github": True,
    "github_user": "RaptorVampire",
    "github_repo": "tranq",
    "github_version": "main",
    "conf_py_path": "/docs/source/",
}

# -- Options for copybutton --------------------------------------------------
copybutton_prompt_text = r">>> |\.\.\. |\$ "
copybutton_prompt_is_regexp = True
copybutton_only_copy_prompt_lines = True

# -- Options for LaTeX -------------------------------------------------------
latex_elements = {}
latex_documents = [
    (master_doc, "tranq.tex", "tranq Documentation",
     "RaptorVampire", "manual"),
]
