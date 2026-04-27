import os
import sys

sys.path.insert(0, os.path.abspath(".."))

project = "Flask CI/CD Demo"
author = "CallMeAl3x"
release = "1.0.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
]

templates_path = ["_templates"]
exclude_patterns = ["_build"]

html_theme = "alabaster"
html_static_path = ["_static"]
