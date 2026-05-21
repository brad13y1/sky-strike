"""
core/ — foundation modules.

These four files (constants, paths, display, input) form the base of
the project. They import from each other but nothing else inside the
project — so they can never have a circular-import problem.

Game code (scenes/, systems/, levels/) imports FROM core, never the
other way around.
"""