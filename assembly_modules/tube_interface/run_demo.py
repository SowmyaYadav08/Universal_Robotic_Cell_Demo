from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from assembly_modules.tube_interface.scenarios import scenarios
from assembly_modules.shared.run_module import run

if __name__ == "__main__":
    run("Tube Interface",scenarios(),Path(__file__).resolve().parent)
