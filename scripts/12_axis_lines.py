import sys
import os
sys.path.insert(0, r"C:\Users\Administrator\Downloads\FreeCAD_1.1.1-Windows-x86_64-py311\bin")
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

def circle_info(edge):
    try:
        c = edge.Curve
    except Exception:
        return None
    if c.TypeId != "Part::GeomCircle":
        return None
    return (c.Radius, c.Center)

def fit_line(points):
    n = len(points)
    centro = App.Vector(0, 0, 0)
    for p in points:
        centro = centro.add(p)
    centro = centro.multiply(1.0 / n)
    spreadmax = 0.0
    for p in points:
        d = p.sub(centro)
        spreadmax = max(spreadmax, d.Length)
    if spreadmax < 1e-6:
        return (App.Vector(1, 0, 0), centro)
    cxx = cyy = czz = cxy = cxz = cyz = 0.0
    for p in points:
        d = p.sub(centro)
        cxx += d.x * d.x; cyy += d.y * d.y; czz += d.z * d.z
        cxy += d.x * d.y; cxz += d.x * d.z; cyz += d.y * d.z
    m = [[cxx, cxy, cxz], [cxy, cyy, cyz], [cxz, cyz, czz]]
    v = [1.0, 1.0, 1.0]
    for _ in range(30):
        nv = [m[i][0] * v[0] + m[i][1] * v[1] + m[i][2] * v[2] for i in range(3)]
        ln = math.sqrt(max(sum(x * x for x in nv), 1e-30))
        v = [x / ln for x in nv]
    return (App.Vector(*v), centro)

def axis_label(d):
    if math.isnan(d.x) or math.isnan(d.y) or math.isnan(d.z):
        return "?"
    m = max(abs(d.x), abs(d.y), abs(d.z))
    if m < 0.5:
        return "?"
    return ["X", "Y", "Z"][[abs(d.x), abs(d.y), abs(d.z)].index(m)]

doc = App.newDocument("step")
Import.insert(STEP, "step")
App.ActiveDocument.recompute()
print("objects:", len(doc.Objects))

for comp, labels in COMPONENTS.items():
    sols = component_solids(doc, labels)
    if not sols:
        print(f"=== {comp}: NO SOLIDS")
        continue
    circles = []
    for s in sols:
        for e in s.Edges:
            ci = circle_info(e)
            if ci is not None and ci[0] >= 18.0:
                circles.append(ci)
    if not circles:
        print(f"=== {comp}: no circles")
        continue
    groups = []
    for cr, ce in circles:
        best = None
        best_err = None
        for g in groups:
            if abs(g[0] - cr) > 3.0:
                continue
            dirv, pt = fit_line([x[1] for x in g[1]])
            rel = ce.sub(pt)
            err = rel.sub(dirv.multiply(rel.dot(dirv))).Length
            if err < 4.0:
                if best_err is None or err < best_err:
                    best_err = err
                    best = g
        if best is not None:
            best[1].append((cr, ce))
        else:
            groups.append([cr, [(cr, ce)]])
    groups.sort(key=lambda g: (-len(g[1]), -g[0]))
    print(f"=== {comp}: {len(circles)} circle edges -> {len(groups)} axis groups")
    for r0, members in groups[:12]:
        pts = [p for (_, p) in members]
        dirv, pt = fit_line(pts)
        spread = 0.0
        for p in pts:
            rel = p.sub(pt)
            spread = max(spread, rel.sub(dirv.multiply(rel.dot(dirv))).Length)
        print(f"   r={r0:7.1f} n={len(members):3d}  axis pt=({pt.x:8.2f},{pt.y:8.2f},{pt.z:8.2f})  dir={axis_label(dirv)} ({dirv.x:+.4f},{dirv.y:+.4f},{dirv.z:+.4f}) lateral_spread={spread:.2f}")
App.closeDocument(doc.Name)
print("DONE")