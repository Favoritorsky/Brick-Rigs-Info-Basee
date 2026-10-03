from net import *
GREY=(90,90,95,255); PINK=(255,60,160,255)
OPS=['NOP','SET','ADD','SUB','SETX','SETY','ADDX','ADDY','VTOX','VTOY','GETX','GETY','DRAW','CLS','SETK','LOOP',
     'JMP','JZ','JNZ','RND','KEY','IFA','IFB','IFC','TEST','JV']
OP={n:i for i,n in enumerate(OPS)}
def asm(lines):
    out=[]
    for l in lines:
        t=l.split(';')[0].split()
        out.append(OP[t[0]]*1000+(int(t[1]) if len(t)>1 else 0))
    return out+[0]*(32-len(out))
PRESETS={
 2:('Звёзды',['CLS','SETK 0','RND 16','VTOX','RND 16','VTOY','DRAW 2','LOOP 2','JMP 1']),
 3:('Рисовалка',['CLS','SETX 8','SETY 8','DRAW 2','DRAW 2','IFA 16','IFB 18','IFC 0','KEY','JV 10',
                 'JMP 3','JMP 20','JMP 22','JMP 24','JMP 26','JMP 3','DRAW 1','JMP 8','DRAW 0','JMP 8',
                 'ADDX 15','JMP 3','ADDX 1','JMP 3','ADDY 1','JMP 3','ADDY 15','JMP 3']),
 4:('Счётчик кнопок',['SET 0','IFA 5','IFB 7','IFC 0','JMP 1','ADD 1','JMP 1','SUB 1','JMP 1']),
 5:('Мячик',['CLS','SETY 8','SETX 0','DRAW 1','DRAW 0','ADDX 1','GETX','SUB 15','JNZ 3',
             'DRAW 1','DRAW 0','ADDX 15','GETX','JNZ 9','JMP 3']),
}
CUSTOM_DEFAULT=asm(['SET 0','ADD 1','JMP 1'])
def build_cpu3(custom=CUSTOM_DEFAULT,presets=PRESETS,speed=3.0):
    N=Net(); S={}
    def M(*a,**k): return N.math(*a,color=k.pop('color',GREY),size=k.pop('size',(10,10,10)),**k)
    C256=M('Add',256.0,0.0); C16=M('Add',16.0,0.0); C31=M('Add',31.0,0.0)
    # --- выбор пресета ---
    names={1:'Своя программа'}; names.update({p:v[0] for p,v in presets.items()}); names[99]='СТОП'
    PSW={p:N.switch(f'{p if p!=99 else 0}. {nm}' if p!=99 else 'СТОП',float(p),color=(60,200,90,255) if p!=99 else (200,40,40,255),size=(20,20,10)) for p,nm in names.items()}
    SUMB=M('Add',list(PSW.values()),0.0)
    BTNP=N.time([SUMB],0.001,0.001,1.0,0.0,rtz=True,color=PINK,size=(10,10,10))
    MODE=M('Add',[],0.0)
    N.set_src(MODE,'InputChannelA',[MODE,M('Multiply',[M('Subtract',[SUMB],[MODE])],[BTNP])])
    RUN=M('Multiply',[M('Greater',[MODE],0.5)],[M('Less',[MODE],50.0)])
    RSTN=M('Multiply',[BTNP],-1.0)
    NOTP=M('Less',[SUMB],0.5)
    TT=N.time([M('Multiply',[RUN],[NOTP])],rtz=True,color=PINK,size=(10,10,10))
    TS=M('Multiply',[TT],speed,color=PINK); S['speed']=TS
    PH=M('Fmod',[M('Add',[TS],0.97)],1.0)
    LO=M('Less',[PH],0.6)
    HI=M('Multiply',[M('GreaterEqual',[PH],0.7)],[M('Less',[PH],0.95)])
    PEX=N.time([HI],0.001,0.001,1.0,0.0,rtz=True,color=PINK,size=(10,10,10))
    PINC=N.time([LO],0.001,0.001,1.0,0.0,rtz=True,color=PINK,size=(10,10,10))
    CNT=M('Add',[],0.0); PC=M('Fmod',[M('Add',[CNT],31.0)],32.0)
    # --- память программы ---
    MEQ={p:M('Equal',[MODE],float(p)) for p in names if p!=99}
    SEL=[];LINEBR=[];lop=[];ln=[]
    for r in range(32):
        s=M('Equal',[PC],float(r),color=(255,220,40,255)); SEL.append(s)
        kc=[M('Multiply',[MEQ[1]],float(custom[r]),color=(40,90,220,255),size=(20,20,20))]; LINEBR.append(kc[0])
        for p,(nm,prog) in presets.items():
            code=asm(prog)[r]
            if code: kc.append(M('Multiply',[MEQ[p]],float(code)))
        ks=M('Add',kc,0.0)
        opr=M('Floor',[M('Divide',[ks],1000.0)]); nr=M('Fmod',[M('Fmod',[ks],1000.0)],256.0)
        lop.append(M('Multiply',[s],[opr])); ln.append(M('Multiply',[s],[nr]))
    OPV=M('Add',lop,0.0); Nn=M('Add',ln,0.0)
    IS={k:M('Equal',[OPV],float(k)) for k in range(1,len(OPS))}
    VR=M('Add',[],0.0); V=M('Fmod',[VR],256.0); XR=M('Add',[],0.0); X=M('Fmod',[XR],16.0)
    YR=M('Add',[],0.0); Y=M('Fmod',[YR],16.0); KR=M('Add',[],0.0); K=M('Fmod',[KR],256.0)
    def term(op,srcs): return M('Multiply',[IS[OP[op]]],srcs)
    # ввод
    ST=M('Add','Steering',0.0); TH=M('Add','Throttle',0.0)
    KEYC=M('Add',[M('Less',[ST],-0.3),M('Multiply',[M('Greater',[ST],0.3)],2.0),M('Multiply',[M('Greater',[TH],0.3)],3.0),
          M('Multiply',[M('Less',[TH],-0.3)],4.0),M('Multiply',[M('Greater',[M('Add','Action1','HandBrake')],0.3)],5.0)],0.0)
    BA=N.switch('Кнопка A',color=(230,60,60,255),size=(30,30,10)); BB=N.switch('Кнопка B',color=(60,200,90,255),size=(30,30,10)); BC=N.switch('Кнопка C',color=(60,120,240,255),size=(30,30,10))
    RAND=M('Floor',[M('Multiply',[M('Abs',[M('Sin',[M('Multiply',[N.time(color=PINK,size=(10,10,10))],12.9898)])])],43758.5453)])
    DIV=M('Add',[Nn,M('Multiply',[M('Equal',[Nn],0.0)],256.0)],0.0)
    RV=M('Fmod',[RAND],[DIV])
    dV=[term('SET',[M('Subtract',[Nn],[V]),C256]),term('ADD',[Nn]),term('SUB',[M('Subtract',256.0,[Nn])]),
        term('GETX',[M('Subtract',[X],[V]),C256]),term('GETY',[M('Subtract',[Y],[V]),C256]),
        term('RND',[M('Subtract',[RV],[V]),C256]),term('KEY',[M('Subtract',[KEYC],[V]),C256])]
    dX=[term('SETX',[M('Subtract',[Nn],[X]),C16]),term('ADDX',[Nn]),term('VTOX',[M('Subtract',[V],[X]),C16])]
    dY=[term('SETY',[M('Subtract',[Nn],[Y]),C16]),term('ADDY',[Nn]),term('VTOY',[M('Subtract',[V],[Y]),C16])]
    dK=[term('SETK',[M('Subtract',[Nn],[K]),C256]),term('LOOP',255.0)]
    for R,ds in ((VR,dV),(XR,dX),(YR,dY),(KR,dK)):
        N.set_src(R,'InputChannelA',[R,M('Multiply',ds,[PEX]),M('Multiply',[R],[RSTN])])
    # экран + чтение пикселя
    PLTP=M('Multiply',[IS[OP['DRAW']]],[PEX])
    DRAW=M('Equal',[Nn],1.0); TOG=M('GreaterEqual',[Nn],2.0)
    K1=M('Add',[DRAW,TOG],0.0); K2=M('Subtract',-1.0,[TOG])
    CLSN=M('Add',[M('Multiply',[M('Multiply',[IS[OP['CLS']]],[PEX])],-1.0),RSTN],0.0)
    colX=[M('Equal',[X],float(c)) for c in range(16)]; rowY=[M('Equal',[Y],float(r)) for r in range(16)]
    PIX={}; pvs=[]
    for r in range(16):
        for c in range(16):
            P=M('Add',[],0.0); sr=M('Multiply',[colX[c]],[rowY[r]])
            d=M('Multiply',[M('Multiply',[sr],[PLTP])],[M('Add',[M('Multiply',[P],[K2])],[K1])])
            N.set_src(P,'InputChannelA',[P,d,M('Multiply',[P],[CLSN])]); PIX[(c,r)]=P
            pvs.append(M('Multiply',[sr],[P]))
    PIXV=M('Add',pvs,0.0)
    # переходы
    VZ=M('Equal',[V],0.0)
    JC=M('Add',[IS[OP['JMP']],M('Multiply',[IS[OP['LOOP']]],[M('Subtract',1.0,[M('Equal',[K],1.0)])]),
              M('Multiply',[IS[OP['JZ']]],[VZ]),M('Multiply',[IS[OP['JNZ']]],[M('Subtract',1.0,[VZ])]),
              M('Multiply',[IS[OP['IFA']]],[M('Greater',[BA],0.5)]),M('Multiply',[IS[OP['IFB']]],[M('Greater',[BB],0.5)]),
              M('Multiply',[IS[OP['IFC']]],[M('Greater',[BC],0.5)]),M('Multiply',[IS[OP['TEST']]],[M('Greater',[PIXV],0.5)])],0.0)
    OFF=M('Add',[M('Subtract',[Nn],[PC]),C31],0.0)
    JD=M('Multiply',[M('Multiply',[JC],[OFF]),M('Multiply',[IS[OP['JV']]],[OFF,V])],[PEX])
    N.set_src(CNT,'InputChannelA',[CNT,PINC,M('Multiply',[CNT],[RSTN])]); N.set_src(CNT,'InputChannelB',[JD])
    ROWLED=[M('Multiply',[SEL[r]],[LO]) for r in range(32)]
    S.update(PC=PC,V=V,X=X,Y=Y,K=K,MODE=MODE,SEL=SEL,LINEBR=LINEBR,ROWLED=ROWLED,PIX=PIX,PSW=PSW,BTN=(BA,BB,BC),M=M,OPV=OPV,N=Nn,names=names)
    return N,S
