# Reverse-engineers a build order for the flattened model: contact graph -> supports -> layered steps.
import sys, json, re, base64, struct
import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import ld
SKIP_SUB={'6594 - Minifig.ldr'}
SUBST={'3660p01.dat':'3660.dat'}          # printed pattern -> plain part
def is_sticker(n): return ld.desc(n).lower().startswith('sticker')
subs={}; cur=None
for l in open(''+os.path.dirname(os.path.abspath(__file__))+'/6594-compact.txt'):
    l=l.rstrip('\n')
    if l.startswith('F '): cur=l[2:]; subs[cur]=[]; continue
    f=l.split(); v=list(map(float,f[1:13])); subs[cur].append((int(f[0]), (v[3:12],v[0:3]), ' '.join(f[13:])))
main=next(iter(subs))
inst=[]  # dicts
skipped=[]
for c,M,name in subs[main]:
    if name in SKIP_SUB: skipped.append(name); continue
    for c2,M2,n2 in subs[name]:
        if is_sticker(n2): skipped.append(n2+' '+ld.desc(n2)); continue
        n2=SUBST.get(n2,n2)
        inst.append({'lp':[round(x) for x in M2[1]],'sub':name.replace('6594 - ','').replace('.ldr',''),'id':n2[:-4],'file':n2,'c':c2 if c2!=16 else c,'M':ld.mul(M,M2)})
# app conversion: (x,y,z)_app = (z,-y,x)/20
C=([0,0,1/20, 0,-1/20,0, 1/20,0,0],[0,0,0])
geo={}
def G(file):
    if file not in geo: geo[file]=ld.flatten(file)
    return geo[file]
for it in inst:
    g=G(it['file']); A=ld.mul(C,it['M']); it['A']=A
    pts=[]
    for T in g['tris'].values(): pts+= [T[i:i+3] for i in range(0,len(T),3)]
    W=[ld.ap(A,p) for p in pts]
    it['lo']=[min(w[k] for w in W) for k in range(3)]; it['hi']=[max(w[k] for w in W) for k in range(3)]
    R=A[0]; u=[-R[1],-R[4],-R[7]]; n=sum(x*x for x in u)**.5; u=[round(x/n) for x in u]; it['u']=u
    it['name']=re.sub(r'\s+',' ',ld.desc(it['file'])).replace('~Moved to ','')
    det=R[0]*(R[4]*R[8]-R[5]*R[7])-R[1]*(R[3]*R[8]-R[5]*R[6])+R[2]*(R[3]*R[7]-R[4]*R[6]); it['det']=det
for f in set(i['file'] for i in inst):
    if ld.desc(f).startswith('~Moved to'):
        tgt=ld.desc(f).split('~Moved to ')[1].strip()+'.dat'
        for i in inst:
            if i['file']==f: i['name']=re.sub(r'\s+',' ',ld.desc(tgt))
WHEEL={'6014','6015'}
def ext(it,u):  # interval along signed axis u
    k=[abs(x) for x in u].index(1); s=u[k]
    a,b=it['lo'][k]*s,it['hi'][k]*s
    return min(a,b),max(a,b),k
def overlap(a,b,k,m=0.08):
    return all(min(a['hi'][j],b['hi'][j])-max(a['lo'][j],b['lo'][j])>m for j in range(3) if j!=k)
for a in inst: a['dep']=set(); a['from']=a['u'][:]
idx={id(i):n for n,i in enumerate(inst)}
def touch(a,b,m=0.05): return all(a['lo'][j]-m<=b['hi'][j] and b['lo'][j]-m<=a['hi'][j] for j in range(3))
for a in inst:
    amin,amax,k=ext(a,a['u'])
    for b in inst:
        if b is a or b['sub']!=a['sub'] or b['id'] in WHEEL or a['id'] in WHEEL: continue
        bmin,bmax,_=ext(b,a['u'])
        if overlap(a,b,k) and bmin<amin-0.03 and bmax>=amin-0.03: a['dep'].add(idx[id(b)])
