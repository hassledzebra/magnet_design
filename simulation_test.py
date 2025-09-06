import numpy as np
import matplotlib.pyplot as plt
import magpylib as magpy
from scipy.spatial.transform import Rotation as R
import pandas as pd
import magsimulator as ms


def build_halbach_ring(n_magnets=16,
                       radius_mm=60.0,
                       cube_side_mm=10.0,
                       magnetization_mT=1270.0,
                       z0_mm=0.0,
                       tag='halbach'):
    """
    Build a simple single-layer circular Halbach ring using discrete cubes.

    - n_magnets: number of cubes around the ring
    - radius_mm: ring radius (to cube centers)
    - cube_side_mm: cube edge length
    - magnetization_mT: remanence magnitude in mT (e.g., ~1270 for N52)
    - z0_mm: z position of the ring plane
    Returns: (ledger_df, magpy.Collection)
    """
    # Positions + rotations following Halbach dipole pattern (rotz = 2*theta)
    pts = ms.generate_ring_of_magnets(r=radius_mm,
                                      z=z0_mm,
                                      cube_side_length=cube_side_mm,
                                      number_mags_aximuthal=int(n_magnets),
                                      theta_offset=0,
                                      tag=tag)

    cols = ['X-pos', 'Y-pos', 'Z-pos','X-rot','Y-rot','Z-rot',
            'Searched','CostValue','Used','Placement_index','Bmag','Magnet_length','Tag']
    ledger = pd.DataFrame(pts, columns=cols)

    col_magnets = magpy.Collection(style_label='halbach_ring')
    for _, row in ledger.iterrows():
        cube = magpy.magnet.Cuboid(
            magnetization=(0, magnetization_mT, 0),
            dimension=(row['Magnet_length'], row['Magnet_length'], row['Magnet_length'])
        )
        cube.position = (row['X-pos'], row['Y-pos'], row['Z-pos'])
        cube.orientation = R.from_euler('zyx', [row['Z-rot'], row['Y-rot'], row['X-rot']], degrees=True)
        col_magnets.add(cube)

    return ledger, col_magnets

def build_halbach_ring_segments(n_magnets=16,
                                center_radius_mm=60.0,
                                radial_thickness_mm=12.7,
                                height_mm=12.7,
                                magnetization_mT=1500.0,
                                z0_mm=0.0,
                                tag='halbach_seg'):
    """
    Build a circular Halbach ring made of trapezoidal wedge magnets using CylinderSegment.

    The segment geometry is trapezoidal in radial cross-section [r1,r2] and spans an
    angular width of dphi = 2*pi/n_magnets. The geometry is rotated to angle theta_i,
    and magnetization is set so that world magnetization rotates as 2*theta_i (dipole Halbach).

    Returns: (segments_ledger, magpy.Collection)
    segments_ledger: list of dicts with keys {theta, dphi, r1, r2, z0, h}
    """
    dphi = 2*np.pi / n_magnets
    r1 = center_radius_mm - radial_thickness_mm/2
    r2 = center_radius_mm + radial_thickness_mm/2
    h = height_mm

    col = magpy.Collection(style_label=f'{tag}_segments')
    segments_ledger = []

    for i in range(n_magnets):
        theta = i * dphi
        # Local segment spanning [-dphi/2, +dphi/2]
        seg = magpy.magnet.CylinderSegment(
            magnetization=(magnetization_mT*np.cos(theta), magnetization_mT*np.sin(theta), 0.0),
            dimension=(r1, r2, h, -np.degrees(dphi)/2, np.degrees(dphi)/2),
        )
        # Place at ring plane and rotate geometry to theta
        seg.position = (0.0, 0.0, z0_mm)
        seg.orientation = R.from_euler('z', np.degrees(theta), degrees=True)
        col.add(seg)
        segments_ledger.append({
            'theta': theta,
            'dphi': dphi,
            'r1': r1,
            'r2': r2,
            'z0': z0_mm,
            'h': h
        })

    return segments_ledger, col


from matplotlib.path import Path as MplPath


