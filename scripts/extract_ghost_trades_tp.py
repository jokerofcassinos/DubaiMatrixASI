import json
import os
import sys
import argparse
from datetime import datetime
from collections import Counter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BASE_DIR = os.path.join(PROJECT_ROOT, "data", "audits", "ghost_trade_audits")

def load_all_ghosts():
    ghosts = []
    # Load from corretos and errados
    for category in ["corretos", "errados"]:
        cat_dir = os.path.join(BASE_DIR, category)
        if os.path.exists(cat_dir):
            for f in os.listdir(cat_dir):
                if f.endswith(".json"):
                    try:
                        with open(os.path.join(cat_dir, f), 'r', encoding='utf-8') as j:
                            ghosts.append(json.load(j))
                    except Exception:
                        pass
    return ghosts

def run_analytics(ghosts):
    if not ghosts:
        print("\n❌ Nenhum ghost trade finalizado encontrado para análise.")
        print("Certifique-se de que os trades em 'pendentes/' foram fechados (TP/SL hit).")
        return

    total = len(ghosts)
    corretos = [g for g in ghosts if g.get("result") == "TRUE_NEGATIVE"]
    errados = [g for g in ghosts if g.get("result") == "FALSE_NEGATIVE"]
    
    wr = (len(corretos) / total) * 100 if total > 0 else 0
    
    print(f"\n📊 [GHOST ANALYTICS DASHBOARD]")
    print("="*80)
    print(f"Total de Vetos Auditados: {total}")
    print(f"✅ VETOS CORRETOS (Salvou da Perda): {len(corretos)} ({wr:.1f}%)")
    print(f"🔥 VETOS ERRADOS (Custou Lucro)   : {len(errados)} ({100-wr:.1f}%)")
    print("-" * 80)

    # Ranking de Vetos que mais custaram dinheiro
    veto_losses = {}
    for g in errados:
        reason = g.get("veto_reason", "Unknown").split("(")[0].strip().split(":")[0].strip()
        pnl = abs(g.get("close_price", 0) - g.get("entry_price", 0))
        veto_losses[reason] = veto_losses.get(reason, 0) + pnl
    
    sorted_losses = sorted(veto_losses.items(), key=lambda x: x[1], reverse=True)
    print("\n💀 TOP VETOS ASSASSINOS (Ranking de PnL Virtual Perdido):")
    for reason, loss in sorted_losses[:10]:
        print(f"  - {reason:30} : ${loss:,.2f}")

    # Heatmap de Confiança vs Resultado
    conf_buckets = {"Low (<0.6)": [0, 0], "Mid (0.6-0.8)": [0, 0], "High (>0.8)": [0, 0]}
    for g in ghosts:
        c = g.get("confidence", 0)
        bucket = "Low (<0.6)" if c < 0.6 else "Mid (0.6-0.8)" if c < 0.8 else "High (>0.8)"
        res_idx = 0 if g.get("result") == "TRUE_NEGATIVE" else 1
        conf_buckets[bucket][res_idx] += 1
    
    print("\n🔥 HEATMAP: CONFIANÇA vs RESULTADO (Eficiência do Veto):")
    for b, counts in conf_buckets.items():
        sub_total = sum(counts)
        acc = (counts[0] / sub_total * 100) if sub_total > 0 else 0
        print(f"  {b:15} | ✅ {counts[0]:3} | 🔥 {counts[1]:3} | Taxa de Acerto do Veto: {acc:5.1f}%")
    print("="*80 + "\n")

