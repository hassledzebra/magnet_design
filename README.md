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

### Notes

- If you prefer using the existing local environment `magnet_design.venv/`, you can activate it directly instead of creating a new one:

  ```bash
  source magnet_design.venv/bin/activate
  ```

- Some packages (e.g., `cadquery`, `nlopt`) may require platform-specific binaries. If installation fails, ensure your Python version matches those supported in `requirements.txt` or try Python 3.12.
