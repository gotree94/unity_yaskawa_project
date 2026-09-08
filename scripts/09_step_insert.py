import os
import sys
import FreeCAD as App
import Import
import Part

STEP = r"C:\Users\Administrator\Desktop\unity_yaskawa_project\GP35L_3D\step\000_gp35l_asm_asm.stp"
doc = App.newDocument("step_test")
try:
    Import.insert(STEP, "step_test")
    print("Import.insert OK")
except Exception as e:
    print("Import.insert FAILED:", repr(e))
    sys.exit(1)
App.ActiveDocument.recompute()
print("objects:", len(doc.Objects))

def all_solids(obj):
    shape = obj.Shape
    stack = [shape]
    out = []
    while stack:
        sh = stack.pop()
        try:
            sols = sh.Solids
        except Exception:
            sols = []
        if sols:
            out.extend(sols)
            continue
        try:
            stack.extend(sh.ChildShapes)
        except Exception:
            pass
    return out

count = 0
for obj in doc.Objects:
    if not hasattr(obj, "Shape"):
        continue
    try:
        sols = all_solids(obj)
    except Exception as e:
        print(obj.Label, "ERR", repr(e)); continue
    vol = sum(s.Volume for s in sols)
    print(f"{obj.Label!r:40s} type={obj.TypeId:22s} solids={len(sols)} vol={vol:.0f}")
    count += 1
    if count > 40:
        break
print("DONE")