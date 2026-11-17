"""sta.py: tiny NLDM static timing for a mapped gate-level Verilog netlist (worst-case, no wires).
usage: python3 sta.py lib.lib netlist.v [input_slew_ns] [out_load_fF]"""
import re,sys,bisect
def tokenize(s):
    return re.findall(r'"[^"]*"|[A-Za-z_][\w\.\[\]\$]*|[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?|[{}();:,\\]',s)
def parse(path):
    s=open(path).read()
    s=re.sub(r'/\*.*?\*/','',s,flags=re.S); s=re.sub(r'//[^\n]*','',s); s=s.replace('\\\n',' ')
    t=tokenize(s); i=0
    def group():
        nonlocal i
        # at: name ( args ) {  OR  name : value ;  OR name ( args ) ;
        name=t[i]; i+=1
        if t[i]==':':
            i+=1; v=[]
            while t[i]!=';': v.append(t[i]); i+=1
            i+=1; return ('attr',name,' '.join(v))
        assert t[i]=='(',(name,t[i])
        i+=1; args=[]
        while t[i]!=')':
            if t[i]!=',': args.append(t[i].strip('"'))
            i+=1
        i+=1
        if t[i]=='{':
            i+=1; kids=[]
            while t[i]!='}': kids.append(group())
            i+=1; return ('group',name,args,kids)
        if t[i]==';': i+=1
        return ('cattr',name,args)
    top=group(); return top
