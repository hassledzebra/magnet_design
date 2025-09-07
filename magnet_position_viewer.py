"""
3D viewer for magnet positions defined by a ledger.

Usage examples:

  - Visualize an exported ledger (Excel):
      python magnet_position_viewer.py --ledger optimization_after_neonate_magnet_Rmin_132p7mm_extrinsic_rot_DSV140mm_maxh60_maxlayers6_maxmag990.xlsx

  - Prefer Plotly scatter if magpylib UI is not desired:
      python magnet_position_viewer.py --ledger path/to/ledger.xlsx --backend plotly

Notes:
  - Ledger must contain the standard columns used in this repo:
    ['X-pos','Y-pos','Z-pos','X-rot','Y-rot','Z-rot','Magnet_length','Tag', ...]
  - The default backend uses magpylib to render cuboids with orientation.
    Plotly backend shows positions as points (basic structure overview).
"""

from __future__ import annotations

import argparse
import os
from typing import Optional

import pandas as pd


def _read_ledger(path: str) -> pd.DataFrame:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(path)
    if ext in (".csv",):
        return pd.read_csv(path)
    raise ValueError(f"Unsupported ledger format: {ext}. Use .xlsx or .csv")


def view_with_magpy(ledger: pd.DataFrame, magnetization=(1270, 0, 0)) -> None:
    """Render 3D cuboids via magpylib using existing helper.

    Falls back to Plotly scatter if magpylib is unavailable.
    """
    try:
        import magsimulator  # local module
        # Normalize required columns casing and presence
        required = [
            'X-pos', 'Y-pos', 'Z-pos',
            'X-rot', 'Y-rot', 'Z-rot',
            'Magnet_length'
        ]
        for col in required:
            if col not in ledger.columns:
                raise KeyError(f"Missing required column '{col}' in ledger")
        # Use built-in visualizer that respects rotations and size
        magsimulator.plot_magnets3D(ledger, localsensors=None, mag_constant=list(magnetization))
    except Exception as e:
        print(f"magpylib visualization failed ({e}). Falling back to Plotly scatter.")
        view_with_plotly(ledger)


def view_with_plotly(ledger: pd.DataFrame) -> None:
    """Simple 3D scatter using Plotly to show basic structure (positions).
    Colors by 'Tag' if present; otherwise by Z.
    """
    import numpy as np
    import plotly.graph_objects as go

    x = ledger['X-pos'].to_numpy()
    y = ledger['Y-pos'].to_numpy()
    z = ledger['Z-pos'].to_numpy()

    if 'Tag' in ledger.columns:
        color = ledger['Tag']
        showscale = False
    else:
        color = z
        showscale = True

    fig = go.Figure()
    fig.add_trace(
        go.Scatter3d(
            x=x, y=y, z=z,
            mode='markers',
            marker=dict(size=3, color=color, colorscale='Viridis', showscale=showscale),
            name='magnets'
        )
    )

    # Draw a reference sphere for isocenter context
    r = max(1.0, float(np.percentile(np.sqrt(x**2 + y**2), 90)))
    u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:10j]
    xs = r*np.cos(u)*np.sin(v)
    ys = r*np.sin(u)*np.sin(v)
    zs = r*np.cos(v)
    fig.add_trace(go.Surface(x=xs, y=ys, z=zs, opacity=0.08, showscale=False, name='ref'))

    fig.update_scenes(
        xaxis_title='X (mm)', yaxis_title='Y (mm)', zaxis_title='Z (mm)',
        aspectmode='data'
    )
    fig.update_layout(title='Magnet Basic Structure (positions)', legend=dict(orientation='h'))
    fig.show()


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="3D view of magnet basic structures from ledger")
    parser.add_argument(
        "--ledger",
        type=str,
        default=None,
        help="Path to ledger file (.xlsx or .csv). If omitted, tries to use a known sample in repo."
    )
    parser.add_argument(
        "--backend",
        choices=["magpy", "plotly"],
        default="magpy",
        help="Visualization backend: magpy (oriented cuboids) or plotly (points)."
    )
    parser.add_argument(
        "--magnetization",
        type=float,
        nargs=3,
        default=(1270.0, 0.0, 0.0),
        metavar=("Mx", "My", "Mz"),
        help="Magnetization vector for magpylib viewer (mT)."
    )
    args = parser.parse_args(argv)

    candidate_defaults = [
        # Preferred output from neonate scripts if present
        "optimization_after_neonate_magnet_Rmin_112p7mm.xlsx",
        # Existing repo artifact
        "optimization_after_neonate_magnet_Rmin_132p7mm_extrinsic_rot_DSV140mm_maxh60_maxlayers6_maxmag990.xlsx",
    ]

    ledger_path = args.ledger
    if ledger_path is None:
        for c in candidate_defaults:
            if os.path.exists(c):
                ledger_path = c
                break
        if ledger_path is None:
            raise SystemExit("No --ledger provided and no default ledger found in repo.")

    ledger = _read_ledger(ledger_path)

    if args.backend == "magpy":
        view_with_magpy(ledger, magnetization=tuple(args.magnetization))
    else:
        view_with_plotly(ledger)


if __name__ == "__main__":
    main()

