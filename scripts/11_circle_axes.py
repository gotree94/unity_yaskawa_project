import os
import math
import FreeCAD as App
import Part
import Import

STEP = r"C:\Users\Administrator\Desktop\unity_yaskawa_project\GP35L_3D\step\000_gp35l_asm_asm.stp"

COMPONENTS = {
    "BASE_AXIS": ["BASE_AXIS"],
    "S_AXIS":    ["SOLID"],
    "L_AXIS":    ["L_AXIS", "L_AXIS001"],
    "U_AXIS":    ["SOLID001"],
    "R_AXIS":    ["SOLID002"],
    "B_AXIS":    ["B_AXIS"],
    "T_AXIS":    ["SOLID003"],
}

def component_solids(doc, labels):
    sh = None
    for obj in doc.Objects:
        if obj.Label in labels and hasattr(obj, "Shape"):
            sh = obj.Shape
            break
    if sh is None:
        return None
    stack = [sh]
    out = []
    while stack:
        s = stack.pop()
        try:
            sols = s.Solids
        except Exception:
            sols = []
        if sols:
            out.extend(sols)
        else:
            try:
                stack.extend(s.ChildShapes)
            except Exception:
                pass
    return out

def circle_info(edge, tol=0.02):
    """Return (radius, center, normal) if edge is exactly circular."""
    try:
        c = edge.Curve
    except Exception:
        return None
    if c.TypeId != "Part::GeomCircle":
        return None
    return (c.Radius, c.Center, c.Axis)

doc = App.newDocument("step")
Import.insert(STEP, "step")
App.ActiveDocument.recompute()

for comp, labels in COMPONENTS.items():
    sols = component_solids(doc, labels)
    if not sols:
        print(f"=== {comp}: NO SOLIDS")
        continue
    circles = []
    for s in sols:
        for e in s.Edges:
            ci = circle_info(e)
            if ci is None:
                continue
            r, cen, nrm = ci
            if r < 20.0:
                continue
            circles.append((r, cen, nrm))
    if not circles:
        print(f"=== {comp}: no circle edges r>=20")
        continue
    # cluster by axis (normal dir + axis point offset) and radius
    clusters = []
    for c in circles:
        placed = False
        for cl in clusters:
            r0, cen0, nrm0, pts = cl
            if abs(r0 - c[0]) > 3.0:
                continue
            if abs(nrm0.dot(c[2])) < 0.98:
                continue
            # lateral distance of center from first center projected perpendicular
            rel = c[1].sub(cen0)
            off = rel.sub(nrm0.multiply(rel.dot(nrm0))).Length
            if off > 3.0:
                continue
            cl[3].append(c[1])
            cl[1] = cen0.add(rel.multiply(0.001))  # keep first point approx
            placed = True
            break
        if not placed:
            clusters.append([c[0], c[1], c[2], [c[1]]])
    clusters.sort(key=lambda cl: (-len(cl[3]), -cl[0]))
    print(f"=== {comp}: {len(circles)} circle edges -> {len(clusters)} axis clusters")
    for r0, cen0, nrm0, pts in clusters[:10]:
        # average center
        avg = App.Vector(0,0,0)
        for p in pts:
            avg = avg.add(p)
        avg = avg.multiply(1.0/len(pts))
        ax = "?"
        d = nrm0
        m = max(abs(d.x), abs(d.y), abs(d.z))
        if m > 0.9:
            ax = ["X","Y","Z"][[abs(d.x),abs(d.y),abs(d.z)].index(m)]
        print(f"   r={r0:8.1f} n={len(pts):2d}  center=({avg.x:9.2f},{avg.y:9.2f},{avg.z:9.2f})  dir={ax} ({d.x:+.4f},{d.y:+.4f},{d.z:+.4f})")
App.closeDocument(doc.Name)
print("DONE")