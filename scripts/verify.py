from pathlib import Path
import re,json,csv,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results'

def source_points(text):
    body=re.search(r'VPWM\s+pwm\s+0\s+PWL\((.*?)\)',text,re.S)[1]
    pairs=[]
    for line in body.splitlines():
        fields=line.lstrip('+ ').split()
        if fields:pairs.append(list(map(float,fields)))
    return np.array(pairs)

def mapping(points,rows):
    assert len(points)>1 and np.isfinite(points).all()
    assert points[0,0]==0 and np.all(np.diff(points[:,0])>0)
    # Observe mid-cycle values independently of bridge transitions.
    t=np.array([row[0] for row in rows])*1e-9+2e-9
    bit=np.array([row[1] for row in rows])
    actual=np.interp(t,points[:,0],points[:,1])
    assert np.max(abs(actual-bit*1.8))<1e-9,'BRIDGE_LEVEL_MISMATCH'
    changes=np.flatnonzero(np.diff(bit)!=0)+1
    assert len(points)==2+2*len(changes),'BRIDGE_TRANSITION_COUNT_MISMATCH'
    for i,index in enumerate(changes):
        assert abs(points[1+2*i,0]-rows[index][0]*1e-9)<1e-12
        assert abs(points[2+2*i,0]-points[1+2*i,0]-1e-9)<1e-12

def exact_rc(points,times):
    tau=.001
    ys=np.zeros(len(points))
    for i in range(len(points)-1):
        dt=points[i+1,0]-points[i,0];u=points[i,1]
        slope=(points[i+1,1]-u)/dt
        ys[i+1]=u+slope*(dt-tau)+(ys[i]-u+slope*tau)*np.exp(-dt/tau)
    ids=np.minimum(np.searchsorted(points[:,0],times,side='right')-1,len(points)-2)
    assert ids.min()>=0
    dt=times-points[ids,0];u=points[ids,1]
    slope=(points[ids+1,1]-u)/(points[ids+1,0]-points[ids,0])
    return u+slope*(dt-tau)+(ys[ids]-u+slope*tau)*np.exp(-dt/tau)

def analog(points,a,duty):
    assert a.shape[0]>10000 and np.isfinite(a).all()
    t=a[:,0];assert np.all(np.diff(t)>0) and t[-1]>=.0204799
    expected=exact_rc(points,t)
    error=float(np.max(abs(a[:,2]-expected)))
    assert error<.0005,'RC_WAVEFORM_MISMATCH'
    start=.02048-20*256e-6
    mask=t>start;ts=np.r_[start,t[mask]];vs=np.r_[np.interp(start,t,a[:,2]),a[mask,2]]
    mean=float(np.trapezoid(vs,ts)/(ts[-1]-ts[0]))
    assert abs(mean-1.8*duty/256)<.005,'RC_MEAN_MISMATCH'
    return dict(duty=duty,mean_V=mean,target_V=1.8*duty/256,
                ripple_peak_to_peak_V=float(np.ptp(vs)),max_exact_solution_error_V=error,samples=len(a))

def verify():
    log=(R/'digital.log').read_text()
    assert 'APB_PWM_DIGITAL_PASS' in log and not re.search(r'(?i)fatal|error|mismatch',log)
    checks=int(re.search(r'APB_PWM_DIGITAL_PASS checks=(\d+)',log)[1])
    assert checks>100000
    results=[]
    for duty in (0,64,128,192,256):
        with (R/f'digital_{duty}.csv').open() as f:rows=[(int(r['time_ns']),int(r['logic'])) for r in csv.DictReader(f)]
        assert len(rows)==80*256
        bits=np.array([r[1] for r in rows]);assert ((bits==0)|(bits==1)).all()
        assert np.all(bits.reshape(80,256).sum(axis=1)==duty),'DIGITAL_DUTY_MISMATCH'
        points=source_points((ROOT/f'build/rc_{duty}.cir').read_text())
        mapping(points,rows)
        if duty>0:
            bad=points.copy();bad[:,1]*=.5
            try:mapping(bad,rows)
            except AssertionError:pass
            else:raise AssertionError('Attenuated bridge was accepted')
        a=np.loadtxt(R/f'analogue_{duty}.dat',skiprows=1)
        results.append(analog(points,a,duty))
        if duty==128:
            bad=a.copy();bad[:,2]=0
            try:analog(points,bad,duty)
            except AssertionError:pass
            else:raise AssertionError('Corrupted analogue response was accepted')
        log=(R/f'analogue_{duty}.log').read_text()
        assert 'ngspice-46 done' in log and not re.search(r'(?im)^\s*(error|fatal)\b',log)
    summary=dict(digital_checks=checks,periods_per_case=80,pwm_clock_Hz=1000000,
                 pwm_period_s=256e-6,R_ohm=10000,C_F=100e-9,tau_s=.001,
                 bridge='recorded feed-forward PWL; no live feedback',cases=results,
                 negative_controls=['Half-amplitude bridge rejected','Flat midscale analogue output rejected'])
    (R/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2));print('APB_PWM_BRIDGE_AND_RC_REFERENCE_VERIFIED')

if __name__=='__main__':verify()