def plot_xy_field(col_magnets,
                  plane_z_mm=0.0,
                  extent_mm=150.0,
                  grid_size=101,
                  component=None,
                  ledger_df=None,
                  segments_ledger=None,
                  show_streamlines=True):
    """
    Compute and plot the magnetic field in the z=constant plane.
    - component: None for |B|, or 0/1/2 for Bx/By/Bz heatmap.
    """
    xs = np.linspace(-extent_mm, extent_mm, grid_size)
    ys = np.linspace(-extent_mm, extent_mm, grid_size)
    X, Y = np.meshgrid(xs, ys)
    grid = np.stack((X, Y, np.full_like(X, plane_z_mm)), axis=-1)
    B = col_magnets.getB(grid)  # shape (ny, nx, 3) in mT

    Bx = B[:, :, 0]
    By = B[:, :, 1]
    Bz = B[:, :, 2]
    Bmag = np.sqrt(Bx**2 + By**2 + Bz**2)

    # Build a mask for magnet footprints in this plane: squares (ledger_df) or segments (segments_ledger)
    mask = np.zeros_like(Bmag, dtype=bool)
    magnet_polys = []  # for drawing outlines of squares
    radial_lines = []  # for drawing segment edges
    arc_curves = []    # (r, theta_start, theta_end) to draw arcs
    if ledger_df is not None:
        for _, row in ledger_df.iterrows():
            s = row['Magnet_length']
            zc = row['Z-pos']
            # Only mask if this plane intersects the cube in z
            if (plane_z_mm >= zc - s/2) and (plane_z_mm <= zc + s/2):
                xc, yc = row['X-pos'], row['Y-pos']
                angle = np.deg2rad(row['Z-rot'])
                # square corners before rotation
                half = s/2.0
                corners = np.array([
                    [-half, -half],
                    [ half, -half],
                    [ half,  half],
                    [-half,  half],
                    [-half, -half],
                ])
                Rz = np.array([[np.cos(angle), -np.sin(angle)],
                               [np.sin(angle),  np.cos(angle)]])
                poly = corners @ Rz.T + np.array([xc, yc])
                magnet_polys.append(poly)
                # mask points inside polygon
                path = MplPath(poly)
                pts = np.vstack((X.ravel(), Y.ravel())).T
                inside = path.contains_points(pts).reshape(X.shape)
                mask |= inside
    if segments_ledger is not None:
        # Precompute polar grid
        Rg = np.sqrt(X**2 + Y**2)
        PHI = np.arctan2(Y, X)
        for seg in segments_ledger:
            zc = seg['z0']
            if (plane_z_mm >= zc - seg['h']/2) and (plane_z_mm <= zc + seg['h']/2):
                theta = seg['theta']
                dphi = seg['dphi']
                r1, r2 = seg['r1'], seg['r2']
                # angle difference wrapped to [-pi, pi]
                d = PHI - theta
                d = (d + np.pi) % (2*np.pi) - np.pi
                inside = (np.abs(d) <= dphi/2) & (Rg >= r1) & (Rg <= r2)
                mask |= inside
                # store outlines: radial lines at theta±dphi/2 and inner/outer arcs
                radial_lines.append((theta - dphi/2, r1, r2))
                radial_lines.append((theta + dphi/2, r1, r2))
                arc_curves.append((r1, theta - dphi/2, theta + dphi/2))
                arc_curves.append((r2, theta - dphi/2, theta + dphi/2))

    # Apply mask to field data
    if component is None:
        data = np.ma.array(Bmag, mask=mask)
        label = '|B|'
    else:
        comp_map = {0: ('Bx', Bx), 1: ('By', By), 2: ('Bz', Bz)}
        label, raw = comp_map.get(component, ('|B|', Bmag))
        data = np.ma.array(raw, mask=mask)

    fig, ax = plt.subplots(1, 1, figsize=(7, 6))
    im = ax.imshow(data, origin='lower', extent=[xs.min(), xs.max(), ys.min(), ys.max()], cmap='coolwarm')
    ax.set_title(f'{label} in plane z={plane_z_mm:.1f} mm (mT)')

    # Streamlines for in-plane field, masked inside magnets
    if show_streamlines:
        U = np.ma.array(Bx, mask=mask)
        V = np.ma.array(By, mask=mask)
        ax.streamplot(X, Y, U, V, color='k', density=1.2, linewidth=0.7, arrowsize=0.7)

    # Draw magnet outlines (squares)
    for poly in magnet_polys:
        ax.plot(poly[:,0], poly[:,1], color='k', linewidth=1.0)
    # Draw segment outlines (radial lines and arcs)
    for th, rmin, rmax in radial_lines:
        xline = [rmin*np.cos(th), rmax*np.cos(th)]
        yline = [rmin*np.sin(th), rmax*np.sin(th)]
        ax.plot(xline, yline, color='k', linewidth=1.0)
    for rfix, th1, th2 in arc_curves:
        ths = np.linspace(th1, th2, 100)
        ax.plot(rfix*np.cos(ths), rfix*np.sin(ths), color='k', linewidth=1.0)

    cbar = fig.colorbar(im, ax=ax)
    cbar.ax.set_ylabel('mT')
    ax.set_xlabel('x (mm)')
    ax.set_ylabel('y (mm)')
    ax.set_aspect('equal', adjustable='box')
    fig.tight_layout()
    plt.show()


if __name__ == '__main__':
    # Trapezoidal (wedge) arch magnets using CylinderSegment
    # Keep comparable sizing to previous cubes: ~12.7 mm radial thickness and height
    radial_thickness_mm = 25.4/2  # 12.7 mm
    height_mm = 25.4/2            # 12.7 mm along z
    R_mm = 40.0                   # bring magnets closer to increase field inside
    n = 10                        # fewer segments
    Br_mT = 1500.0               # stronger individual magnetization
    z_plane = 0.0

    print(f'Building wedge Halbach ring: n={n}, R_center={R_mm} mm, dr={radial_thickness_mm} mm, h={height_mm} mm, Br={Br_mT} mT')
    seg_ledger, col_demo = build_halbach_ring_segments(n_magnets=n,
                                                       center_radius_mm=R_mm,
                                                       radial_thickness_mm=radial_thickness_mm,
                                                       height_mm=height_mm,
                                                       magnetization_mT=Br_mT,
                                                       z0_mm=z_plane,
                                                       tag='halbach_wedge')

    # Visualize |B| and in-plane streamlines in the z=0 plane
    extent = 2.0 * (R_mm + radial_thickness_mm)
    plot_xy_field(col_demo, plane_z_mm=z_plane, extent_mm=extent, grid_size=181, component=None, segments_ledger=seg_ledger, show_streamlines=True)
