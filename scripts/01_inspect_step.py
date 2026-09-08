import os
import sys
import FreeCAD as App

STEP = r"C:\Users\Administrator\Desktop\unity_yaskawa_project\GP35L_3D\step\000_gp35l_asm_asm.stp"
if not os.path.exists(STEP):
    print("STEP not found:", STEP)
    sys.exit(1)

doc = App.openDocument(STEP)
name = os.path.basename(doc.FileName)
print("=== DOC ===", name)
for obj in doc.Objects:
    lbl = obj.Label
    kind = obj.TypeId
    try:
        if hasattr(obj, "Shape") and obj.Shape.Solids:
            n_sol = len(obj.Shape.Solids)
            bb = obj.Shape.BoundBox
            bbox = (round(bb.XMin,1), round(bb.YMin,1), round(bb.ZMin,1),
                    round(bb.XMax,1), round(bb.YMax,1), round(bb.ZMax,1))
            vol = round(obj.Shape.Volume, 0)
            print(f"{lbl!r:60s} {kind:28s} solids={n_sol} vol={vol:.0f} bbox={bbox}")
        else:
            print(f"{lbl!r:60s} {kind:28s} <no solids>")
    except Exception as e:
        print(f"{lbl!r:60s} {kind:28s} ERR {e}")
App.closeDocument(doc.Name)
print("DONE")