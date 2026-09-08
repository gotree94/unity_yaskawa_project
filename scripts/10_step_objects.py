import os
import sys
import FreeCAD as App
import Import

STEP = r"C:\Users\Administrator\Desktop\unity_yaskawa_project\GP35L_3D\step\000_gp35l_asm_asm.stp"
doc = App.newDocument("step")
Import.insert(STEP, "step")
App.ActiveDocument.recompute()
for obj in doc.Objects:
    tag = ""
    try:
        if hasattr(obj, "Shape"):
            bb = obj.Shape.BoundBox
            tag = f"bbox=({bb.XMin:.1f},{bb.YMin:.1f},{bb.ZMin:.1f})-({bb.XMax:.1f},{bb.YMax:.1f},{bb.ZMax:.1f}) vol={obj.Shape.Volume:.0f}"
    except Exception:
        pass
    print(f"{obj.Label!r:25s} {obj.TypeId:22s} {tag} attrs={len([a for a in dir(obj) if not a.startswith('_')])}")
print("DONE")