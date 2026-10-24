"""Generate three independent module reports; no combined incident dataset."""
import argparse
from pathlib import Path
import subprocess
import sys

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previews",action="store_true",help="Generate approved previews separately for the two new modules")
    args = parser.parse_args()
    base = Path(__file__).resolve().parent
    for module in ("light_localizer","prefilter","tube_interface"):
        command = [sys.executable,str(base/module/"run_demo.py")]
        if args.previews and module != "light_localizer":
            command.append("--previews")
        print(f"Running {module.replace('_',' ')}...",flush=True)
        subprocess.run(command,check=True)
    from build_hub import build_hub
    build_hub()
    print(f"Finished. Open {base/'index.html'} for links to the three separate reports.")
