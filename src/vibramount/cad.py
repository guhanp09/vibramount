"""Editable FreeCAD mount assemblies, exported in mm (STEP) and m (STL)."""

import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def modules():
    import FreeCAD as App
    import Part

    return App, Part


def make_parts(config, design):
    App, Part = modules()
    v = App.Vector
    p, d = config["plate"], design
    h, cap = d["rubber_height_mm"], p["cap_mm"]
    spacer = d.get("spacer_mm", 0)
    upper_z = cap + h + spacer
    top_z = upper_z + cap
    base_size, top_size = p["base_mm"], p["top_mm"]
    centers = list(itertools.product(*[[-x / 2, x / 2] for x in p["mount_pitch_mm"]]))

    def plate(size, z, holes):
        a, b, t = size
        shape = Part.makeBox(a, b, t, v(-a / 2, -b / 2, z))
        for x, y, dia in holes:
            shape = shape.cut(Part.makeCylinder(dia / 2, t + 2, v(x, y, z - 1)))
        return shape.removeSplitter()

    mounts = [(x, y, p["stud_hole_mm"]) for x, y in centers]
    anchors = [
        (x, y, p["anchor_hole_mm"])
        for x, y in itertools.product(*[[-x / 2, x / 2] for x in p["anchor_pitch_mm"]])
    ]
    feet = [
        (x, y, p["anchor_hole_mm"])
        for x, y in itertools.product(*[[-x / 2, x / 2] for x in p["compressor_pitch_mm"]])
    ]
    parts = {
        "base": plate(base_size, -base_size[2], mounts + anchors),
        "top": plate(top_size, top_z, mounts + feet),
    }
    rubber, lower, upper, mid, washers, nuts = [], [], [], [], [], []
    r0, r1, bore = d["bottom_diameter_mm"] / 2, d["top_diameter_mm"] / 2, d["bore_mm"] / 2
    for x, y in centers:
        if spacer:
            body = Part.makeCylinder(r0, h / 2, v(x, y, cap)).fuse(
                Part.makeCylinder(r1, h / 2, v(x, y, cap + h / 2 + spacer))
            )
            ring = Part.makeCylinder(r0, spacer, v(x, y, cap + h / 2)).cut(
                Part.makeCylinder(bore, spacer + 2, v(x, y, cap + h / 2 - 1))
            )
            mid.append(ring)
        elif r0 == r1:
            body = Part.makeCylinder(r0, h, v(x, y, cap))
        else:
            body = Part.makeCone(r0, r1, h, v(x, y, cap))
        rubber.append(body.cut(Part.makeCylinder(bore, h + spacer + 2, v(x, y, cap - 1))))
        lower.append(
            Part.makeCylinder(r0, cap, v(x, y, 0)).fuse(
                Part.makeCylinder(3, base_size[2] + 11, v(x, y, -base_size[2] - 10))
            )
        )
        upper.append(
            Part.makeCylinder(r1, cap, v(x, y, upper_z)).fuse(
                Part.makeCylinder(3, top_size[2] + 11, v(x, y, upper_z + cap - 1))
            )
        )
        for z in [-base_size[2] - 1.6, top_z + top_size[2]]:
            washers.append(
                Part.makeCylinder(6, 1.6, v(x, y, z)).cut(
                    Part.makeCylinder(3.5, 3.6, v(x, y, z - 1))
                )
            )
        for z in [-base_size[2] - 6.6, top_z + top_size[2] + 1.6]:
            rr = 10 / math.sqrt(3)
            points = [
                v(x + rr * math.cos(i * math.pi / 3), y + rr * math.sin(i * math.pi / 3), z)
                for i in range(6)
            ]
            blank = Part.Face(Part.makePolygon(points + [points[0]])).extrude(v(0, 0, 5))
            nuts.append(blank.cut(Part.makeCylinder(3.1, 7, v(x, y, z - 1))))
    for key, shapes in [
        ("rubber", rubber),
        ("lower_hardware", lower),
        ("upper_hardware", upper),
        ("washers", washers),
        ("nuts", nuts),
        ("spacer", mid),
    ]:
        if shapes:
            parts[key] = Part.makeCompound(shapes)
    return parts, centers, top_z


