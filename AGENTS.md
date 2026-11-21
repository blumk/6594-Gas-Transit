# 3D Build Guide (agent instructions)

An interactive WebGL step-by-step assembly guide for brick models. It is one self-contained page (`index.html`, no
server) with two models. It opens on **6594 Gas Transit**. The Tow tray is `hidden: true` in `MODELS`, so it has no
button and only opens with `#tow-tray` in the URL (the switch buttons appear again if two models are not hidden):

- **Tow tray**: hand-modelled in code from line-art schematics (7 steps, 22 parts).
- **6594 Gas Transit** (a tanker truck, called "Tanker truck" below): imported from an LDraw model file (25 steps,
  119 parts). The header and page title use the set's official number and name.

A separate Blender pipeline in `render/` makes a photoreal still of the tanker truck.

## Layout

- `app.js`           Source: three.js scene, Tow tray part geometry and steps, model switching, UI wiring.
- `shell.html`       Page markup and CSS. The marker `/*APP*/` is replaced by the bundle.
- `build.sh`         Bundles `app.js` (and `truck-data.json`) with esbuild and inlines it into `index.html`.
- `index.html`       Built output. Never edit by hand; rebuild instead.
- `truck-data.json`  Generated data for the Tanker truck. Never edit by hand; regenerate with `tools/analyze.py`.
- `tools/`           `ld.py` (LDraw file resolver and flattener), `analyze.py` (steps and export),
                     `6594-compact.txt` (the model's part list).
- `render/`          Blender scripts, the model as `.mpd`, and the rendered still.
- `shot.js`          Playwright smoke test: for each model, a mid-drop frame, a spread of steps, exploded view, phone layout.
- `package.json`     Dependencies: `three`, `esbuild`.

## Commands

    npm install                                   # once
    ./build.sh                                    # regenerate index.html
    node shot.js                                  # screenshots; needs playwright + chromium
    python3 tools/analyze.py truck-data.json      # regenerate the Tanker truck data, then ./build.sh
    python3 tools/analyze.py                      # print the step table only
    python3 tools/analyze.py --auto               # same, with the inferred order instead of the printed one

Open `index.html` directly in a browser to view.

## Landing page

The page opens on a landing view (`showLanding(true)`, class `landing` on `<body>`): title with the model year in
parentheses, above it the path line "LEGO System > Town > Vehicles" (product line, theme, subtheme; plain text, no logo),
no part counts, chips or written description, a primary "Build now" button that goes to step 1 and a secondary "Official
manual" link to `landing.manual` (the set's brickinstructions.com page; falls back to the `more` link). Beside it the finished model turns slowly and can be dragged, with its own Explode slider (same value as
the control bar's, reset to 0 by "Build now"). The content comes
from `landing` in the model's `MODELS` entry; a model without `landing` skips it. The "Home" button in the control bar returns to it.

## How the page is organised

- `MODELS` in `app.js` lists the models (`name`, `hash`, `steps`, optional `credit` and `more` link).
  `loadModel(i)` clears the scene and rebuilds parts, part pictures, camera framing and the step list.
- A step is `{ title, parts }`. There is no description text per step; keep it that way.
- Parts drop in from above unless `from: [x, y, z]` gives another arrival direction. The explode slider moves parts along
  the same direction, scaled so long models do not fly apart.
- The camera target and zoom ease to fit everything built so far (`fits`).
- To add a third model: produce a steps array (hand-written like `SUB_STEPS`, or generated like `truck-data.json`) and add
  an entry to `MODELS`. Nothing else needs to change.

## Tow tray (hand-modelled)

Driven by the `SUB_STEPS` array at the top of `app.js`. A part is:

    { t, s: [x, z, plates], p: [x, z, plates], c, n, rot?, from?, inn? }

- Units: 1 = one stud horizontally; vertical values are in plates (1 plate = 0.4, brick = 3 plates).
- Axes: x = length (tow ring end is x = 0), z = width, y = up. `p` is the part's minimum corner.
- `t` types: `box`, `fence`, `hitch`, `shaftbrick`, `bracket`, `linkfork`, `linktongue`, `clip`, `jawtop`, `jaw`, `tank`,
  `cone`, `prop`, `dome`. The round and eight-sided types lie along x, are centred in their `s` box and ignore `rot`.
- `rot` = quarter turns about y. At rot 0 the `fence` lattice is on the +z edge and the `hitch` ring is off the +x end.
  `s` is always the final footprint.
- `inn` is only for `tank`: -1 or +1, the z side that faces the tray and carries the row of studs.
- `c` is a key in `COL`; `n` is the display name in the parts list.
- To add a part type, add a branch in `buildRaw(p)` that fills a `THREE.Group` using `addMesh` (which also adds the
  outline edges) and `studs`.
- Shapes follow the user's schematics (steps 1 to 3, 4 to 7, the detailed step 5 arm, the higher-resolution 6 and 7).
  The canopy is a 6 x 6 stud, even eight-sided dome with clear framed panes.

## Tanker truck (imported)

- Source: LDraw Official Model Repository file `6594-1.mpd` by Iván Sánchez Ortega (CC BY 2.0), saved in compact form as
  `tools/6594-compact.txt` (one line per part: colour, position, 3 x 3 matrix, file). Part shapes come from the LDraw
  parts library (CC BY), fetched on demand by `tools/ld.py` from the GitHub mirror `gkjohnson/ldraw-parts-library` and
  cached in `tools/cache/`.
- Steps: the `OFFICIAL` table in `tools/analyze.py` assigns every part to one of 25 steps, following the order of the
  set's printed instructions (truck 1 to 10, then trailer 1 to 15). The sheet builds the trailer axles upside down and
  some parts as side assemblies; here every part goes on in place, and parts marked `below` are pushed up from
  underneath. The script fails if any part is unassigned or a selector matches nothing.
- `--auto` uses the inferred order instead. It takes each part's bounding box and stud axis, links a part to the parts it
  rests on, then releases parts lowest first into steps of at most 7 parts and 4 kinds, wheels last. The `AFTER` table
  fixes the cases geometry cannot decide (parts held by a clip, the ball pushed into its socket, the sideways reel stack).
- Export format: part geometry quantised to 1/50 LDraw unit as base64 (indexed triangles plus edge lines); each step part
  has `t: 'ld'`, `id`, colour key `L<LDraw code>`, `m` (3 x 4 matrix in stud units, y up) and `from`.
- In `app.js` imported parts use the same flat three-tone shader, double sided because LDraw winding is not reliable.
  They get no white seams.
- The LDraw file lacks the steering wheel and hose string that the printed sheet shows. Do not invent them.

## Visual style

Printed instruction sheet look: flat fills, black outlines, orthographic (isometric) camera.

- Tow tray palette in `COL`: black parts (top #6D6F6D, sides #353735, deep shadow #070707), yellow #FFF131, red #F3694E,
  transparent blue #84CAF6 (canopy, 28% opacity).
- Tanker truck: `theme: 'manual'` in `MODELS` puts the class `manual` on `<body>` and gives the page the look of a
  printed instruction sheet: sky to grass page gradient, pale yellow boxes with thin black rules, heavy black numbers.
  Its part colours are the `SHEET` palette in `app.js` (black parts as dark grey with lighter tops, clean white, bright
  red and green, transparent red shown as pink). The Tow tray keeps the page colours listed below.
- `mat()` is a flat shader that picks one of three tones of the part colour by face direction. No lights, no gradients
  on parts, never a second hue on one part.
- Tow tray only: stud tops take the part colour and stud walls are black; holes, hollow stud centres, recesses and nose
  cone tips are black (`boreMat`); where two black parts touch, `seams()` redraws that outline as a thin white line once
  the part is seated.
- Transparent parts are drawn after everything else so what is behind shows through tinted; their own edges stay black.
- Page: gradient #F4F9F3 (top) to #66BAD2 (bottom), the only gradient. Callout and side panel #FDF9AF with black
  borders. Arrows and step numbers solid black.
- `#callout` (top right) shows pictures of the parts added in the current step, made by `makeThumbs()` and reused in the
  parts list. `pointer()` draws the elbow line from the callout to the new parts. `makeArrow()` builds the placement
  arrows shown while a part hovers.

## Behavior to preserve

- New parts of the current step hover with placement arrows, then move into place. Outlines stay black (no highlight).
- Controls: model buttons, Home (returns to the landing page; it replaced the Back button, so going back a step is by
  dot or left arrow key), Next, numbered step dots, Play build, Auto rotate, Explode slider, arrow keys.
- With more than 10 steps the dots shrink and wrap and the step number moves up (`.many` classes).
- Steps carry `g` (sub-assembly) and `k` (number within it): the Tanker truck counts Truck 1 to 10, then Trailer 1 to 15,
  as the printed sheet does. The big number, the step line and the dot rows all use `k`.
- The page stays self-contained: inline JS and CSS, no external requests. The only outside reference is the plain
  "More details" link for the Tanker truck.

## Photoreal render (`render/`)

Separate from the web page. Uses Blender as a Python module (`pip install bpy`, 5.3 tested) and the ImportLDraw add-on
(https://github.com/TobyLobster/ImportLDraw, GPL 2).

    git clone https://github.com/TobyLobster/ImportLDraw render/ImportLDraw
    python3 render/import_scene.py                                   # tanker.mpd -> tanker.blend
    python3 render/render_scene.py 1920 1080 72 tanker-truck-render.png

- `import_scene.py` imports `tanker.mpd` (the model without stickers and figure) with the realistic look, bevelled
  edges, ground plane, environment light and an automatically placed camera, and saves `tanker.blend`.
- `render_scene.py <width> <height> <samples> <out.png>` renders with Cycles on the CPU with denoising. 1920 x 1080 at
  72 samples took about 5 minutes on 2 cores.
- Both need an LDraw parts folder: set `LDRAW_DIR`, or leave it unset to use `render/ldraw`. Only the files the model
  references are needed; `tools/ld.py` can fetch them.
- Stud logos are off (`useLogoStuds = False`). Keep them off.

## Content rules

- Left out of the Tanker truck on purpose, in the guide and in the render: the stickers, the printed pattern on one
  slope (a plain slope is used) and the figure. They are brand artwork and a trademarked character. Do not add them,
  and do not add brand logos or stud logos anywhere.
- From the printed instruction sheet only the order of assembly and the general colour theme are used. Do not copy its artwork, logos, layout or scans into
  the project; the LDraw licence covers the LDraw file and parts library, not the sheet.
- Keep the credit line and the "More details" link in `MODELS`; the CC BY sources require the credit.
- Keep the Tow tray's shapes and visual style original to the user's schematics.
- No em dashes in user-facing text.
- After any change: rebuild, run `node shot.js`, and look at the last step and the exploded view of both models.
