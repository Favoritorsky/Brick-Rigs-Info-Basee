import struct, math
def s8(s): b=s.encode(); return bytes([len(b)])+b
def f32(v): return struct.pack('<f',v)
def srcb(lst): return struct.pack('<H',len(lst))+b''.join(struct.pack('<H',i+1) for i in lst)
def txt(s): b=s.encode('latin1'); return struct.pack('<h',len(b))+b
class Net:
    def __init__(s): s.b=[]   # dict(cls,props,pos,sim)
    def add(s,cls,props,pos=(0,0,0),sim=None,color=None,size=None):
        p=dict(props)
        if color: p['BrickColor']=bytes(color)
        if size: p['BrickSize']=b''.join(f32(v) for v in size)
        s.b.append(dict(cls=cls,props=p,pos=pos,sim=sim)); return len(s.b)-1
    def _ch(s,p,name,v,sim_in):
        if isinstance(v,str):
            p[name+'.InputAxis']=s8(v); sim_in.append(('a',v)); return
        if isinstance(v,(int,float)):
            p[name+'.InputAxis']=s8('AlwaysOn'); p[name+'.Value']=f32(float(v)); sim_in.append(('c',float(v)))
        else:
            p[name+'.InputAxis']=s8('Custom'); p[name+'.SourceBricks']=srcb(v); sim_in.append(('s',list(v)))
    def math(s,op,A,B=0.0,**kw):
        p={'Operation':s8(op)}; ins=[]
        s._ch(p,'InputChannelA',A,ins); s._ch(p,'InputChannelB',B,ins)
        return s.add('MathBrick',p,sim=('math',op,ins),**kw)
    def set_src(s,i,chan,lst):   # для обратных связей
        b=s.b[i]; b['props'][chan+'.InputAxis']=s8('Custom'); b['props'][chan+'.SourceBricks']=srcb(lst)
        k=0 if chan=='InputChannelA' else 1; b['sim'][2][k]=('s',list(lst))
    def time(s,enable=None,minin=0,maxin=1e6,minout=0,maxout=1e6,rtz=False,**kw):
        p={'SensorType':s8('Time'),'OutputChannel.MinIn':f32(minin),'OutputChannel.MaxIn':f32(maxin),
           'OutputChannel.MinOut':f32(minout),'OutputChannel.MaxOut':f32(maxout)}
        if rtz: p['bReturnToZero']=b'\x01'
        if enable is None: p['EnabledInputChannel.InputAxis']=s8('AlwaysOn'); p['EnabledInputChannel.Value']=f32(1.0)
        else: p['EnabledInputChannel.InputAxis']=s8('Custom'); p['EnabledInputChannel.SourceBricks']=srcb(enable)
        return s.add('SensorBrick',p,sim=('time',enable,(minin,maxin,minout,maxout)),**kw)
    def light(s,srcs,bright=0.6,**kw):
        p={'InputChannel.InputAxis':s8('Custom'),'InputChannel.SourceBricks':srcb(srcs),'Brightness':f32(bright)}
        return s.add('LightBrick',p,sim=('light',srcs),**kw)
    def switch(s,name,maxout=1.0,momentary=True,**kw):
        b=name.encode('utf-16-le'); nm=struct.pack('<h',-(len(b)//2))+b
        p={'SwitchName':nm,'OutputChannel.MinIn':f32(0.0),'OutputChannel.MaxIn':f32(1.0),'OutputChannel.MinOut':f32(0.0),
           'OutputChannel.MaxOut':f32(maxout),'bReturnToZero':b'\x01' if momentary else b'\x00'}
        return s.add('SwitchBrick',p,sim=('switch',name,maxout),**kw)
    def display(s,srcs,color,**kw):
        p={'InputChannel.InputAxis':s8('Custom'),'InputChannel.SourceBricks':srcb(srcs),'NumFractionalDigits':b'\x00','DisplayColor':bytes(color)}
        return s.add('DisplayBrick',p,sim=('light',srcs),**kw)
    def utext(s,t,size=(10,10,10),**kw):
        b=t.encode('utf-16-le'); return s.add('TextBrick',{'Text':struct.pack('<h',-(len(b)//2))+b},size=size,**kw)
    def text(s,t,size=(20,20,10),fs=10.0,**kw):
        return s.add('TextBrick',{'Text':txt(t),'FontSize':f32(fs)},size=size,**kw)
    def block(s,size,**kw):
        return s.add('ScalableBrick',{},size=size,**kw)

def remap(x,a,b,c,d):
    if a==b: return c if x<=a else d
    t=(x-a)/(b-a); t=max(0,min(1,t)); return c+(d-c)*t
OPS={'Add':lambda a,b:a+b,'Subtract':lambda a,b:a-b,'Multiply':lambda a,b:a*b,
     'Divide':lambda a,b:a/b if b else 0,'Fmod':lambda a,b:math.fmod(a,b) if b else 0,
     'Floor':lambda a,b:math.floor(a),'Equal':lambda a,b:float(a==b),'Greater':lambda a,b:float(a>b),
     'Less':lambda a,b:float(a<b),'Min':min,'Sin':lambda a,b:math.sin(a),'Abs':lambda a,b:abs(a),'Max':max,'Round':lambda a,b:float(round(a)),'GreaterEqual':lambda a,b:float(a>=b),'LessEqual':lambda a,b:float(a<=b)}
def simulate(net,seconds,fps=60,mode='sync',probe=None,every=None,inputs=None,hook=None):
    n=len(net.b); out=[0.0]*n; timers={}
    dt=1/fps; log=[]
    order=range(n-1,-1,-1) if mode=='rseq' else range(n)
    cur={}
    def val(o,ins):
        if ins[0]=='a': return cur.get(ins[1],0.0)
        return ins[1] if ins[0]=='c' else sum(o[j] for j in ins[1])
    for fr in range(int(seconds*fps)):
        global_cur=None
        if inputs: cur=inputs(fr*dt,out)
        src=out if mode in('seq','rseq') else list(out)
        new=out if mode in('seq','rseq') else [0.0]*n
        for i in order:
            sm=net.b[i]['sim']
            if sm is None: continue
            if sm[0]=='math':
                a=val(src,sm[2][0]); b=val(src,sm[2][1]); new[i]=OPS[sm[1]](a,b)
            elif sm[0]=='time':
                en=1 if sm[1] is None else sum(src[j] for j in sm[1])
                if en>0:
                    t=timers.get(i,-dt)+dt; timers[i]=t; new[i]=remap(t,*sm[2])
                else: timers.pop(i,None); new[i]=0.0
            elif sm[0]=='switch':
                new[i]=sm[2]*cur.get('sw:'+sm[1],0.0)
            elif sm[0]=='light':
                new[i]=sum(src[j] for j in sm[1])
        out=new
        if hook: hook(fr*dt,out)
        if probe and every and fr%every==0: log.append((fr*dt,[out[j] for j in probe]))
    return out,log

def write_brv(path,bricks,weld=1):
    classes=[]; props={}
    for b in bricks:
        if b['cls'] not in classes: classes.append(b['cls'])
        for k,v in b['props'].items():
            L=props.setdefault(k,{})
            if v not in L: L[v]=len(L)
    pn=list(props); pi={k:i for i,k in enumerate(pn)}
    out=bytearray([18])+struct.pack('<HHH',len(bricks),len(classes),len(pn))
    for c in classes: out+=s8(c)
    for k in pn:
        L=list(props[k]); data=b''.join(L); out+=s8(k)+struct.pack('<HI',len(L),len(data))+data
        if len(L)>1:
            if len(set(map(len,L)))==1: out+=struct.pack('<H',len(L[0]))
            else: out+=struct.pack('<H',0)+struct.pack(f'<{len(L)}H',*map(len,L))
    ci={c:i for i,c in enumerate(classes)}
    for b in bricks:
        body=bytearray([len(b['props'])])
        for k,v in b['props'].items(): body+=struct.pack('<HH',pi[k],props[k][v])
        body+=struct.pack('<6f',*b['pos'],*b.get('rot',(0,0,0)))+struct.pack('<HH',0,weld)
        out+=struct.pack('<HI',ci[b['cls']],len(body))+body
    open(path,'wb').write(out); return len(out)
FONT={0:["###","#.#","#.#","#.#","###"],1:[".#.","##.",".#.",".#.","###"],2:["###","..#","###","#..","###"],
      3:["###","..#","###","..#","###"],4:["#.#","#.#","###","..#","..#"],5:["###","#..","###","..#","###"],
      6:["###","#..","###","#.#","###"],7:["###","..#",".#.",".#.",".#."],8:["###","#.#","###","#.#","###"],
      9:["###","#.#","###","..#","###"]}