class Component:
    def execute(self, obj):
        config = json.loads(obj.Parameters.Configuration)
        d = dict(config["designs"][obj.Parameters.Design])
        for prop, key in [
            ("RubberHeight", "rubber_height_mm"),
            ("BottomDiameter", "bottom_diameter_mm"),
            ("TopDiameter", "top_diameter_mm"),
            ("BoreDiameter", "bore_mm"),
        ]:
            d[key] = getattr(obj.Parameters, prop).Value
        obj.Shape = make_parts(config, d)[0][obj.Component]

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


def drawing(name, c, d, path):
    plate = c["plate"]
    spacer = d.get("spacer_mm", 0)
    height = d["rubber_height_mm"] + 2 * plate["cap_mm"] + spacer
    body = f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540">
<rect width="960" height="540" fill="white"/>
<style>text{{font-family:Arial;fill:#203344}} .line{{stroke:#203344;fill:none;stroke-width:2}}</style>
<text x="35" y="40" font-size="24">VibraMount — {name}</text>
<text x="35" y="65" font-size="14">Dimensions mm · unloaded assembly · threads omitted</text>
<rect x="45" y="140" width="330" height="270" class="line"/>
<rect x="60" y="155" width="300" height="240" class="line"/>
<text x="45" y="440">Base 220×180×4; upper plate 200×160×4</text>
<text x="470" y="120">Side elevation · mount stack {height:.1f}</text>
<rect x="480" y="360" width="390" height="8" fill="#aab5be"/>
<rect x="495" y="{360 - height * 3 - 8}" width="360" height="8" fill="#3b7b9c"/>
'''
    for x in [105, 315]:
        for y in [192.5, 357.5]:
            body += f'<circle cx="{x}" cy="{y}" r="12" class="line"/>'
    for x in [550, 780]:
        body += f'<rect x="{x}" y="{360 - height * 3}" width="34" height="{height * 3}" fill="#444c55"/>'
        body += f'<line x1="{x + 17}" y1="{360 - height * 3 - 25}" x2="{x + 17}" y2="{360 - height * 3 + 5}" stroke="#bb7b31" stroke-width="4"/>'
        body += f'<line x1="{x + 17}" y1="355" x2="{x + 17}" y2="390" stroke="#bb7b31" stroke-width="4"/>'
    body += f"""<text x="470" y="420">Elastomer height {d["rubber_height_mm"]}; OD {d["bottom_diameter_mm"]}/{d["top_diameter_mm"]}; bore {d["bore_mm"]}</text>
<text x="35" y="480">Mounts: 4× M6 split studs on 140×110 pitch; plate holes Ø6.6; radial clearance 0.3</text>
<text x="35" y="505">Base anchors: 190×150 pitch Ø8.5; compressor interface: 100×70 pitch Ø8.5; verify purchased hardware.</text>
</svg>"""
    path.write_text(body)


def export_all():
    App, Part = modules()
    c = json.loads((ROOT / "configs/baseline.json").read_text())
    for name, d in c["designs"].items():
        out = ROOT / "cad/exports" / name
        out.mkdir(parents=True, exist_ok=True)
        parts, centers, top_z = make_parts(c, d)
        checks = {
            "freecad_version": ".".join(App.Version()[:3]),
            "design": name,
            "valid_solids": {},
            "unexpected_intersections": [],
            "step_units": "mm",
            "stl_units": "m",
            "geometry_state": "unloaded",
            "dynamic_properties": "assigned independently of geometry",
        }
        for key, shape in parts.items():
            if not shape.isValid() or not shape.Solids or shape.Volume <= 0:
                raise ValueError(f"Invalid solid {name}/{key}")
            checks["valid_solids"][key] = {"count": len(shape.Solids), "volume_mm3": shape.Volume}
        for a, b in itertools.combinations(parts, 2):
            if parts[a].common(parts[b]).Volume > 1e-4:
                checks["unexpected_intersections"].append([a, b])
        if checks["unexpected_intersections"]:
            raise ValueError(checks)
        checks["base_mount_holes_open"] = all(
            not parts["base"].isInside(App.Vector(x, y, -2), 1e-6, True) for x, y in centers
        )
        checks["metal_gap_mm"] = Part.makeCompound(
            [parts["base"], parts["lower_hardware"]]
        ).distToShape(Part.makeCompound([parts["top"], parts["upper_hardware"]]))[0]
        if not checks["base_mount_holes_open"] or checks["metal_gap_mm"] <= 0:
            raise ValueError("Mounting path check failed")
        doc = App.newDocument("VibraMount_" + name)
        parameters = doc.addObject("App::FeaturePython", "Parameters")
        parameters.addProperty("App::PropertyString", "Configuration").Configuration = json.dumps(c)
        parameters.addProperty("App::PropertyString", "Design").Design = name
        for prop, key in [
            ("RubberHeight", "rubber_height_mm"),
            ("BottomDiameter", "bottom_diameter_mm"),
            ("TopDiameter", "top_diameter_mm"),
            ("BoreDiameter", "bore_mm"),
        ]:
            parameters.addProperty("App::PropertyLength", prop, "Geometry")
            setattr(parameters, prop, d[key])
        objects = []
        mesh = {}
        for key in parts:
            obj = doc.addObject("Part::FeaturePython", key)
            obj.addProperty("App::PropertyLink", "Parameters").Parameters = parameters
            obj.addProperty("App::PropertyString", "Component").Component = key
            obj.Proxy = Component()
            objects.append(obj)
        doc.recompute()
        for obj in objects:
            points, triangles = obj.Shape.tessellate(0.35)
            mesh[obj.Name] = {
                "points_mm": [[p.x, p.y, p.z] for p in points],
                "triangles": triangles,
            }
        Part.export(objects, str(out / (name + ".step")))
        solid = Part.makeCompound([o.Shape for o in objects])
        matrix = App.Matrix()
        matrix.scale(0.001, 0.001, 0.001)
        solid.transformGeometry(matrix).exportStl(str(out / (name + "_m.stl")))
        import Mesh

        checks["step_reimport_valid"] = Part.read(str(out / (name + ".step"))).isValid()
        checks["stl_extent_m"] = Mesh.Mesh(str(out / (name + "_m.stl"))).BoundBox.XLength
        if not checks["step_reimport_valid"] or abs(checks["stl_extent_m"] - 0.220) > 1e-5:
            raise ValueError("STEP/STL export verification failed")
        doc.saveAs(str(out / (name + ".FCStd")))
        (out / "triangles.json").write_text(json.dumps(mesh))
        drawing(name, c, d, out / "drawing.svg")
        original = parts["rubber"].Volume
        parameters.RubberHeight = d["rubber_height_mm"] + 1
        for obj in objects:
            obj.touch()
        doc.recompute()
        checks["editable_height_recompute"] = doc.getObject("rubber").Shape.Volume > original
        App.closeDocument(doc.Name)
        restored = App.openDocument(str(out / (name + ".FCStd")))
        restored.recompute()
        checks["native_reopen_valid"] = all(
            o.Shape.isValid() for o in restored.Objects if hasattr(o, "Shape")
        )
        App.closeDocument(restored.Name)
        if not checks["editable_height_recompute"] or not checks["native_reopen_valid"]:
            raise ValueError("Native edit/reopen failed")
        (out / "checks.json").write_text(json.dumps(checks, indent=2) + "\n")
        print(name, "valid, editable, interference-free; metal gap", checks["metal_gap_mm"])
