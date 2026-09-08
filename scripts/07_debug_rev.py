import os
import FreeCAD as App
import Import

path = r"C:\Users\Administrator\Desktop\unity_yaskawa_project\GP35L_3D\iges\t_axis.igs"
doc = App.newDocument("t")
Import.insert(path, "t")
best = None; best_vol = 0
for obj in doc.Objects:
    if not hasattr(obj, "Shape"):
        continue
    for s in obj.Shape.Solids:
        if s.Volume > best_vol:
            best_vol = s.Volume; best = s
print("faces:", len(best.Faces))
shown = 0
for f in best.Faces:
    surf = f.Surface
    if surf.TypeId == "Part::GeomSurfaceOfRevolution":
        shown += 1
        print("REV FACE", shown)
        print("  dir():", [a for a in dir(surf) if not a.startswith('_')][:40])
        try:
            ax = surf.Axis
            print("  Axis =", ax)
        except Exception as e:
            print("  Axis ERR:", repr(e))
        try:
            print("  BasisCurve:", surf.BasisCurve)
        except Exception as e:
            print("  BasisCurve ERR:", repr(e))
        if shown >= 3:
            break
App.closeDocument(doc.Name)
print("DONE")