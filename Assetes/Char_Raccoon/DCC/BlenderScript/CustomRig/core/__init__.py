import importlib

# 1. On importe les modules
from . import constants
from . import operators
from . import ui

# 2. On force le rafraîchissement de la mémoire
importlib.reload(constants)
importlib.reload(operators)
importlib.reload(ui)

def register():
    operators.register()
    ui.register()

def unregister():
    ui.unregister()
    operators.unregister()