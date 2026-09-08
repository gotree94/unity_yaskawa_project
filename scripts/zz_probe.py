import os
import FreeCAD as App
import Import
STEP = r'C:\Users\Administrator\Desktop\unity_yaskawa_project\GP35L_3D\step\000_gp35l_asm_asm.stp'
doc = App.newDocument('d2')
Import.insert(STEP, 'd2')
App.ActiveDocument.recompute()
labels = ['BASE_AXIS']
for obj in doc.Objects:
    if obj.Label in labels:
        print('FOUND', repr(obj.Label), obj.TypeId, hasattr(obj,'Shape'))
        try:
            sols = obj.Shape.Solids
            print('  solids=', len(sols))
        except Exception as e:
            print('  solids ERR', repr(e))
App.closeDocument(doc.Name)
print('DONE')
