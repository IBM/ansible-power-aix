##############################################################################
# © Copyright IBM Corporation 2020                                           #
##############################################################################

##############################################################################
#                 Sphinx documentation Configuration                         #
##############################################################################
# Configuration file for the Sphinx documentation builder, for more follow link:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
# ``sphinx-build``` options follow link:
# https://www.sphinx-doc.org/en/latest/man/sphinx-build.html
##############################################################################

##############################################################################
# Project information
##############################################################################

project = 'IBM Power Systems AIX'
copyright = '2020, IBM'
author = 'IBM'

# The full version, including alpha/beta/rc tags
release = '1.0.0-beta1'

# Disable the Copyright footer for Read the docs at the bottom of the page
# by setting property html_show_copyright = False
html_show_copyright = True

# Disable showing Sphinx footer message:
# "Built with Sphinx using a theme provided by Read the Docs. "
html_show_sphinx = False

##############################################################################
# General configuration
##############################################################################

# # Add any Sphinx extension module names here, as strings. They can be extensions
# # coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
# extensions = [
#     "sphinx_rtd_theme",
# ]

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autosectionlabel'
]

# Add any paths that contain templates here, relative to this directory.
# templates_path = ['../templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

html_context = {
    "display_github": "True",
    "github_user": "IBM",
    "github_repo": "ansible-power-aix",
    "github_version": "dev-collection",
    "conf_py_path": "/docs/source/",
}

# The master toctree document.
master_doc = 'index'

html_favicon = 'favicon.ico'
