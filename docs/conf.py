# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import sys
from pathlib import Path

# add root/docs for finding stubs
# sys.path.insert(0, Path(__file__).parent.resolve().as_posix())
# add root for finding module mcpb
sys.path.insert(0, Path(__file__).parents[1].resolve().as_posix())


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "MCPB"
copyright = "2024, Felix Wallner"
author = "Felix Wallner"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    # "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx.ext.autodoc.typehints",
    # "my_extension",
    # "sphinx_autodoc_typehints",
    # "sphinx.ext.viewcode",
    # "sphinx.ext.autosectionlabel",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]


autodoc_default_options = {
    "member-order": "bysource",
    "members": True,
    "undoc-members": True,
    # "show-inheritance": False, # False shows Bases?
}
add_module_names = False