def floats(a): return [float(x) for x in re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?',' '.join(a))]
def load(path):
    top=parse(path); tmpl={}; cells={}
    for k in top[3]:
        if k[0]=='group' and k[1]=='lu_table_template':
            d={}
            for a in k[3]:
                if a[0]=='cattr': d[a[1]]=floats(a[2])
            tmpl[k[2][0]]=d
    for k in top[3]:
        if not(k[0]=='group' and k[1]=='cell'): continue
        c=dict(area=0,pins={},arcs=[]); 
        for a in k[3]:
            if a[0]=='attr' and a[1]=='area': c['area']=float(a[2])
            if a[0]=='group' and a[1]=='pin':
                pn=a[2][0]; p=dict(dir=None,cap=0.0)
                for b in a[3]:
                    if b[0]=='attr' and b[1]=='direction': p['dir']=b[2]
                    if b[0]=='attr' and b[1]=='capacitance': p['cap']=float(b[2])
                c['pins'][pn]=p
                for b in a[3]:
                    if b[0]=='group' and b[1]=='timing':
                        arc=dict(out=pn,rel=None,sense='non_unate',tabs={})
                        for e in b[3]:
                            if e[0]=='attr' and e[1]=='related_pin': arc['rel']=e[2].strip('"')
                            if e[0]=='attr' and e[1]=='timing_sense': arc['sense']=e[2]
                            if e[0]=='group' and e[1] in('cell_rise','cell_fall','rise_transition','fall_transition'):
                                d=dict(i1=None,i2=None,v=None)
                                for f in e[3]:
                                    if f[0]=='cattr':
                                        if f[1]=='index_1': d['i1']=floats(f[2])
                                        if f[1]=='index_2': d['i2']=floats(f[2])
                                        if f[1]=='values': d['v']=floats(f[2])
                                tm=tmpl.get(e[2][0],{})
                                if d['i1'] is None: d['i1']=tm.get('index_1')
                                if d['i2'] is None: d['i2']=tm.get('index_2')
                                if d['i2'] is None or d['i1'] is None: continue
                                n2=len(d['i2']); d['v']=[d['v'][r*n2:(r+1)*n2] for r in range(len(d['i1']))]
                                arc['tabs'][e[1]]=d
                        if arc['rel'] and 'cell_rise' in arc['tabs']: c['arcs'].append(arc)
        cells[k[2][0]]=c
    return cells
def interp(tab,x,y):
    i1,i2,v=tab['i1'],tab['i2'],tab['v']
    def seg(a,x):
        j=bisect.bisect_right(a,x)-1; j=max(0,min(j,len(a)-2)); return j,(x-a[j])/(a[j+1]-a[j])
    j,fx=seg(i1,x); k,fy=seg(i2,y)
    a=v[j][k]*(1-fy)+v[j][k+1]*fy; b=v[j+1][k]*(1-fy)+v[j+1][k+1]*fy
    return a*(1-fx)+b*fx
def netlist(path):
    s=open(path).read(); s=re.sub(r'/\*.*?\*/','',s,flags=re.S); s=re.sub(r'//[^\n]*','',s)
    ports={'input':[],'output':[]}
    for m in re.finditer(r'\b(input|output)\s*(\[(\d+):(\d+)\])?\s*([\w\\\$\.]+)\s*;',s):
        d,_,hi,lo,n=m.groups()
        if hi is None: ports[d].append(n)
        else: ports[d]+= [f'{n}[{b}]' for b in range(int(lo),int(hi)+1)]
    insts=[]
    for m in re.finditer(r'^\s*([A-Z][A-Z0-9_]*_X\d+)\s+(\S+)\s*\((.*?)\);',s,re.S|re.M):
        pins=dict((p,n.strip()) for p,n in re.findall(r'\.(\w+)\(([^()]*)\)',m.group(3)))
        insts.append((m.group(1),m.group(2),pins))
    assigns=re.findall(r'assign\s+([^=;]+?)\s*=\s*([^;]+?)\s*;',s)
    return ports,insts,assigns
def run(lib,nl,slew=0.02,outload=3.0):
    cells=load(lib); ports,insts,assigns=netlist(nl)
    alias={}
    for l,r in assigns: alias[l.strip()]=r.strip()
    def res(n):
        n=n.strip()
        while n in alias: n=alias[n]
        return n
    load_={}; drv={}
    for ct,nm,pins in insts:
        c=cells[ct]
        for p,n in pins.items():
            n=res(n)
            if c['pins'][p]['dir']=='input': load_[n]=load_.get(n,0)+c['pins'][p]['cap']
            else: drv[n]=(ct,nm,pins)
    for o in ports['output']: load_[res(o)]=load_.get(res(o),0)+outload
    arr={}  # net -> {'r':(t,slew),'f':(t,slew)}
    for n in ports['input']: arr[n]={'r':(0.0,slew),'f':(0.0,slew)}
    for n in('1\'h0','1\'h1',"1'b0","1'b1"): arr[n]={'r':(0.0,0.0),'f':(0.0,0.0)}
    import sys; sys.setrecursionlimit(10000)
    def get(n):
        n=res(n)
        if n in arr: return arr[n]
        ct,nm,pins=drv[n]; c=cells[ct]
        outp=[p for p,x in pins.items() if res(x)==n][0]
        best={'r':(0.0,0.0),'f':(0.0,0.0)}; cl=load_.get(n,0.0)
        for a in c['arcs']:
            if a['out']!=outp or a['rel'] not in pins: continue
            ia=get(pins[a['rel']])
            for oe,(tk,sk) in (('r',('cell_rise','rise_transition')),('f',('cell_fall','fall_transition'))):
                if tk not in a['tabs']: continue
                ies={'positive_unate':[oe],'negative_unate':['f' if oe=='r' else 'r']}.get(a['sense'],['r','f'])
                for ie in ies:
                    t0,s0=ia[ie]; d=interp(a['tabs'][tk],s0,cl); so=interp(a['tabs'][sk],s0,cl)
                    if t0+d>best[oe][0]: best[oe]=(t0+d,so)
        arr[n]=best; return best
    wd=0.0; wn=None
    for o in ports['output']:
        a=get(o)
        for e in 'rf':
            if a[e][0]>wd: wd=a[e][0]; wn=o
    area=sum(cells[ct]['area'] for ct,_,_ in insts)
    return wd*1000,area,len(insts),wn
if __name__=='__main__':
    lib,nl=sys.argv[1],sys.argv[2]; sl=float(sys.argv[3]) if len(sys.argv)>3 else 0.02; ol=float(sys.argv[4]) if len(sys.argv)>4 else 3.0
    d,a,n,o=run(lib,nl,sl,ol); print(f'delay={d:.1f} ps area={a:.3f} cells={n} worst_out={o}')
