"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — SEMANTIC NLP FOR ORDER FLOW                  ║
║     Transmuta a fita de trades e o Order Book em Tokens de Linguagem         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import numpy as np

class FlowTokenizer:
    """
    NLP PARA ORDER FLOW:
    Lê a fita de micro-ticks e a converte em um "vocabulário" institucional.
    Cada evento HFT se torna uma palavra. A sequência forma uma "frase" sintática.
    """
    def __init__(self):
        self.vocab = {
            "WHALE_BUY_BOMB": 100,
            "WHALE_SELL_BOMB": 101,
            "HFT_MACHINE_GUN_BUY": 200,
            "HFT_MACHINE_GUN_SELL": 201,
            "RETAIL_NOISE": 300,
            "BID_WALL_SPOOF": 400,
            "ASK_WALL_SPOOF": 401,
            "LIQUIDITY_VACUUM": 500
        }

    def tokenize_flow(self, ticks: list, book_analysis: dict) -> list:
        tokens = []
        if not ticks:
            return tokens
        
        # 1. Análise de Ticks (Fita)
        for t in ticks:
            vol = t.get('volume', 0.0)
            flags = t.get('flags', 0)
            # Aproximação de flags de compra/venda do MT5
            is_buy = (flags & 1) != 0 # Simplificação: depende da flag exata da corretora
            
            if vol > 10.0:
                tokens.append(self.vocab["WHALE_BUY_BOMB"] if is_buy else self.vocab["WHALE_SELL_BOMB"])
            elif vol < 0.1:
                # Possível metralhadora ou varejo
                tokens.append(self.vocab["RETAIL_NOISE"])

        # 2. Análise Estrutural do Book
        if book_analysis:
            spoof = book_analysis.get('spoofing_detected', False)
            if spoof:
                tokens.append(self.vocab["BID_WALL_SPOOF"]) # simplificado

        return tokens


class MicroMarketAttention:
    """
    Numpy-based Mini Attention Mechanism.
    Mapeia qual evento passado (Token) tem mais relevância causal com o presente.
    Roda puramente na CPU local com overhead < 1ms.
    """
    def __init__(self, d_model=16):
        self.d_model = d_model
        # Matrizes de projeção aleatórias otimizáveis depois via SelfOptimizer
        self.W_q = np.random.randn(d_model, d_model) * 0.1
        self.W_k = np.random.randn(d_model, d_model) * 0.1
        self.W_v = np.random.randn(d_model, d_model) * 0.1

    def forward(self, token_embeddings):
        """
        token_embeddings: (seq_len, d_model)
        """
        if token_embeddings.shape[0] == 0:
            return np.zeros((1, self.d_model))

        Q = np.dot(token_embeddings, self.W_q)
        K = np.dot(token_embeddings, self.W_k)
        V = np.dot(token_embeddings, self.W_v)

        scores = np.dot(Q, K.T) / np.sqrt(self.d_model)
        
        # Softmax
        exp_scores = np.exp(scores - np.max(scores, axis=-1, keepdims=True))
        attention_weights = exp_scores / np.sum(exp_scores, axis=-1, keepdims=True)

        context = np.dot(attention_weights, V)
        return context[-1] # Retorna o contexto causal focado no último evento
