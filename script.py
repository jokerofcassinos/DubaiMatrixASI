import json
import glob
import os

directory = r"D:\DubaiMatrixASI\data\audits\ghost_trade_audits\errados\2026-03-24\cycle_001"

files = [
    "1_1.json", "1.json", "2_1.json", "2_2.json", "2_3.json", "2.json", 
    "3_1.json", "3_2.json", "3_3.json", "3.json", "4_1.json", "4_2.json", 
    "4_3.json", "5_4.json", "5_5.json", "5_6.json", "6_3.json", "7_1.json", 
    "7_2.json", "7_3.json", "7.json", "8_1.json", "8.json", "9_1.json", 
    "9_2.json", "9.json", "10_3.json", "11_1.json", "11_2.json", "11.json", 
    "12.json", "13_1.json", "13.json"
]

output_file = r"D:\DubaiMatrixASI\summary.txt"

def analyze_agents(bull, bear):
    key_agents = ["TrendAgent", "MomentumAgent", "MacroBiasAgent", "LiquidationVacuumAgent", "ExplosionDetectorAgent"]
    bull_keys = [a for a in bull if a in key_agents]
    bear_keys = [a for a in bear if a in key_agents]
    return f"Bull Keys: {bull_keys} | Bear Keys: {bear_keys}"

with open(output_file, "w") as out:
    for filename in files:
        filepath = os.path.join(directory, filename)
        if not os.path.exists(filepath):
            out.write(f"--- File: {filename} NOT FOUND ---\n\n")
            continue
            
        with open(filepath, "r") as f:
            data = json.load(f)
            
        out.write(f"--- File: {filename} ---\n")
        out.write(f"Veto Reason: {data.get('veto_reason')}\n")
        out.write(f"Regime: {data.get('snapshot', {}).get('regime')}\n")
        out.write(f"Phi: {data.get('phi')}\n")
        
        metadata = data.get('snapshot', {}).get('metadata', {})
        out.write(f"Tick Vel: {metadata.get('tick_velocity')} | Ent: {metadata.get('shannon_entropy')} | Jounce: {metadata.get('jounce')} | VPulse: {metadata.get('v_pulse_detected')}\n")
        
        bull = data.get('swarm_intelligence', {}).get('bull_agents', [])
        bear = data.get('swarm_intelligence', {}).get('bear_agents', [])
        
        out.write(analyze_agents(bull, bear) + "\n")
        out.write(f"Bull Total: {len(bull)} | Bear Total: {len(bear)}\n\n")
