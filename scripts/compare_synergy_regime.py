import json
import os
import glob
from collections import defaultdict

base_dir = "d:/DubaiMatrixASI/data/audits/ghost_trade_audits"

def extract_detailed_stats(category):
    files = glob.glob(f"{base_dir}/{category}/*.json")
    regime_stats = defaultdict(list)
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as j:
                data = json.load(j)
                veto = data.get("veto_reason", "")
                if "SYNERGY" in veto or "UNKNOWN_REGIME_INCOHERENCE" in veto or "DRIFT_COHERENCE" in veto:
                    regime = data.get("snapshot", {}).get("regime", "UNKNOWN")
                    regime_stats[regime].append({
                        "phi": data.get("phi", 0),
                        "coherence": data.get("coherence", 0),
                        "signal": data.get("signal_strength", 0)
                    })
        except: pass
    return regime_stats

errados_regime = extract_detailed_stats("errados")
corretos_regime = extract_detailed_stats("corretos")

print("--- REGIME ANALYSIS: ERRADOS (False Negatives) ---")
for r, items in errados_regime.items():
    print(f"Regime {r}: {len(items)} cases")

print("\n--- REGIME ANALYSIS: CORRETOS (True Negatives) ---")
for r, items in corretos_regime.items():
    print(f"Regime {r}: {len(items)} cases")
