import json
import os
import glob

files = [
    "d:/DubaiMatrixASI/data/audits/ghost_trade_audits/errados/GST_1774228929323.json",
    "d:/DubaiMatrixASI/data/audits/ghost_trade_audits/errados/GST_1774228929592.json",
    "d:/DubaiMatrixASI/data/audits/ghost_trade_audits/errados/GST_1774228930167.json",
    "d:/DubaiMatrixASI/data/audits/ghost_trade_audits/errados/GST_1774228931028.json",
    "d:/DubaiMatrixASI/data/audits/ghost_trade_audits/errados/GST_1774230239646.json",
    "d:/DubaiMatrixASI/data/audits/ghost_trade_audits/errados/GST_1774230242524.json",
    "d:/DubaiMatrixASI/data/audits/ghost_trade_audits/errados/GST_1774230296912.json",
    "d:/DubaiMatrixASI/data/audits/ghost_trade_audits/errados/GST_1774230303454.json",
    "d:/DubaiMatrixASI/data/audits/ghost_trade_audits/errados/GST_1774230304703.json",
    "d:/DubaiMatrixASI/data/audits/ghost_trade_audits/errados/GST_1774230345261.json",
    "d:/DubaiMatrixASI/data/audits/ghost_trade_audits/errados/GST_1774230357087.json",
    "d:/DubaiMatrixASI/data/audits/ghost_trade_audits/errados/GST_1774230410294.json",
    "d:/DubaiMatrixASI/data/audits/ghost_trade_audits/errados/GST_1774230420949.json",
    "d:/DubaiMatrixASI/data/audits/ghost_trade_audits/errados/GST_1774230470487.json",
    "d:/DubaiMatrixASI/data/audits/ghost_trade_audits/errados/GST_1774230531250.json"
]

results = []
for f in files:
    try:
        with open(f, 'r') as j:
            data = json.load(j)
            results.append({
                "id": data.get("id"),
                "veto": data.get("veto_reason"),
                "coherence": data.get("coherence"),
                "phi": data.get("phi"),
                "signal": data.get("signal_strength"),
                "res": data.get("result"),
                "tp": data.get("tp_price"),
                "close": data.get("close_price")
            })
    except Exception as e:
        print(f"Error loading {f}: {e}")

print(json.dumps(results, indent=2))
