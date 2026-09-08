import os
import sys
import FreeCAD as App
import Import

DIR = r"C:\Users\Administrator\Desktop\unity_yaskawa_project\GP35L_3D\iges"
parts = ["s_axis", "l_axis", "u_axis", "r_axis", "b_axis", "t_axis"]

def axis_label(d):
    x, y, z = abs(d.x), abs(d.y), abs(d.z)
    if x > 0.9: return "X"
    if y > 0.9: return "Y"
    if z > 0.9: return "Z"
    return "?"

for name in parts:
    path = os.path.join(DIR, name + ".igs")
    doc = App.newDocument(name)
    Import.insert(path, name)
    best = None; best_vol = 0
    for obj in doc.Objects:
        if not hasattr(obj, "Shape"):
            continue
        try:
            sols = obj.Shape.Solids
        except Exception:
            sols = []
        for s in sols:
            v = s.Volume
            if v > best_vol:
                best_vol = v; best = s
    if best is None:
        print(f"=== {name}: NO SOLID")
        App.closeDocument(doc.Name)
        continue
    cyls = []
    for f in best.Faces:
        try:
            surf = f.Surface
        except Exception:
            continue
        if surf.TypeId == "Geom::Cylinder":
            r = surf.Radius
            if r > 20.0:
                c = surf.Center
                d = surf.Axis.normalize()
                cyls.append((r, c, d))
    cyls.sort(key=lambda t: -t[0])
    print(f"=== {name} (solid vol={best_vol:.0f}) big cylinders (r>20mm):")
    for r, c, d in cyls[:10]:
        print(f"   r={r:8.1f}  center=({c.x:9.2f},{c.y:9.2f},{c.z:9.2f})  axis={axis_label(d)}  dir=({d.x:+.3f},{d.y:+.3f},{d.z:+.3f})")
    App.closeDocument(doc.Name)
    print("FLUSH_OK")
print("DONE")