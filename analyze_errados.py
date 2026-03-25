import os
import glob
import json
from collections import Counter

# Caminho para os arquivos
base_path = r"d:\DubaiMatrixASI\data\audits\ghost_trade_audits\errados\2026-03-25\cycle_001"
files = glob.glob(os.path.join(base_path, "*.json"))

veto_reasons = Counter()
pnl_lost = 0.0
total_files = len(files)

details = []

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            data = json.load(file)
            veto = data.get("veto_reason", "UNKNOWN")
            veto_reasons[veto] += 1
            
            # Simulated PnL (assuming TP hit)
            tp_dist = abs(data.get("take_profit", 0) - data.get("entry_price", 0))
            if tp_dist > 0:
                pnl_lost += tp_dist * data.get("lot_size", 1.0)
                
            details.append({
                "veto": veto,
                "signal": data.get("signal", 0),
                "phi": data.get("phi", 0),
                "conf": data.get("confidence", 0),
                "coherence": data.get("coherence", 0)
            })
    except Exception as e:
        print(f"Erro ao ler {f}: {e}")

with open(r"d:\DubaiMatrixASI\analyze.txt", "w", encoding="utf-8") as out:
    out.write(f"=== ANÁLISE DE FALSOS NEGATIVOS (CYCLE 001 - 2026-03-25) ===\n")
    out.write(f"Total de trades lucrativos vetados: {total_files}\n")
    out.write("\nTop Motivos de Veto:\n")
    for reason, count in veto_reasons.most_common(10):
        pct = (count / total_files) * 100
        out.write(f" - {count} ({pct:.1f}%): {reason}\n")

    out.write(f"\nDetalhes Médios por Veto:\n")
    for top_veto, _ in veto_reasons.most_common(5):
        subset = [d for d in details if d["veto"] == top_veto]
        avg_sig = sum(abs(d["signal"]) for d in subset) / len(subset)
        avg_phi = sum(abs(d["phi"]) for d in subset) / len(subset)
        avg_coh = sum(d["coherence"] for d in subset) / len(subset)
        out.write(f"[{top_veto[:30]}...] Sig: {avg_sig:.3f} | Phi: {avg_phi:.3f} | Coh: {avg_coh:.3f}\n")
