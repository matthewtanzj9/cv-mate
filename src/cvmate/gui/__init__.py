# Empty marker module — deliberately no re-exports and no side-effect
# imports here. `cvmate/__init__.py` (the core library's import surface)
# never imports from this package, so `import cvmate` never pulls in
# PySide6. Only code that explicitly does `from cvmate.gui import ...` or
# runs the `cvmate-gui` entry point touches Qt.
