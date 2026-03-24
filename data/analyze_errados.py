import os
import json
from collections import Counter
import numpy as np

dir_path = r"D:\DubaiMatrixASI\data\audits\ghost_trade_audits\errados\2026-03-24\cycle_002"

if not os.path.exists(dir_path):
    print(f"Directory {dir_path} not found.")
    exit()

files = [f for f in os.listdir(dir_path) if f.endswith('.json')]
print(f"Total files in errados: {len(files)}")

results = Counter()
veto_reasons = Counter()
bull_agents = Counter()
bear_agents = Counter()
regimes = Counter()
directions = Counter()

coherence_list = []
signal_list = []

for f in files:
    with open(os.path.join(dir_path, f), 'r') as file:
        data = json.load(file)
        
        res = data.get("result", "UNKNOWN")
        results[res] += 1
        
        directions[data.get("direction", "UNKNOWN")] += 1
        
        veto = data.get("veto_reason", "NONE")
        if veto != "NONE":
            if "NO_CONVERGENCE" in veto:
                veto_reasons["NO_CONVERGENCE"] += 1
            elif "LOW_COHERENCE" in veto:
                veto_reasons["LOW_COHERENCE"] += 1
            elif "CHOPPY" in veto:
                veto_reasons["CHOPPY_MARKET"] += 1
            elif "POOR_RR" in veto:
                veto_reasons["POOR_RR"] += 1
            elif "SUPERPOSITION" in veto:
                veto_reasons["SUPERPOSITION"] += 1
            elif "T-CELL" in veto or "Patógeno" in veto:
                veto_reasons["T-CELL_VETO"] += 1
            else:
                veto_reasons[veto] += 1
        
        regimes[data.get("snapshot", {}).get("regime", "UNKNOWN")] += 1
        
        swarm = data.get("swarm_intelligence", {})
        for a in swarm.get("bull_agents", []): bull_agents[a] += 1
        for a in swarm.get("bear_agents", []): bear_agents[a] += 1
        
        if "coherence" in data: coherence_list.append(data["coherence"])
        if "signal_strength" in data: signal_list.append(abs(data["signal_strength"]))

print("\n--- RESULTS ---")
for k, v in results.items(): print(f"{k}: {v}")

print("\n--- DIRECTIONS ---")
for k, v in directions.items(): print(f"{k}: {v}")

print("\n--- REGIMES ---")
for k, v in regimes.items(): print(f"{k}: {v}")

print("\n--- VETO REASONS ---")
for k, v in veto_reasons.most_common(): print(f"{k}: {v}")

print(f"\nAvg Coherence: {np.mean(coherence_list):.3f}")
print(f"Avg Signal Strength: {np.mean(signal_list):.3f}")

print("\n--- TOP BULL AGENTS IN ERRADOS ---")
for k, v in bull_agents.most_common(10): print(f"{k}: {v}")

print("\n--- TOP BEAR AGENTS IN ERRADOS ---")
for k, v in bear_agents.most_common(10): print(f"{k}: {v}")
