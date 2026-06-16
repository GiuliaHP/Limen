from . import cleaner, applier, Constent, morph_bake
import importlib

from .cleaner import clear_rig_data
from .applier import apply_constraints_from_dict
from .morph_bake import update_adult_shape
from .Constent import MAPPING_DICT

def reload_core():
    """Recharge les modules enfants ET re-binde les noms du package vers les versions fraîches."""
    global clear_rig_data, apply_constraints_from_dict, update_adult_shape, MAPPING_DICT
    importlib.reload(Constent)
    importlib.reload(cleaner)
    importlib.reload(applier)
    importlib.reload(morph_bake)
    # Sans ces ré-affectations, le package garde les fonctions du 1er import (versions périmées).
    clear_rig_data = cleaner.clear_rig_data
    apply_constraints_from_dict = applier.apply_constraints_from_dict
    update_adult_shape = morph_bake.update_adult_shape
    MAPPING_DICT = Constent.MAPPING_DICT
    print("✅ Core modules reloaded.")
