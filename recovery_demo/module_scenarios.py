"""Compatibility imports. New module definitions live in assembly_modules."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from assembly_modules.shared.engine import ModuleCase, run_module_case
from assembly_modules.prefilter.scenarios import scenarios as prefilter_cases
from assembly_modules.tube_interface.scenarios import scenarios as tube_cases


def module_cases():
    return prefilter_cases() + tube_cases()
