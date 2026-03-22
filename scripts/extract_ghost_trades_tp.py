import json
import os
import sys
from datetime import datetime
import sys

def main():
    shadow_path = r"d:\DubaiMatrixASI\data\audits\shadow_trades.json"
    if not os.path.exists(shadow_path):
        print(f"❌ Shadow trades file not found: {shadow_path}")
        sys.exit(1)
        
    try:
        with open(shadow_path, "r", encoding="utf-8") as f:
            trades = json.load(f)
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")
        sys.exit(1)
        
    # Extrair trades que atingiram o TP virtual (FALSE_NEGATIVE = Veto nos custou dinheiro)
    # E que possuem a nova estrutura PhD-level 
    ghost_tp = [t for t in trades if t.get("result") == "FALSE_NEGATIVE"]
    
    # Sort backwards para ver os mais recentes primeiro
    ghost_tp.sort(key=lambda x: x.get("close_time", ""), reverse=True)
    
    print(f"\n👻 [SHADOW REVELATION] {len(ghost_tp)} Trades Fantasmas Atingiram o TP (Falsos Negativos)\n")
    print("="*100)
    
    count = 0
    for t in ghost_tp:
        count += 1
        
        duration_str = ""
        entry_time_str = t.get('entry_time')
        close_time_str = t.get('close_time')
        if entry_time_str and close_time_str:
            try:
                # Python 3.11+ can parse trailing Z, but earlier versions need replace
                t1 = datetime.fromisoformat(entry_time_str.replace("Z", "+00:00"))
                t2 = datetime.fromisoformat(close_time_str.replace("Z", "+00:00"))
                duration_sec = (t2 - t1).total_seconds()
                duration_str = f" | ⏱️ TEMPO ATÉ O TP: {duration_sec:.1f}s"
            except Exception:
                pass

        print(f"[{count}] ⚡ GHOST ID: {t.get('id')} | DIR: {t.get('direction')} | ENTRY: {entry_time_str}{duration_str}")
        print(f"💰 PnL Virtual: Entrada {t.get('entry_price', 0.0):.2f} -> Saída (TP) {t.get('close_price', 0.0):.2f}")
        print(f"🛑 VETO KILLER: {t.get('veto_reason')}")
        
        # PhD Level details se houver
        if 'confidence' in t:
            print(f"🧠 METRICS: Conf={t.get('confidence'):.2f} | Sig={t.get('signal_strength'):.2f} | Φ={t.get('phi'):.3f} | Coh={t.get('coherence'):.2f}")
            mac = t.get('mc_data', '')
            if mac: print(f"🎲 {mac}")
            
            swarm = t.get("swarm_intelligence", {})
            bull = swarm.get("bull_agents", [])
            bear = swarm.get("bear_agents", [])
            print(f"  🐂 BULL ({len(bull)}): {', '.join(bull)}")
            print(f"  🐻 BEAR ({len(bear)}): {', '.join(bear)}")
            
            snap = t.get("snapshot", {})
            print(f"  🌌 REGIME: {snap.get('regime')} | ATR: {snap.get('atr'):.2f}")
            
        print("-" * 100)

if __name__ == "__main__":
    main()
