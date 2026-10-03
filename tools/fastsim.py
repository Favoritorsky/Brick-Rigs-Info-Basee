# Векторная симуляция синхронной модели (каждый блок — задержка 1 кадр)
import numpy as np, scipy.sparse as sp, math
OPC=['Add','Subtract','Multiply','Divide','Fmod','Floor','Equal','Greater','Less','GreaterEqual','LessEqual','Min','Max','Sin','Abs','Round']
class Fast:
    def __init__(s,net):
        n=len(net.b); s.n=n
        rows={k:[] for k in ('A','B','L','E')}; 
        s.op=np.full(n,-1); s.cA=np.zeros(n); s.cB=np.zeros(n); s.axA={}; s.axB={}
        s.kind=np.zeros(n,int)   # 0 none,1 math,2 time,3 light,4 switch
        s.tparams=np.zeros((n,4)); s.always=np.zeros(n,bool); s.sw={}
        def add(key,i,ins):
            if ins[0]=='s':
                for j in ins[1]: rows[key].append((i,j))
            return ins
        for i,b in enumerate(net.b):
            sm=b['sim']
            if sm is None: continue
            if sm[0]=='math':
                s.kind[i]=1; s.op[i]=OPC.index(sm[1])
                for key,ins,c,ax in (('A',sm[2][0],s.cA,s.axA),('B',sm[2][1],s.cB,s.axB)):
                    if ins[0]=='c': c[i]=ins[1]
                    elif ins[0]=='a': ax[i]=ins[1]
                    else: add(key,i,ins)
            elif sm[0]=='time':
                s.kind[i]=2; s.tparams[i]=sm[2]
                if sm[1] is None: s.always[i]=True
                else: add('E',i,('s',sm[1]))
            elif sm[0]=='light':
                s.kind[i]=3; add('L',i,('s',sm[1]))
            elif sm[0]=='switch':
                s.kind[i]=4; s.sw[i]=(sm[1],sm[2])
        def mat(key):
            if not rows[key]: return sp.csr_matrix((n,n))
            r,c=zip(*rows[key]); return sp.csr_matrix((np.ones(len(r)),(r,c)),shape=(n,n))
        s.MA=mat('A'); s.MB=mat('B'); s.ML=mat('L'); s.ME=mat('E')
        s.mathidx=np.where(s.kind==1)[0]; s.timeidx=np.where(s.kind==2)[0]; s.lightidx=np.where(s.kind==3)[0]
    def run(s,seconds,fps=60,inputs=None,hook=None):
        n=s.n; out=np.zeros(n); timers=np.full(n,-1.0); dt=1/fps
        for fr in range(int(seconds*fps)):
            t=fr*dt; cur=inputs(t,out) if inputs else {}
            A=s.MA@out+s.cA; B=s.MB@out+s.cB
            for i,a in s.axA.items(): A[i]=cur.get(a,0.0)
            for i,a in s.axB.items(): B[i]=cur.get(a,0.0)
            new=np.zeros(n)
            o=s.op; m=s.mathidx; a=A[m]; b=B[m]; oo=o[m]; r=np.zeros(len(m))
            with np.errstate(all='ignore'):
                r=np.select([oo==0,oo==1,oo==2,oo==3,oo==4,oo==5,oo==6,oo==7,oo==8,oo==9,oo==10,oo==11,oo==12,oo==13,oo==14,oo==15],
                 [a+b,a-b,a*b,np.where(b!=0,a/np.where(b!=0,b,1),0),np.where(b!=0,np.fmod(a,np.where(b!=0,b,1)),0),np.floor(a),
                  (a==b)*1.0,(a>b)*1.0,(a<b)*1.0,(a>=b)*1.0,(a<=b)*1.0,np.minimum(a,b),np.maximum(a,b),np.sin(a),np.abs(a),np.round(a)])
            new[m]=r
            en=s.ME@out
            ti=s.timeidx
            on=s.always[ti]|(en[ti]>0)
            timers[ti]=np.where(on,np.where(timers[ti]<0,0.0,timers[ti]+dt),-1.0)
            p=s.tparams[ti]; x=timers[ti]
            eqmask=p[:,0]==p[:,1]
            span=np.where(eqmask,1,p[:,1]-p[:,0])
            tt=np.clip((x-p[:,0])/span,0,1)
            val=np.where(eqmask,np.where(x<=p[:,0],p[:,2],p[:,3]),p[:,2]+(p[:,3]-p[:,2])*tt)
            new[ti]=np.where(on,val,0.0)
            new[s.lightidx]=(s.ML@out)[s.lightidx]
            for i,(nm,mx) in s.sw.items(): new[i]=mx*cur.get('sw:'+nm,0.0)
            out=new
            if hook: hook(t,out)
        return out
