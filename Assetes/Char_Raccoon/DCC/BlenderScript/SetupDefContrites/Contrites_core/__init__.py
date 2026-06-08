from . import cleaner, applier, Constent
import importlib

from .cleaner import clear_rig_data
from .applier import apply_constraints_from_dict
from .Constent import MAPPING_DICT

def reload_core():
    """Recharge les modules enfants"""
    importlib.reload(Constent)
    importlib.reload(cleaner)
    importlib.reload(applier)
    print("✅ Core modules reloaded.")