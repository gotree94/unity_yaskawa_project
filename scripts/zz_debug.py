import os
import FreeCAD as App
import Import
STEP = r'C:\Users\Administrator\Desktop\unity_yaskawa_project\GP35L_3D\step\000_gp35l_asm_asm.stp'
doc = App.newDocument('dbg')
Import.insert(STEP, 'dbg')
App.ActiveDocument.recompute()
for obj in doc.Objects:
    has_sh = hasattr(obj, 'Shape')
    print(repr(obj.Label), obj.TypeId, 'hasShape=%s' % has_sh)
App.closeDocument(doc.Name)
print('DONE')
