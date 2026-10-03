import struct, itertools, math
from collections import defaultdict
def rot_extents(size,rot):
    sx,sy,sz=size; p,y,r=[round(a)%360 for a in rot]
    # поддерживаем повороты, кратные 90: roll(X) -> pitch(Y) -> yaw(Z)
    v=[sx,sy,sz]
    if r in(90,270): v=[v[0],v[2],v[1]]
    if p in(90,270): v=[v[2],v[1],v[0]]
    if y in(90,270): v=[v[1],v[0],v[2]]
    return v
def box_of(b):
    if 'BrickSize' not in b['props']: return None
    s=struct.unpack('<3f',b['props']['BrickSize'])
    e=rot_extents(s,b.get('rot',(0,0,0)))
    return tuple((b['pos'][i]-e[i]/2,b['pos'][i]+e[i]/2) for i in range(3))
def snap(N,skip=()):
    for i,b in enumerate(N.b):
        if i in skip: continue
        bx=box_of(b)
        if not bx: continue
        p=list(b['pos'])
        for a in range(3):
            lo=bx[a][0]; d=round(lo/10)*10-lo
            if abs(d)>1e-6: p[a]+=d
        b['pos']=tuple(p)
def pts(a0,a1):
    n=max(1,round((a1-a0)/10)); st=(a1-a0)/n
    return [round(a0+st*(k+0.5),3) for k in range(n)]
def connected(A,B):
    for ax in range(3):
        for fa,fb in ((A[ax][1],B[ax][0]),(A[ax][0],B[ax][1])):
            if abs(fa-fb)<1e-3:
                ok=True
                for i in [i for i in range(3) if i!=ax]:
                    lo,hi=max(A[i][0],B[i][0]),min(A[i][1],B[i][1])
                    if hi-lo<=1e-3: ok=False;break
                    pa={p for p in pts(*A[i]) if lo<p<hi}; pb={p for p in pts(*B[i]) if lo<p<hi}
                    if not pa&pb: ok=False;break
                if ok: return True
    return False
def overlap(A,B): return all(min(A[i][1],B[i][1])-max(A[i][0],B[i][0])>1e-3 for i in range(3))
def analyze(N,ignore=()):
    boxes={i:box_of(b) for i,b in enumerate(N.b)}
    boxes={i:x for i,x in boxes.items() if x and i not in ignore}
    # пространственная хеш-сетка
    cell=100; grid=defaultdict(list)
    for i,bx in boxes.items():
        for gx in range(int(bx[0][0]//cell),int(bx[0][1]//cell)+1):
            for gy in range(int(bx[1][0]//cell),int(bx[1][1]//cell)+1):
                for gz in range(int(bx[2][0]//cell),int(bx[2][1]//cell)+1):
                    grid[(gx,gy,gz)].append(i)
    par={i:i for i in boxes}
    def f(i):
        while par[i]!=i: par[i]=par[par[i]]; i=par[i]
        return i
    ov=[]; seen=set()
    for lst in grid.values():
        for a,b in itertools.combinations(lst,2):
            if (a,b) in seen: continue
            seen.add((a,b))
            A,B=boxes[a],boxes[b]
            if overlap(A,B): ov.append((a,b))
            elif connected(A,B): par[f(a)]=f(b)
    comps=defaultdict(list)
    for i in boxes: comps[f(i)].append(i)
    return sorted(comps.values(),key=len,reverse=True),ov
