import struct,sys
from collections import Counter
def s8(b): return b[1:1+b[0]].decode('latin1')
def s16(b):
    n=struct.unpack_from('<h',b,0)[0]
    return b[2:2+n].decode('latin1') if n>=0 else b[2:2-2*n].decode('utf-16-le')
def load(path):
    d=open(path,'rb').read()
    v=d[0]; nb,nc,npr=struct.unpack_from('<HHH',d,1); p=7
    cls=[]
    for i in range(nc):
        l=d[p]; cls.append(d[p+1:p+1+l].decode()); p+=1+l
    props=[]
    for i in range(npr):
        l=d[p]; name=d[p+1:p+1+l].decode(); p+=1+l
        cnt,size=struct.unpack_from('<HI',d,p); p+=6
        data=d[p:p+size]; p+=size
        if cnt>1: es=struct.unpack_from('<H',d,p)[0]; p+=2
        else: es=size
        if cnt==1: vals=[data]
        elif es>0: vals=[data[i*es:(i+1)*es] for i in range(cnt)]
        else:
            sizes=struct.unpack_from(f'<{cnt}H',d,p); p+=2*cnt; q=0; vals=[]
            for s in sizes: vals.append(data[q:q+s]); q+=s
        props.append((name,vals))
    bricks=[]
    for bi in range(nb):
        c,size=struct.unpack_from('<HI',d,p); p+=6
        b=d[p:p+size]; p+=size
        n=b[0]; q=1; pr={}
        for k in range(n):
            pi,vi=struct.unpack_from('<HH',b,q); q+=4
            pr[props[pi][0]]=props[pi][1][vi]
        f=struct.unpack_from('<6f',b,q); q+=24
        ed,we=struct.unpack_from('<HH',b,q) if len(b)>=q+4 else (0,0)
        bricks.append(dict(cls=cls[c],pr=pr,pos=f[:3],rot=f[3:],editor=ed,weld=we))
    assert p==len(d)
    return v,cls,props,bricks
if __name__=='__main__':
    path=sys.argv[1]
    v,cls,props,bricks=load(path)
    print('=== ',path,'ver',v,'блоков',len(bricks),'типов',len(cls),'свойств',len(props))
    for k,n in Counter(b['cls'] for b in bricks).most_common(): print(f'{n:5} {k}')
    xs,ys,zs=zip(*[b['pos'] for b in bricks])
    print('габариты см: X',round(max(xs)-min(xs)),'Y',round(max(ys)-min(ys)),'Z',round(max(zs)-min(zs)))
    print('без поворота',sum(1 for b in bricks if all(abs(r)<0.01 for r in b['rot'])))
    print('углы не кратные 90:',sum(1 for b in bricks if any(abs(r)%90>0.5 and abs(r)%90<89.5 for r in b['rot'])))
    print('сварка:',Counter(b['weld'] for b in bricks).most_common(8))
    print('группы редактора:',Counter(b['editor'] for b in bricks).most_common(8))
    P=dict(props)
    print('свойства:',[p[0] for p in props])
    for k in P:
        if k.endswith('InputAxis') or k in('SensorType','Operation','BrickMaterial','ActuatorMode','BrickPattern','Font','Image','AmmoType','FuelType','CouplingMode','SpinnerShape','FlashSequence','SirenType','ExhaustEffect','LightDirection'):
            try: print(' ',k,[s8(x) for x in P[k]])
            except: pass
    for k in ('Text','SeatName','SwitchName','CameraName'):
        if k in P: print(' ',k,[s16(x) for x in P[k]])
    th=[b for b in bricks if 'BrickSize' in b['pr'] and min(struct.unpack('<3f',b['pr']['BrickSize']))<5]
    print('тонких (<5см):',len(th))
