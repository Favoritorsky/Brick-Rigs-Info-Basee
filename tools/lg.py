import struct
from collections import Counter,defaultdict,deque
from analyze import load,s8,s16
KEYS=('InputChannel.SourceBricks','InputChannelA.SourceBricks','InputChannelB.SourceBricks','EnabledInputChannel.SourceBricks','SteeringInputChannel.SourceBricks','BrakeInputChannel.SourceBricks','ThrottleInputChannel.SourceBricks','PowerInputChannel.SourceBricks','PitchInputChannel.SourceBricks','YawInputChannel.SourceBricks','RollInputChannel.SourceBricks')
class G:
    def __init__(s,path):
        s.v,s.cls,s.props,s.B=load(path); B=s.B
        s.ins=[[ (j,k) for k in KEYS for j in s.src(b,k)] for b in B]
        s.outs=defaultdict(list)
        for i,l in enumerate(s.ins):
            for j,k in l: s.outs[j].append(i)
    def src(s,b,k):
        v=b['pr'].get(k)
        if not v: return []
        n=struct.unpack_from('<H',v,0)[0]; return [j-1 for j in struct.unpack_from(f'<{n}H',v,2)]
    def f(s,b,k):
        v=b['pr'].get(k); return round(struct.unpack('<f',v)[0],3) if v and len(v)==4 else None
    def name(s,i):
        b=s.B[i]; pr=b['pr']; n=b['cls'].replace('Brick','')
        if 'Operation' in pr: n+=':'+s8(pr['Operation'])
        elif b['cls']=='MathBrick': n+=':Add'
        if 'SensorType' in pr: n+=':'+s8(pr['SensorType'])
        if 'SwitchName' in pr: n+='"'+s16(pr['SwitchName'])+'"'
        for k in ('InputChannel.InputAxis','InputChannelA.InputAxis','InputChannelB.InputAxis','EnabledInputChannel.InputAxis'):
            if k in pr and s8(pr[k]) not in ('Custom',): n+=f'[{k.split(".")[0][:6]}={s8(pr[k])}]'
        ex=[]
        for k in ('InputChannelA.Value','InputChannelB.Value','OutputChannel.MinIn','OutputChannel.MaxIn','OutputChannel.MinOut','OutputChannel.MaxOut','MinLimit','MaxLimit','SpeedFactor'):
            v=s.f(b,k)
            if v is not None: ex.append(f'{k.split(".")[-1]}={v}')
        if ex: n+='{'+','.join(ex)+'}'
        return f'#{i} '+n
    def tree(s,i,d=0,maxd=5,seen=None):
        seen=set() if seen is None else seen
        print('  '*d+s.name(i)+(' (уже)' if i in seen else ''))
        if i in seen or d>=maxd: return
        seen.add(i)
        for j,k in s.ins[i]: s.tree(j,d+1,maxd,seen)
