# Renders tanker.blend with Cycles on the CPU: render_scene.py <width> <height> <samples> <out.png>. See AGENTS.md.
import bpy, sys, os
HERE=os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE,'tanker.blend'))
s=bpy.context.scene; W,H,SPP,out=int(sys.argv[-4]),int(sys.argv[-3]),int(sys.argv[-2]),os.path.abspath(sys.argv[-1])
s.render.engine='CYCLES'; s.cycles.device='CPU'; s.cycles.samples=SPP; s.cycles.use_denoising=True
s.render.resolution_x=W; s.render.resolution_y=H; s.render.resolution_percentage=100
s.render.filepath=out; s.render.image_settings.file_format='PNG'
bpy.ops.render.render(write_still=True)
