import json
import os
import glob

base_dir = "d:/DubaiMatrixASI/data/audits/ghost_trade_audits"

def extract_synergy_stats(category):
    files = glob.glob(f"{base_dir}/{category}/*.json")
    stats = []
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as j:
                data = json.load(j)
                veto = data.get("veto_reason", "")
                if "SYNERGY" in veto or "UNKNOWN_REGIME_INCOHERENCE" in veto:
                    stats.append({
                        "id": data.get("id"),
                        "phi": data.get("phi", 0),
                        "coherence": data.get("coherence", 0),
                        "signal": data.get("signal_strength", 0),
                        "regime": data.get("snapshot", {}).get("regime", "UNKNOWN"),
                        "direction": data.get("direction"),
                        "agents_bull": len(data.get("swarm_intelligence", {}).get("bull_agents", [])),
                        "agents_bear": len(data.get("swarm_intelligence", {}).get("bear_agents", []))
                    })
        except:
            pass
    return stats

errados = extract_synergy_stats("errados")
corretos = extract_synergy_stats("corretos")

print("--- STATS: ERRADOS (False Negatives - Lost Profit) ---")
print(json.dumps(errados, indent=2))
print("\n--- STATS: CORRETOS (True Negatives - Saved Loss) ---")
print(json.dumps(corretos, indent=2))

# Calculate averages
def print_avg(name, data):
    if not data: return
    p = sum(d['phi'] for d in data) / len(data)
    c = sum(d['coherence'] for d in data) / len(data)
    s = sum(abs(d['signal']) for d in data) / len(data)
    print(f"\nAVG {name}: Phi={p:.4f}, Coherence={c:.4f}, AbsSignal={s:.4f}, Count={len(data)}")

print_avg("ERRADOS", errados)
print_avg("CORRETOS", corretos)
