"""Feed-forward interface: recorded RTL levels -> explicit 1.8 V PWL source."""
from pathlib import Path
import csv,json,hashlib
root=Path(__file__).resolve().parents[1]
records=[]
for duty in (0,64,128,192,256):
    path=root/f'results/digital_{duty}.csv'
    with path.open() as f:rows=[(int(r['time_ns']),int(r['logic'])) for r in csv.DictReader(f)]
    assert len(rows)==80*256
    assert all(t==i*1000 and bit in (0,1) for i,(t,bit) in enumerate(rows))
    points=[(0.,rows[0][1]*1.8)]
    previous=rows[0][1]
    for ns,bit in rows[1:]:
        if bit!=previous:
            t=ns*1e-9
            points.extend(((t,previous*1.8),(t+1e-9,bit*1.8)))
            previous=bit
    duration=(rows[-1][0]+1000)*1e-9
    points.append((duration,previous*1.8))
    pwl='\n'.join(f'+ {t:.12g} {v:.12g}' for t,v in points)
    text=f'''RTL PWM driving ideal RC filter · duty {duty}/256
VPWM pwm 0 PWL(
{pwl}
+)
R1 pwm vout 10k
C1 vout 0 100n IC=0
.options reltol=1e-6 abstol=1e-12
.control
set noaskquit
set wr_singlescale
set wr_vecnames
tran 0.5u {duration:.12g} 0 0.5u uic
wrdata ../results/analogue_{duty}.dat v(pwm) v(vout)
quit
.endc
.end
'''
    (root/f'build/rc_{duty}.cir').write_text(text)
    records.append(dict(duty=duty,trace_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                        samples=len(rows),pwl_points=len(points),duration_s=duration))
(root/'results/bridge.json').write_text(json.dumps(dict(high_V=1.8,low_V=0.,time_unit='ns',ramp_s=1e-9,cases=records),indent=2)+'\n')
print('PWM_RECORDED_WAVEFORMS_TRANSLATED',len(records))
