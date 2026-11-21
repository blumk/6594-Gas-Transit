#!/bin/sh
# Bundles app.js (+ three.js) and inlines it into shell.html -> index.html
set -e
npx esbuild app.js --bundle --minify --format=iife --outfile=app.min.js
python3 - <<'PY'
s=open('shell.html').read(); js=open('app.min.js').read().replace('</script','<\\/script')
open('index.html','w').write(s.replace('/*APP*/',js))
PY
echo "built index.html"
