"""Sphinx configuration."""
project = "event-horyzen"
author = "David Wright"
copyright = f"2022, {author}"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
]
html_static_path = ["_static"]
