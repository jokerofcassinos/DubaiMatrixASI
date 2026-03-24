# core/consciousness/agents/neural_sentience_agent.py

from core.consciousness.agents.base import BaseAgent, AgentSignal
from utils.logger import ASILogger

logger = ASILogger("NeuralSentienceAgent")

class NeuralSentienceAgent(BaseAgent):
    """
    Agente de Sentimento Neural (LOB Spoofing/Algorithmic Panic).
    Projeto Omega-8: Neural Sentience.
    
    Analisa os "Flash Cancels" e o pânico do Order Book.
    Se players massivos estão enchendo e removendo liquidez rapidamente,
    eles estão manipulando ou fugindo. O agente converte esse pânico em 
    ação direcional de altíssima convicção.
    """
    
    def __init__(self, weight=5.5):
        super().__init__("NeuralSentienceAgent")
        self.weight = weight

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        book_data = snapshot.indicators.get("order_book", {})
        if not book_data:
            return AgentSignal(self.name, 0.0, 0.0, "Sem OrderBook", self.weight)
            
        # Get Flash Cancel Metrics
        bid_panic = book_data.get("bid_flash_cancels", 0.0)
        ask_panic = book_data.get("ask_flash_cancels", 0.0)
        
        panic_threshold = 50.0 
        
        signal = 0.0
        reason = "DOM Estável"
        
        if bid_panic > panic_threshold and ask_panic < (bid_panic * 0.3):
            signal = -0.85 
            reason = f"Bid Panic Detected ({bid_panic:.1f} Lots vanished). Buyers fleeing."
            self._log_strike("BEAR_SENTIENCE", reason, signal)
            
        elif ask_panic > panic_threshold and bid_panic < (ask_panic * 0.3):
            signal = 0.85
            reason = f"Ask Panic Detected ({ask_panic:.1f} Lots vanished). Sellers fleeing."
            self._log_strike("BULL_SENTIENCE", reason, signal)
            
        elif ask_panic > panic_threshold and bid_panic > panic_threshold:
            reason = "Caos Bilateral (Ambos fugindo)"
            
        if not hasattr(snapshot, "metadata"):
            snapshot.metadata = {}
            
        snapshot.metadata["bid_panic_level"] = bid_panic
        snapshot.metadata["ask_panic_level"] = ask_panic
            
        return AgentSignal(self.name, signal, abs(signal), reason, self.weight)

    def _log_strike(self, attack_vector: str, context: str, signal: float):
        logger.omega(f"🧠 [NEURAL SENTIENCE] 💀 {attack_vector} | S:{signal:+.2f} | {context}")
