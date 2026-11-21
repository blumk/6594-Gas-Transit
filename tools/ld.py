# LDraw resolver/flattener. Fetches library files on demand from the GitHub mirror of the LDraw parts library (CC BY).
import os, sys, json, subprocess, re
BASE='https://raw.githubusercontent.com/gkjohnson/ldraw-parts-library/master/complete/ldraw/'
CACHE=os.path.join(os.path.dirname(os.path.abspath(__file__)),'cache'); os.makedirs(CACHE,exist_ok=True)
def fetch(rel):
    p=os.path.join(CACHE, rel.replace('/','__'))
    if os.path.exists(p):
        d=open(p,encoding='utf-8',errors='replace').read()
        return None if d=='__404__' else d
    r=subprocess.run(['curl','-sS','-L','-w','%{http_code}','-o',p+'.tmp',BASE+rel],capture_output=True,text=True)
    if r.stdout.strip()=='200':
        os.rename(p+'.tmp',p); return open(p,encoding='utf-8',errors='replace').read()
    open(p,'w').write('__404__'); 
    if os.path.exists(p+'.tmp'): os.remove(p+'.tmp')
    return None
_files={}
def load(name):
    n=name.strip().lower().replace('\\','/')
    if n in _files: return _files[n]
    cands=['parts/'+n,'p/'+n] if not n.startswith(('48/','8/')) else ['p/'+n]
    txt=None
    for c in cands:
        txt=fetch(c)
        if txt is not None: break
    _files[n]=txt.splitlines() if txt is not None else None
    return _files[n]
def desc(name):
    L=load(name); 
    return L[0][2:].strip() if L else name
def mul(A,B): # 3x4 affine [a..i, x,y,z] as (R 3x3 row-major, t)
    Ra,ta=A; Rb,tb=B
    R=[sum(Ra[i*3+k]*Rb[k*3+j] for k in range(3)) for i in range(3) for j in range(3)]
    t=[sum(Ra[i*3+k]*tb[k] for k in range(3))+ta[i] for i in range(3)]
    return (R,t)
def ap(M,v):
    R,t=M; return [R[0]*v[0]+R[1]*v[1]+R[2]*v[2]+t[0], R[3]*v[0]+R[4]*v[1]+R[5]*v[2]+t[1], R[6]*v[0]+R[7]*v[1]+R[8]*v[2]+t[2]]
I=([1,0,0,0,1,0,0,0,1],[0,0,0])
def flatten(name, M=I, col=16, out=None, depth=0):
    """out: {'tris':{col:[...]}, 'lines':[...]}"""
    if out is None: out={'tris':{}, 'lines':[], 'missing':set()}
    L=load(name)
    if L is None: out['missing'].add(name); return out
    for ln in L:
        f=ln.split()
        if not f: continue
        t=f[0]
        if t=='1' and len(f)>=15:
            c=int(f[1]) if f[1].lstrip('-').isdigit() else 16
            c=col if c==16 else c
            v=list(map(float,f[2:14]))
            flatten(' '.join(f[14:]), mul(M,(v[3:12],v[0:3])), c, out, depth+1)
        elif t=='2' and len(f)>=8:
            v=list(map(float,f[2:8])); out['lines']+=ap(M,v[0:3])+ap(M,v[3:6])
        elif t in('3','4'):
            n=3 if t=='3' else 4
            if len(f)<2+3*n: continue
            c=int(f[1]) if f[1].lstrip('-').isdigit() else 16
            c=col if c==16 else c
            v=list(map(float,f[2:2+3*n])); P=[ap(M,v[i*3:i*3+3]) for i in range(n)]
            T=out['tris'].setdefault(c,[])
            T+=P[0]+P[1]+P[2]
            if n==4: T+=P[0]+P[2]+P[3]
    return out
