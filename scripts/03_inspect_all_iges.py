import os
import sys
import FreeCAD as App
import Import

DIR = r"C:\Users\Administrator\Desktop\unity_yaskawa_project\GP35L_3D\iges"
parts = ["base_axis", "s_axis", "l_axis", "u_axis", "r_axis", "b_axis", "t_axis"]

for name in parts:
    path = os.path.join(DIR, name + ".igs")
    if not os.path.exists(path):
        print(f"--- {name}: MISSING FILE")
        continue
    doc = App.newDocument(name)
    try:
        Import.insert(path, name)
    except Exception as e:
        print(f"--- {name}: IMPORT FAILED {e!r}")
        App.closeDocument(doc.Name)
        continue
    for obj in doc.Objects:
        if hasattr(obj, "Shape"):
            bb = obj.Shape.BoundBox
            s = obj.Shape
            print(f"{name:10s} label={obj.Label!r:20s} solids={len(s.Solids)} vol={s.Volume:12.0f} "
                  f"bboxX=[{bb.XMin:9.2f},{bb.XMax:9.2f}] bboxY=[{bb.YMin:9.2f},{bb.YMax:9.2f}] bboxZ=[{bb.ZMin:9.2f},{bb.ZMax:9.2f}]")
    App.closeDocument(doc.Name)
print("DONE")