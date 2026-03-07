import asyncio
from config.omega_params import OMEGA
from utils.logger import log

class WormholeRouter:
    """
    🌌 WORMHOLE RISK ROUTER (Dobrando o espaço de perdas)
    Quando uma posição principal está afundando em direção ao Stop Loss (ex: 80% do percurso),
    nós abrimos um "Buraco de Minhoca": engatilhamos micro-posições agressivas de hedge
    (Gamma Scalping) para extrair valor do micro-ruído do pânico, amortizando a perda.
    """
    def __init__(self, bridge):
        self.bridge = bridge
        self.active_wormholes = {}

    def monitor_event_horizon(self, position: dict):
        """Avalia se uma posição está sendo tragada para o abismo linear do SL"""
        ticket = position.get('ticket')
        if not ticket or ticket in self.active_wormholes:
            return

        pnl = position.get('profit', 0.0)
        sl_price = position.get('sl', 0.0)
        entry_price = position.get('open_price', 0.0)
        volume = position.get('volume', 0.01)
        p_type = position.get('type', "BUY")
        symbol = position.get('symbol') or position.get('symbol_name', "")

        # Aproximando a perda total se bater no SL
        if sl_price == 0.0:
            return

        # Simplified drawdown %: (current_price - entry) / (sl - entry)
        current_price = position.get('price_current', entry_price)
        if entry_price == sl_price:
            return
            
        drawdown_pct = (current_price - entry_price) / (sl_price - entry_price)

        if drawdown_pct > 0.80 and pnl < 0: # 80% do caminho pro SL no negativo
            self._open_wormhole(ticket, symbol, volume, p_type)

    def _open_wormhole(self, ticket, symbol, volume, p_type):
        self.active_wormholes[ticket] = True
        grid_vol = max(0.01, volume * 0.1) # 10% do tamanho para o scalp reverso ou 0.01 minimo
        
        log.omega(f"🌌 [WORMHOLE OPENED] Rasgando o tecido do SL na posição {ticket}. Iniciando Gamma Scalping reverso.")
        
        wormhole_direction = "BUY" if p_type == "SELL" else "SELL"
        
        try:
            # Disparamos fogo no sentido inverso para farmar os rebotes curtos
            res = self.bridge.send_market_order(
                action=wormhole_direction,
                lot=grid_vol,
                sl=0.0, # Sem SL duro (fechado dinamicamente)
                tp=0.0, # Sem TP duro
                comment="WORMHOLE",
                magic=999999 # Magic Number do Wormhole
            )
            if res and res.get("success"):
                log.omega(f"🌌 [WORMHOLE] Micro-scalp ancorado no ticket {res.get('ticket')} com vol {grid_vol}.")
        except Exception as e:
            log.error(f"Erro ao abrir wormhole: {e}")
