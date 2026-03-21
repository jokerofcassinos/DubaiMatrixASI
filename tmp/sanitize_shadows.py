import json
import os

file_path = "d:/DubaiMatrixASI/data/audits/shadow_trades.json"

if not os.path.exists(file_path):
    print("File not found.")
    exit()

with open(file_path, "r", encoding="utf-8") as f:
    trades = json.load(f)

count = 0
for trade in trades:
    if trade.get("status") == "OPEN":
        # Detect large default distances
        dist_sl = abs(trade["entry_price"] - trade["sl_price"])
        dist_tp = abs(trade["entry_price"] - trade["tp_price"])
        
        if dist_sl >= 499 or dist_tp >= 999:
            # Re-calibrar para 50/100 pontos (mais realista p/ BTC scalp se ATR estava bugado)
            # Ou apenas marcar como CLOSED/INVALID para limpar o log do usuário
            # Vamos usar 50/100 points como um fallback razoável
            new_sl = 50.0
            new_tp = 100.0
            
            if trade["direction"] == "BUY":
                trade["sl_price"] = trade["entry_price"] - new_sl
                trade["tp_price"] = trade["entry_price"] + new_tp
            else:
                trade["sl_price"] = trade["entry_price"] + new_sl
                trade["tp_price"] = trade["entry_price"] - new_tp
            count += 1

print(f"Sanitized {count} shadow trades.")

with open(file_path, "w", encoding="utf-8") as f:
    json.dump(trades, f, indent=2, ensure_ascii=False)
