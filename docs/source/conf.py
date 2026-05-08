# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import sys

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath("../.."))

import datetime
import sphinx
from typing import Dict, Any

logger = sphinx.util.logging.getLogger(__name__)

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Display"
copyright = "2026, NLDCSC"
author = "Paul Tikken"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.githubpages",
    "sphinx.ext.intersphinx",
    # "sphinx.ext.autosectionlabel",
    "myst_parser",
    "sphinx_copybutton",
    "sphinx_inline_tabs",
    "sphinx_design",
]

myst_enable_extensions = [
    "colon_fence",
    "deflist",
]

myst_heading_anchors = 4

suppress_warnings = ["myst.xref_missing"]

templates_path = ["_templates"]
exclude_patterns = []

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master", None),
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]

html_title = "Display"
html_favicon = "_static/images/display.png"
html_logo = "_static/images/display.png"

html_css_files = [
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/fontawesome.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/solid.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/brands.min.css",
    "css/custom.css",
]

html_theme_options: Dict[str, Any] = {
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/NLDCSC/display",
            "html": "",
            "class": "fa-brands fa-square-github fa-2x",
        },
    ],
    "source_repository": "https://github.com/NLDCSC/display",
    "source_branch": "master",
    "source_directory": "docs/source/",
    "top_of_page_buttons": [],
    "navigation_with_keys": True,
}
html_show_sphinx = False
html_last_updated_fmt = datetime.datetime.now().replace(microsecond=0).isoformat()
html_show_sourcelink = False
