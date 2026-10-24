"""Run the original Light Localizer implementation into its own module folder."""
from pathlib import Path
import subprocess
import sys

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    output = Path(__file__).resolve().parent/"outputs"
    subprocess.run([sys.executable,str(root/"recovery_demo/run_demo.py"),"--output-dir",str(output)],check=True)
    # Preserve working references to existing approved evidence and review pages.
    playback = output/"recovery_playback.html"
    playback.write_text(playback.read_text(encoding="utf-8-sig").replace(
        '../../outputs/approved_visual_references/', '../../../outputs/approved_visual_references/'),encoding="utf-8")
    dashboard = output/"dashboard.html"
    dashboard.write_text(dashboard.read_text(encoding="utf-8-sig").replace(
        'href="real_video_review/review.html"','href="../../../recovery_demo/outputs/real_video_review/review.html"'),encoding="utf-8")