# parts nothing lies under: if they touch a part that starts lower along their own stud axis, they follow it
for a in inst:
    if a['dep'] or a['id'] in WHEEL: continue
    amin,amax,k=ext(a,a['u'])
    for b in inst:
        if b is a or b['sub']!=a['sub'] or b['id'] in WHEEL or not touch(a,b): continue
        bmin,bmax,_=ext(b,a['u'])
        if (bmin+bmax)/2<(amin+amax)/2-0.05 and bmin<amin-0.03: a['dep'].add(idx[id(b)])
# hand corrections where the geometry alone cannot tell (part held by a clip, ball pushed up into a socket)
# key: (sub, part, stud axis or None) -> (part it follows, stud axis of that part or None, arrival direction or None)
SIDE=(0,0,-1)
AFTER={('Trailer','2736',None):('3491',None,[0,-1,0]), ('Trailer','4210a',None):('6019',None,[0,0,-1]), ('Trailer','2585',None):('2584',None,None),
       ('Truck Head','4590',None):('3034',None,None),
       ('Trailer','3022',SIDE):('3956',None,[0,0,1]), ('Trailer','3660',SIDE):('3022',SIDE,[0,0,1]), ('Trailer','6141',SIDE):('3660',SIDE,[0,0,1])}
for a in inst:
    r=AFTER.get((a['sub'],a['id'],tuple(a['u']))) or AFTER.get((a['sub'],a['id'],None))
    if r:
        a['dep']={idx[id(b)] for b in inst if b['sub']==a['sub'] and b['id']==r[0] and (r[1] is None or tuple(b['u'])==r[1])}
        if r[2]: a['from']=r[2]
        for b in inst: b['dep'].discard(idx[id(a)]) if b is not a else None
for sub in set(i['sub'] for i in inst):
    P=[i for i in inst if i['sub']==sub]
    cz=sum((p['lo'][2]+p['hi'][2])/2 for p in P)/len(P)
    for a in P:
        if a['id'] in WHEEL: a['from']=[0,0,1 if (a['lo'][2]+a['hi'][2])/2>cz else -1]
# layered picks, then merge neighbours into instruction-sized steps
steps=[]
MAXP,MAXK=7,4
for sub in ['Truck Head','Trailer']:
    P=[i for i in inst if i['sub']==sub]; done=set(); body=[p for p in P if p['id'] not in WHEEL]; seq=[]
    while len(done)<len(body):
        av=[p for p in body if idx[id(p)] not in done and all(d in done for d in p['dep'])]
        if not av: av=[p for p in body if idx[id(p)] not in done][:1]; print('CYCLE at',av[0]['id'])
        y0=min(p['lo'][1] for p in av)
        band=sorted([p for p in av if p['lo'][1]<=y0+0.3], key=lambda p:(p['name'],p['c'],p['lo'][0],p['lo'][2]))
        for p in band: done.add(idx[id(p)])
        seq.append(band)
    cur=[]
    def kinds(L): return len(set((p['name'],p['c']) for p in L))
    for band in seq:
        for p in band:
            if cur and (len(cur)+1>MAXP or kinds(cur+[p])>MAXK): steps.append((sub,cur)); cur=[]
            cur.append(p)
    if cur: steps.append((sub,cur))
    steps.append((sub+' wheels',sorted([p for p in P if p['id'] in WHEEL], key=lambda p:(p['id'],p['lo'][0],p['lo'][2]))))
