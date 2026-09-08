import os
import sys
import FreeCAD as App

FILE = r"C:\Users\Administrator\Desktop\unity_yaskawa_project\GP35L_3D\iges\base_axis.igs"
if not os.path.exists(FILE):
    print("not found:", FILE)
    sys.exit(1)

import Import
doc = App.newDocument("test")
try:
    Import.insert(FILE, "test")
    print("Import.insert OK, objects:", len(doc.Objects))
except Exception as e:
    print("Import.insert FAILED:", repr(e))
    output = App.Console.GetOutput()
    err = App.Console.GetError()
    print("CONSOLE OUT:", output[-2000:] if output else "(empty)")
    print("CONSOLE ERR:", err[-2000:] if err else "(empty)")
    sys.exit(1)

for obj in doc.Objects:
    lbl = obj.Label
    try:
        if hasattr(obj, "Shape"):
            bb = obj.Shape.BoundBox
            print(f"{lbl!r:50s} {obj.TypeId:30s} vol={obj.Shape.Volume:.0f} bbox=({bb.XMin:.1f},{bb.YMin:.1f},{bb.ZMin:.1f})-({bb.XMax:.1f},{bb.YMax:.1f},{bb.ZMax:.1f})")
        else:
            print(f"{lbl!r:50s} {obj.TypeId}")
    except Exception as e:
        print(lbl, "ERR", e)
App.closeDocument(doc.Name)
print("DONE")