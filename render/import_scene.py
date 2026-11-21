# Imports tanker.mpd into Blender with the ImportLDraw add-on and saves tanker.blend. See AGENTS.md.
import sys, os, bpy
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,os.path.join(HERE,'ImportLDraw'))
from loadldraw import loadldraw
O=loadldraw.Options
O.ldrawDirectory=os.environ.get('LDRAW_DIR',os.path.join(HERE,'ldraw'))
O.useLogoStuds=False; O.useLSynthParts=False; O.useUnofficialParts=False
O.resolution='Standard'; O.useColourScheme='lgeo'; O.gaps=True; O.addBevelModifier=True; O.bakeBevels=True
O.addWorldEnvironmentTexture=True; O.addGroundPlane=True; O.positionCamera=True; O.setRenderSettings=True; O.importCameras=False
O.instructionsLook=False; O.verbose=1
bpy.ops.wm.read_factory_settings(use_empty=False)
loadldraw.loadFromFile(None,os.path.join(HERE,'tanker.mpd'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE,'tanker.blend'))
