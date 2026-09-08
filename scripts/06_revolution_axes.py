import os
import sys
import traceback
import FreeCAD as App
import Part
import Import

DIR = r"C:\Users\Administrator\Desktop\unity_yaskawa_project\GP35L_3D\iges"
parts = ["base_axis", "s_axis", "l_axis", "u_axis", "r_axis", "b_axis", "t_axis"]

def axis_label(d):
    x, y, z = abs(d.x), abs(d.y), abs(d.z)
    if x > 0.9: return "X"
    if y > 0.9: return "Y"
    if z > 0.9: return "Z"
    return "?"

def all_solids_recursive(shape, depth=0):
    """Yield all solids contained in a shape (top-level only recursion)."""
    if depth > 4:
        return
    try:
        sols = shape.Solids
    except Exception:
        sols = []
    if sols:
        for s in sols:
            yield s
        return
    try:
        subs = shape.ChildShapes
    except Exception:
        subs = []
    if subs:
        for c in subs:
            for s in all_solids_recursive(c, depth + 1):
                yield s
        return
    try:
        for c in shape.Compounds:
            for s in all_solids_recursive(c, depth + 1):
                yield s
    except Exception:
        pass

for name in parts:
    try:
        path = os.path.join(DIR, name + ".igs")
        doc = App.newDocument(name)
        Import.insert(path, name)
        App.ActiveDocument.recompute()
        best = None; best_vol = 0
        for obj in doc.Objects:
            if not hasattr(obj, "Shape"):
                continue
            for s in all_solids_recursive(obj.Shape):
                v = s.Volume
                if v > best_vol:
                    best_vol = v; best = s
        if best is None:
            print(f"=== {name}: NO SOLID (objects={[o.Label for o in doc.Objects]})")
            App.closeDocument(doc.Name)
            continue
        revs = []
        for f in best.Faces:
            surf = f.Surface
            if surf.TypeId != "Part::GeomSurfaceOfRevolution":
                continue
            try:
                loc = surf.Location
                dirv = surf.Direction.normalize()
            except Exception:
                continue
            rmin = None
            for v in f.Vertexes:
                rel = v.Point.sub(loc)
                perp = rel.sub(dirv.multiply(rel.dot(dirv)))
                d = perp.Length
                rmin = d if rmin is None else min(rmin, d)
            r = rmin or 0.0
            if r > 20.0:
                revs.append((r, loc, dirv))
        revs.sort(key=lambda t: -t[0])
        print(f"=== {name}: revolution faces r>20mm = {len(revs)}  (solid vol={best_vol:.0f})")
        for r, loc, dirv in revs[:14]:
            print(f"   r={r:8.1f}  loc=({loc.x:9.2f},{loc.y:9.2f},{loc.z:9.2f})  axis={axis_label(dirv)} dir=({dirv.x:+.3f},{dirv.y:+.3f},{dirv.z:+.3f})")
        App.closeDocument(doc.Name)
    except Exception as e:
        print(f"!!! {name} FAILED:", repr(e))
        traceback.print_exc()
print("DONE")