"""
Agente Ph.D. focado em Geodésicas Temporais.
Mapeia o tempo bidimensionalmente, não como um fluxo linear, mas como uma topologia 
de toruses, onde aberturas de sessões e resets de H1 criam poços gravitacionais
de liquidez na Microestrutura.
"""

from datetime import datetime, timezone
import math
from core.consciousness.agents.base import BaseAgent, AgentSignal

class TemporalGeodesicAgent(BaseAgent):
    def __init__(self, weight: float = 3.6):
        super().__init__("TemporalGeodesic", weight)
        
    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        if not snapshot.timestamp:
            return AgentSignal(self.name, 0.0, 0.0, "Time Data Missing", self.weight)
            
        if isinstance(snapshot.timestamp, datetime):
            dt = snapshot.timestamp
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        else:
            try:
                dt = datetime.fromtimestamp(float(snapshot.timestamp), tz=timezone.utc)
            except Exception:
                return AgentSignal(self.name, 0.0, 0.0, "Invalid Time Format", self.weight)
                
        hour = dt.hour
        minute = dt.minute
        second = dt.second
        
        signal = 0.0
        confidence = 0.0
        reason = "Continuum Temporal Estável"
        
        # 1. ═══ CURVATURAS MICRO-TEMPORAIS (Top e Bottom de Hora) ═══
        # Algoritmos VWAP/TWAP tendem a ser agressivos ou finalizar cotas nestes períodos
        if minute >= 55 or minute <= 5:
            confidence = 0.65
            reason = "Distorção Teta: H1 Institutional Roll-Over"
            
        # OMEGA-CLASS Time Zones: NY Open, London Open, Asia Fix
        if 13 <= hour < 15:
            confidence += 0.25
            reason = "Singularidade: NY Open Liquidity Hunt"
        elif 7 <= hour < 9:
            confidence += 0.20
            reason = "Singularidade: London Open Flush"
        elif 20 <= hour <= 21:
            # NY Close / Asia Transition - Fading momentum
            confidence += 0.15
            reason = "Singularidade: NY Close Fading"
            
        if confidence < 0.4:
            return AgentSignal(self.name, 0.0, 0.0, "Time Continuum Flat", self.weight)
            
        # 2. ═══ INTERAÇÃO COM A MATRIZ DE LIQUIDEZ ═══
        # O agente temporal é contra-tendência em pontos de Poço Gravitacional
        # Se o mercado estica exatamente num Poço, os MM's estão buscando liquidez para reverter
        flow_pressure = snapshot.metadata.get("orderbook_pressure", 0.0)
        
        # Função de onda senoidal baseada nos segundos da virada de minuto (Micro-HFT)
        # 0s e 30s são os topos da onda (pontos de sincronização dos bots HFT)
        sync_wave = math.cos((second % 30) / 30.0 * 2 * math.pi)
        
        if flow_pressure > 0.5 and sync_wave > 0.8:
            # Exaustão compradora no momento de Sincronização e Poço Temporal
            signal = -1.0
            reason += f" | Short Peak Sync (Wave: {sync_wave:.2f})"
        elif flow_pressure < -0.5 and sync_wave > 0.8:
            # Exaustão vendedora no momento exato de Sincronização
            signal = 1.0
            reason += f" | Buy Dip Sync (Wave: {sync_wave:.2f})"
        else:
            return AgentSignal(self.name, 0.0, 0.0, "Sem Sincronização Fractal para Ignição Temporal", self.weight)
            
        confidence = min(confidence + (sync_wave * 0.1), 1.0)
        return AgentSignal(self.name, signal, confidence, reason, self.weight)
