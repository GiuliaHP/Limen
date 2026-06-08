from . import cleaner, applier, Constent
import importlib

from .cleaner import clear_rig_data
from .applier import apply_constraints_from_dict
from .Constent import MAPPING_DICT

def reload_core():
    """Recharge les modules enfants ET re-binde les noms du package vers les versions fraîches."""
    global clear_rig_data, apply_constraints_from_dict, MAPPING_DICT
    importlib.reload(Constent)
    importlib.reload(cleaner)
    importlib.reload(applier)
    # Sans ces ré-affectations, le package garde les fonctions du 1er import (versions périmées).
    clear_rig_data = cleaner.clear_rig_data
    apply_constraints_from_dict = applier.apply_constraints_from_dict
    MAPPING_DICT = Constent.MAPPING_DICT
    print("✅ Core modules reloaded.")