def list_cycles():
    pendentes_path = os.path.join(BASE_DIR, "pendentes")
    if not os.path.exists(pendentes_path):
        print("❌ Diretório de pendentes não encontrado.")
        return
    
    print("\n📂 [GHOST CYCLES DISPONÍVEIS]")
    print("="*80)
    found_any = False
    for date_dir in sorted(os.listdir(pendentes_path), reverse=True):
        day_path = os.path.join(pendentes_path, date_dir)
        if not os.path.isdir(day_path): continue
        
        print(f"\n📅 DATA: {date_dir}")
        for cycle_dir in sorted(os.listdir(day_path)):
            cycle_path = os.path.join(day_path, cycle_dir)
            meta_file = os.path.join(cycle_path, "cycle_meta.json")
            if os.path.exists(meta_file):
                found_any = True
                with open(meta_file, 'r') as f:
                    meta = json.load(f)
                    ghost_count = len([x for x in os.listdir(cycle_path) if x.endswith(".json") and x != "cycle_meta.json"])
                    print(f"  - Código: {meta['code']:20} | Ghosts Ativos: {ghost_count:2} | Início: {meta['start_iso']}")
    
    if not found_any:
        print("Nenhum ciclo ativo encontrado em 'pendentes/'.")
    print("-" * 80 + "\n")

def run_forensics(cycle_code):
    pendentes_path = os.path.join(BASE_DIR, "pendentes")
    found = False
    if not os.path.exists(pendentes_path): return
    
    for date_dir in os.listdir(pendentes_path):
        day_path = os.path.join(pendentes_path, date_dir)
        if not os.path.isdir(day_path): continue
        
        for cycle_dir in os.listdir(day_path):
            cycle_path = os.path.join(day_path, cycle_dir)
            meta_file = os.path.join(cycle_path, "cycle_meta.json")
            if os.path.exists(meta_file):
                with open(meta_file, 'r') as f:
                    meta = json.load(f)
                    if meta.get("code") == cycle_code:
                        found = True
                        print(f"\n🔍 [VISUAL FORENSICS: {cycle_code}]")
                        print("="*80)
                        
                        screenshot = [f for f in os.listdir(cycle_path) if f.startswith("chart_") and f.endswith(".png")]
                        if screenshot:
                            print(f"🖼️  CHART IMAGE: {screenshot[0]}")
                            print(f"📍 LOCALIZAÇÃO: {os.path.abspath(os.path.join(cycle_path, screenshot[0]))}")
                        
                        print("\n👻 GHOSTS REGISTRADOS (Contagem da esquerda para direita):")
                        ghost_files = sorted([x for x in os.listdir(cycle_path) if x.endswith(".json") and x != "cycle_meta.json"], 
                                           key=lambda x: (int(x.split(".")[0].split("_")[0]), x))
                        
                        for g_file in ghost_files:
                            try:
                                with open(os.path.join(cycle_path, g_file), 'r', encoding='utf-8') as gj:
                                    g = json.load(gj)
                                    pos = g.get("candle_pos")
                                    reason = g.get("veto_reason", "").split("(")[0][:60]
                                    print(f"  [{pos:4}] | {g['direction']:4} | VETO: {reason}")
                                    print(f"         🧠 Φ={g.get('phi',0):.3f} | Conf={g.get('confidence',0):.2f} | Sig={g.get('signal_strength',0):.2f} | {g['entry_time'][11:19]}")
                            except Exception:
                                pass
                        print("="*80 + "\n")
    if not found:
        print(f"❌ Ciclo {cycle_code} não encontrado.")

def main():
    parser = argparse.ArgumentParser(description="Ghost Trade Analytics & Forensics Dashboard")
    parser.add_argument("--analytics", action="store_true", help="Rodar estatísticas de performance dos vetos")
    parser.add_argument("--cycle", type=str, help="Ver detalhes visuais de um ciclo específico")
    parser.add_argument("--list-cycles", action="store_true", help="Listar ciclos disponíveis")
    
    args = parser.parse_args()
    
    if args.list_cycles:
        list_cycles()
    elif args.cycle:
        run_forensics(args.cycle)
    elif args.analytics:
        run_analytics(load_all_ghosts())
    else:
        # Modo default inteligente
        ghosts = load_all_ghosts()
        if ghosts:
            run_analytics(ghosts)
        else:
            list_cycles()

if __name__ == "__main__":
    main()

