import os
import FreeCAD as App
import Import

DIR = r"C:\Users\Administrator\Desktop\unity_yaskawa_project\GP35L_3D\iges"
for name in ["s_axis", "l_axis"]:
    path = os.path.join(DIR, name + ".igs")
    doc = App.newDocument(name)
    Import.insert(path, name)
    best = None; best_vol = 0
    for obj in doc.Objects:
        if not hasattr(obj, "Shape"):
            continue
        for s in obj.Shape.Solids:
            if s.Volume > best_vol:
                best_vol = s.Volume; best = s
    from collections import Counter
    cnt = Counter()
    areas = Counter()
    for f in best.Faces:
        try:
            t = f.Surface.TypeId
        except Exception:
            t = "ERR"
        cnt[t] += 1
        areas[t] += f.Area
    print(f"=== {name}: faces={len(best.Faces)}")
    for t, n in cnt.most_common():
        print(f"   {t:35s} n={n:6d} area={areas[t]:12.0f}")
    App.closeDocument(doc.Name)
print("DONE")