AUTO=steps
# Step sequence of the set's printed instructions (10 truck steps, 15 trailer steps), as which parts go in which step.
# Selector: (part, {c: colour, y: height in the sub-model, below: True = pushed up from underneath in our upright view}).
B={'below':True}
OFFICIAL=[
 ('Truck Head','Truck: axle plates',[('4600',{})]),
 ('Truck Head','Truck: chassis plate',[('3034',{})]),
 ('Truck Head','Truck: front bumper and rear plates',[('2436a',{}),('3710',{'c':2}),('3024',{}),('2412a',{}),('3021',{}),('6141',{}),('3022',{'c':0}),('4590',{})]),
 ('Truck Head','Truck: red plate and coupling plate',[('3022',{'c':4}),('3709b',{})]),
 ('Truck Head','Truck: cab base and turntable',[('4211',{}),('4032b',{})]),
 ('Truck Head','Truck: cab floor',[('3020',{}),('3710',{'c':4})]),
 ('Truck Head','Truck: grille, doors and back wall',[('2877',{}),('3821',{}),('3822',{}),('3010',{})]),
 ('Truck Head','Truck: windscreen and roof',[('3823',{}),('4214',{}),('4213',{})]),
 ('Truck Head','Truck: roof panels and antenna',[('4865a',{}),('4592',{}),('4593',{})]),
 ('Truck Head','Truck: wheels',[('6014',{}),('6015',{})]),
 ('Trailer','Trailer: frame plate',[('3738',{})]),
 ('Trailer','Trailer: under-frame plates and tail lights',[('3023',{'c':0,**B}),('2436a',B),('3070b',{})]),
 ('Trailer','Trailer: white plates',[('3023',{'c':15,'y':-64}),('2412a',{}),('3022',{'c':15})]),
 ('Trailer','Trailer: front support and reel holder',[('4854',B),('3660',{'y':-80}),('6019',{}),('3024',{}),('3956',{}),('2584',{})]),
 ('Trailer','Trailer: deck plates',[('3034',{}),('3022',{'c':4})]),
 ('Trailer','Trailer: coupling plate, green layer and hose reel',[('3491',{}),('3460',{'c':2,'y':-80}),('3023',{'c':2}),('3660',{'y':-58}),('6141',{}),('2585',{}),('4210a',{})]),
 ('Trailer','Trailer: red and white plates',[('3666',{}),('3023',{'c':4,'y':-88}),('3710',{'c':2,'y':-88})]),
 ('Trailer','Trailer: corner bricks, panel and green plates',[('3005',{}),('4864b',{}),('3023',{'c':15,'y':-96}),('3460',{'c':2,'y':-96}),('3710',{'c':2,'y':-96})]),
 ('Trailer','Trailer: red layer and side bricks',[('3710',{'c':4}),('3023',{'c':4,'y':-104}),('3009',{})]),
 ('Trailer','Trailer: white plates',[('3460',{'c':15}),('2420',{})]),
 ('Trailer','Trailer: tank walls',[('2465',{}),('3004',{})]),
 ('Trailer','Trailer: tank slopes',[('4445',{})]),
 ('Trailer','Trailer: axles and coupling pin',[('2460',B),('4600',B),('2736',B)]),
 ('Trailer','Trailer: filler caps',[('4032a',{})]),
 ('Trailer','Trailer: wheels',[('6014',{}),('6015',{})]),
]
def official():
    taken=set(); out=[]
    for sub,title,sels in OFFICIAL:
        pick=[]
        for pid,q in sels:
            m=[p for p in inst if p['sub']==sub and p['id']==pid and idx[id(p)] not in taken and ('c' not in q or p['c']==q['c']) and ('y' not in q or p['lp'][1]==q['y'])]
            assert m,(title,pid,q)
            for p in m:
                taken.add(idx[id(p)])
                if q.get('below'): p['from']=[0,-1,0]; p['below']=True
            pick+=m
        # order inside the step: parts pushed up from below go first (highest first), the rest follow what they rest on
        below=sorted([p for p in pick if p.get('below')], key=lambda p:-p['lo'][1])
        rest=[p for p in pick if not p.get('below')]; ids={idx[id(p)] for p in rest}; done=set(); order=[]
        while rest:
            av=[p for p in rest if all(d in done or d not in ids for d in p['dep'])] or rest[:1]
            p=min(av, key=lambda p:(p['id'] in WHEEL and p['id']=='6015', round(p['lo'][1],2), p['name'], p['lo'][0], p['lo'][2]))
            order.append(p); done.add(idx[id(p)]); rest.remove(p)
        out.append((sub,below+order,title))
    left=[p['id'] for p in inst if idx[id(p)] not in taken]; assert not left, left
    return out
