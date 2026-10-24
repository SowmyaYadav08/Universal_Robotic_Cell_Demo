# Universal Robotic Cell (URC) Demo

**[View the interactive demo](https://SowmyaYadav08.github.io/Universal_Robotic_Cell_Demo/)** — switch between three module dashboards, explore issue filters, download simulated results, and watch the Light Localizer replacement playback. All published results are synthetic examples; no physical robot is controlled.

The demo is built automatically by the GitHub Pages workflow. Manufacturing recordings and reference photos are excluded from the public website.

Explore assembly problems, review video motion, and demonstrate a simulated recovery workflow. The project includes Light Localizer, Prefilter, and Tube Interface assembly examples, plus presentation material.

**Start with the offline demo below.** It uses scripted scenarios and needs no recordings, model downloads, or external services. It does not control a physical robot or PLC.

## Quick start

Install Python 3.10 or newer, clone this repository from its GitHub **Code** menu, and open a terminal in the cloned folder.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe recovery_demo/run_demo.py
```

Open `recovery_demo/outputs/dashboard.html` in your browser. It shows simulated assembly issues, priorities, and recovery outcomes. Use **Watch simulated recovery** to view the replacement animation. Rerunning the demo overwrites its generated reports.

To generate separate reports for all three modules:

```powershell
.\.venv\Scripts\python.exe assembly_modules/run_all.py
```

Open `assembly_modules/index.html`. Each module keeps its own reports. The basic demos use only the Python standard library.

## Find your way around

| Location | What it contains |
| --- | --- |
| [recovery_demo/](recovery_demo/README.md) | Light Localizer recovery simulation, dashboard, video review, and evaluation instructions |
| [assembly_modules/](assembly_modules/README.md) | Separate entry points for Light Localizer, Prefilter, and Tube Interface |
| [SYNTHETIC_DEMO.md](SYNTHETIC_DEMO.md) | Generated video scenarios and plate-loss detector validation |
| `step*.py` | Exploratory frame extraction, MobileNet feature comparison, ROI selection, and motion analysis |
| `light_localizer_config.py` | Assembly stages and anomaly categories |
| [experiments/dinov2_comparison/](experiments/dinov2_comparison/README.md) | Optional model-comparison experiment |
| [presentation_assets/](presentation_assets/README.md) | Editable fishbone diagrams and rendering script |
| `Data/` | Local recordings; excluded from Git |
| `outputs/` | Locally generated results; excluded from Git |

## Optional video and model experiments

The generated video demo needs NumPy and OpenCV:

```powershell
.\.venv\Scripts\python.exe -m pip install numpy opencv-python
.\.venv\Scripts\python.exe validate_synthetic_demo.py
```

See [the synthetic demo guide](SYNTHETIC_DEMO.md) for expected results and limitations. The MobileNet scripts additionally need `torch`, `torchvision`, and `Pillow`; their first use may download pretrained weights. Follow the separate DINOv2 experiment README for that experiment's setup.

Real-video workflows require the approved recordings and local configuration described in [recovery_demo/README.md](recovery_demo/README.md). Recordings are not included. Some exploratory scripts use fixed paths or interactive region selection; check those scripts before running them. `step2_extract_frames.py` expects `data/normal/normal_video.mp4` and `data/failure/failure_video.mp4`. Folder capitalization matters on Linux.

## What the results mean

- Recovery scenarios and sensor checks are simulated, rather than measured factory events.
- Real-video motion alerts identify moments for human review; they do not prove a component dropped.
- Evaluation requires independently verified reference intervals. Calibration results alone do not establish accuracy.
- Prefilter and Tube Interface examples have synthetic scenarios; their automatic fault recovery and video detectors are not implemented.
- Fishbone branches are investigation hypotheses, rather than confirmed physical causes.

## Work with teammates on GitHub

1. The repository owner opens **Settings → Collaborators** (or the organization's access settings) and invites teammates using their GitHub usernames.
2. Each teammate clones the repository using the URL from **Code**.
3. Before starting work, update the local default branch with `git pull --ff-only`.
4. Create a branch, make changes, and push it:

   ```powershell
   git switch -c docs/improve-demo-guide
   git add README.md
   git commit -m "Improve demo guide"
   git push -u origin docs/improve-demo-guide
   ```

5. On GitHub, open a pull request, explain the change and how it was checked, and request a teammate's review before merging.

Use **Issues** for tasks and bugs. Share code and documentation through commits and pull requests. Share only recordings and assets that the team is permitted to distribute; keep credentials out of commits. Large approved files can be shared through an agreed team storage location or Git LFS after configuring it.

## Checks

Run the recovery tests from the repository root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s recovery_demo -p "test_*.py" -v
```

The repository excludes local environments, recordings, model weights, generated reports, and the frozen experiment snapshot. Clone users regenerate reports with the commands above. See the folder-specific guides for additional setup and checks.
