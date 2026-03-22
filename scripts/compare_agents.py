import json
import os
import glob
from collections import Counter

base_dir = "d:/DubaiMatrixASI/data/audits/ghost_trade_audits"

def analyze_agents(category):
    files = glob.glob(f"{base_dir}/{category}/*.json")
    bull_counter = Counter()
    bear_counter = Counter()
    total_files = len(files)
    
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as j:
                data = json.load(j)
                bull_agents = data.get("swarm_intelligence", {}).get("bull_agents", [])
                bear_agents = data.get("swarm_intelligence", {}).get("bear_agents", [])
                bull_counter.update(bull_agents)
                bear_counter.update(bear_agents)
        except: pass
    
    return bull_counter, bear_counter, total_files

e_bull, e_bear, e_total = analyze_agents("errados")
c_bull, c_bear, c_total = analyze_agents("corretos")

def print_top(name, counter, total):
    print(f"\n--- TOP AGENTS in {name} (N={total}) ---")
    for agent, count in counter.most_common(10):
        print(f"  {agent:30}: {count/total*100:.1f}%")

print_top("ERRADOS (BULL)", e_bull, e_total)
print_top("CORRETOS (BULL)", c_bull, c_total)
