import json
import os
import glob
from collections import defaultdict

base_dir = "d:/DubaiMatrixASI/data/audits/ghost_trade_audits"

def extract_detailed_stats(category):
    files = glob.glob(f"{base_dir}/{category}/*.json")
    results = []
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as j:
                data = json.load(j)
                veto = data.get("veto_reason", "")
                if "SYNERGY" in veto or "UNKNOWN_REGIME_INCOHERENCE" in veto:
                    snap_meta = data.get("snapshot", {}).get("metadata", {})
                    results.append({
                        "id": data.get("id"),
                        "phi": data.get("phi", 0),
                        "coherence": data.get("coherence", 0),
                        "signal": data.get("signal_strength", 0),
                        "vel": snap_meta.get("tick_velocity", 0.0),
                        "v_pulse": 1 if snap_meta.get("v_pulse_detected", False) else 0
                    })
        except: pass
    return results

errados = extract_detailed_stats("errados")
corretos = extract_detailed_stats("corretos")

def print_k_stats(name, data):
    if not data: return
    v_avg = sum(abs(d['vel']) for d in data) / len(data)
    vp_sum = sum(d['v_pulse'] for d in data)
    print(f"\nSTATS {name}: Avg Abs Vel={v_avg:.2f}, V-Pulse Count={vp_sum}/{len(data)}")

print_k_stats("ERRADOS", errados)
print_k_stats("CORRETOS", corretos)