if '--auto' not in sys.argv: steps=official()
if __name__=='__main__':
    print('skipped' ,skipped); print('dets',set(round(i['det']*8000,2) for i in inst))
    for n,(sub,pk,*_t) in enumerate(steps):
        print(f'--- step {n+1} [{sub}]')
        for p in pk: print('   ',p['id'],p['name'],'c',p['c'],'y',round(p['lo'][1],2),'x',round(p['lo'][0],1),round(p['hi'][0],1),'from',p['from'],'deps',[inst[d]['id'] for d in p['dep']][:5])

def export(path):
    import collections
    SUBN={'Truck Head':'Truck','Trailer':'Trailer'}
    PL={'Plate':'plates','Brick':'bricks','Slope':'slopes','Tile':'tiles','Bracket':'brackets','Technic':'plates','Panel':'panels','Door':'doors','Windscreen':'windscreen','Hinge':'roof parts','Car':'cab base','Hose':'hose reel','Minifig':'hose nozzle','Tyre':'tyres','Wheel':'rims'}
    NAME={'Minifig Tool Hose Nozzle with Handle':'Hose Nozzle with Handle'}
    out={'parts':{}, 'steps':[], 'colors':{}}
    cfg=ld.fetch('LDConfig.ldr')
    for l in cfg.splitlines():
        m=re.match(r'0 !COLOUR (\S+)\s+CODE\s+(\d+)\s+VALUE\s+#([0-9A-Fa-f]{6})\s+EDGE\s+\S+(?:\s+ALPHA\s+(\d+))?',l)
        if m: out['colors'][int(m.group(2))]={'n':m.group(1).replace('_',' '),'hex':m.group(3),'a':int(m.group(4)) if m.group(4) else 255}
    used=set(); num={}
    for sub,pk,*_t in steps:
        if not pk: continue
        base=SUBN.get(sub.replace(' wheels',''),sub)
        if sub.endswith('wheels'): title=base+': wheels'
        else:
            cnt=collections.Counter(PL.get(p['name'].split()[0],'parts') for p in pk)
            w=[k for k,_ in cnt.most_common(2)]
            title=base+': '+' and '.join(w)
        if _t: title=_t[0]
        ps=[]
        for p in pk:
            used.add(p['file']); R,t=p['A']
            ps.append({'t':'ld','id':p['id'],'c':'L%d'%p['c'],'n':NAME.get(p['name'],p['name']),'m':[round(x,5) for x in R+t],'from':p['from']})
        num[base]=num.get(base,0)+1
        out['steps'].append({'title':title,'g':base,'k':num[base],'parts':ps})
    Q=50
    for f in sorted(used):
        g=geo[f]; T=[v for c in g['tris'] for v in g['tris'][c]]
        vid={}; vs=[]; ix=[]
        for i in range(0,len(T),3):
            k=(round(T[i]*Q),round(T[i+1]*Q),round(T[i+2]*Q))
            if k not in vid: vid[k]=len(vs)//3; vs+=k
            ix.append(vid[k])
        # drop triangles that collapsed after rounding
        ix2=[]
        for i in range(0,len(ix),3):
            a,b,c=ix[i:i+3]
            if a!=b and b!=c and a!=c: ix2+= [a,b,c]
        assert len(vs)//3<65536 and max(abs(v) for v in vs)<32768, f
        ls=[round(v*Q) for v in g['lines']]
        b64=lambda fmt,a: base64.b64encode(struct.pack('<%d%s'%(len(a),fmt),*a)).decode()
        out['parts'][f[:-4]]={'v':b64('h',vs),'i':b64('H',ix2),'l':b64('h',ls)}
    out['colors']={k:v for k,v in out['colors'].items() if any(p['c']=='L%d'%k for s_ in out['steps'] for p in s_['parts'])}
    out['q']=Q
    json.dump(out,open(path,'w'),separators=(',',':'))
    print('steps',len(out['steps']),'parts',sum(len(s_['parts']) for s_ in out['steps']),'unique',len(out['parts']),'bytes',os.path.getsize(path))
    for s_ in out['steps']: print(' ',s_['title'],len(s_['parts']))
    print(out['colors'])
import os
if __name__=='__main__' and [a for a in sys.argv[1:] if not a.startswith('--')]: export([a for a in sys.argv[1:] if not a.startswith('--')][0])
