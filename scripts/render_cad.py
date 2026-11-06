"""Render tessellations exported by the FreeCAD kernel."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

root = Path(__file__).resolve().parents[1]
fig = plt.figure(figsize=(12, 4.5))
for i, name in enumerate(["cylindrical", "tapered", "stepped"]):
    ax = fig.add_subplot(1, 3, i + 1, projection="3d")
    data = json.loads((root / "cad/exports" / name / "triangles.json").read_text())
    for component, mesh in data.items():
        polys = np.array(mesh["points_mm"])[np.array(mesh["triangles"])]
        color = (
            "#444b55" if component == "rubber" else ("#3987a2" if component == "top" else "#adb9c4")
        )
        ax.add_collection3d(
            Poly3DCollection(
                polys, facecolor=color, edgecolor="none", alpha=0.45 if component == "top" else 0.95
            )
        )
    ax.set(
        xlim=(-120, 120),
        ylim=(-100, 100),
        zlim=(-20, 65),
        xlabel="x [mm]",
        ylabel="y [mm]",
        zlabel="z [mm]",
        title=name,
    )
    ax.tick_params(labelsize=7)
    ax.xaxis.label.set_size(8)
    ax.yaxis.label.set_size(8)
    ax.zaxis.label.set_size(8)
    ax.set_box_aspect((240, 200, 85))
    ax.view_init(25, -48)
fig.suptitle("FreeCAD assemblies · uncompressed geometry · separate upper/lower studs")
fig.subplots_adjust(left=0.02, right=0.98, top=0.85, bottom=0.10, wspace=0.18)
fig.savefig(root / "results/cad_comparison.png", dpi=170, bbox_inches="tight")
