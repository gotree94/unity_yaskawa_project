import os
import math
import FreeCAD as App
import Part
import Import

DIR = r"C:\Users\Administrator\Desktop\unity_yaskawa_project\GP35L_3D\iges"
parts = ["base_axis", "s_axis", "l_axis", "u_axis", "r_axis", "b_axis", "t_axis"]

def all_solids_recursive(shape, depth=0):
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
        for c in subs:
            for s in all_solids_recursive(c, depth + 1):
                yield s
        return
    except Exception:
        pass
    try:
        for c in shape.Compounds:
            for s in all_solids_recursive(c, depth + 1):
                yield s
    except Exception:
        pass

def revolved_axis(face):
    """Return (axis_unit_vec, axis_point, radius) or None."""
    surf = face.Surface
    try:
        u0, u1, v0, v1 = surf.bounds()
    except Exception:
        return None
    if not (u1 > u0 and v1 > v0):
        return None
    um = (u0 + u1) / 2.0
    try:
        A = face.valueAt(um, v0)
        B = face.valueAt(um, v0 + (v1 - v0) * 0.25)
        C = face.valueAt(um, v0 + (v1 - v0) * 0.5)
    except Exception:
        return None
    p = B.sub(A)
    q = C.sub(A)
    n = p.cross(q)
    ln = n.Length
    if ln < 1e-6:
        return None
    n.normalize()
    pu = p.Length
    if pu < 1e-6:
        return None
    u = p.multiply(1.0 / pu)
    w = n.cross(u)
    qw = q.dot(w)
    if abs(qw) < 1e-9:
        return None
    a = pu / 2.0
    b = (q.dot(q) - 2.0 * a * q.dot(u)) / (2.0 * qw)
    O = A.add(u.multiply(a)).add(w.multiply(b))
    r = math.sqrt(a * a + b * b)
    if r < 1e-6:
        return None
    return (n, O, r)

def axis_label(d):
    x, y, z = abs(d.x), abs(d.y), abs(d.z)
    m = max(x, y, z)
    if m < 0.5:
        return "?"
    if m == x: return "X"
    if m == y: return "Y"
    return "Z"

for name in parts:
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
        print(f"=== {name}: NO SOLID")
        App.closeDocument(doc.Name)
        continue
    bb = best.BoundBox
    rows = []
    for f in best.Faces:
        if f.Surface.TypeId != "Part::GeomSurfaceOfRevolution":
            continue
        res = revolved_axis(f)
        if res is None:
            continue
        n, O, r = res
        if r < 20.0:
            continue
        if not (bb.XMin - 60 <= O.x <= bb.XMax + 60 and
                bb.YMin - 60 <= O.y <= bb.YMax + 60 and
                bb.ZMin - 60 <= O.z <= bb.ZMax + 60):
            continue
        rows.append((r, O, n))
    rows.sort(key=lambda t: -t[0])
    print(f"=== {name}: revolved axes r>=20 whose point inside part = {len(rows)}")
    for r, O, n in rows[:16]:
        print(f"   r={r:8.1f}  O=({O.x:9.2f},{O.y:9.2f},{O.z:9.2f})  dir={axis_label(n)} ({n.x:+.4f},{n.y:+.4f},{n.z:+.4f})")
    App.closeDocument(doc.Name)
print("DONE")