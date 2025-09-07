# MRI4ALL Open-Source Tools for Design of the Hallbach-Array Magnet

Please watch the <a href="https://www.youtube.com/embed/iKs5pwwoyoQ" target="_blank">video below</a> for an introduction to the tools provided in this repository.

[![Overview of the MRI4ALL Magnet Tools](https://img.youtube.com/vi/iKs5pwwoyoQ/0.jpg)](https://www.youtube.com/watch?v=iKs5pwwoyoQ)

## Getting Started

Use a Python virtual environment and install dependencies from `requirements.txt`.

### Prerequisites

- Python 3.12 or newer recommended
- `pip` available in your environment

### Setup

1. Create and activate a virtual environment:

   - macOS/Linux:

     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

   - Windows (PowerShell):

     ```powershell
     py -3 -m venv .venv
     .venv\Scripts\Activate.ps1
     ```

2. Install dependencies from `requirements.txt`:

   ```bash
   pip install -r requirements.txt
   ```

### Running

- Example script: `simulation_test.py`:1
  - After activating the environment, run:

    ```bash
    python simulation_test.py
    ```

## 3D Viewer

Visualize basic magnet structures from a ledger using `magnet_position_viewer.py`:1.

- magpylib cuboids (uses orientations and sizes):

  ```bash
  python magnet_position_viewer.py --ledger optimization_after_neonate_magnet_Rmin_132p7mm_extrinsic_rot_DSV140mm_maxh60_maxlayers6_maxmag990.xlsx
  ```

- Plotly point cloud (positions only):

  ```bash
  python magnet_position_viewer.py --ledger path/to/ledger.xlsx --backend plotly
  ```

- Options:
  - `--ledger`: Path to `.xlsx` or `.csv` ledger file.
  - `--backend`: `magpy` (default) or `plotly`.
  - `--magnetization Mx My Mz`: For magpylib rendering, default `1270 0 0` mT.

If `--ledger` is omitted, the script tries known filenames in the repo.

### Notes

- If you prefer using the existing local environment `magnet_design.venv/`, you can activate it directly instead of creating a new one:

  ```bash
  source magnet_design.venv/bin/activate
  ```

- Some packages (e.g., `cadquery`, `nlopt`) may require platform-specific binaries. If installation fails, ensure your Python version matches those supported in `requirements.txt` or try Python 3.12.
