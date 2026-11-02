#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build/runtime results
if [ -f local.env.sh ]; then source ./local.env.sh; fi
export LD_LIBRARY_PATH="$PWD/build/runtime${NGSPICE_RUNTIME_DIR:+:$NGSPICE_RUNTIME_DIR}:${LD_LIBRARY_PATH:-}"
case "${1:-all}" in
 digital)
    igny run --env ams-pwm-rc iverilog -g2012 -s tb -o build/pwm.vvp rtl/apb_pwm.v tests/tb.v
    igny run --env ams-pwm-rc vvp build/pwm.vvp >results/digital.log 2>&1
    ;;
 analogue)
    python3 scripts/bridge.py
    cd build
    for duty in 0 64 128 192 256; do
       igny run --env ams-pwm-rc ngspice -b -o "../results/analogue_${duty}.log" "rc_${duty}.cir"
    done
    ;;
 *) exit 2 ;;
esac
