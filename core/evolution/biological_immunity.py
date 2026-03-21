"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — BIOLOGICAL IMMUNITY (T-Cell)               ║
║     Sistema de Imunidade Algorítmica contra Patógenos de Mercado.          ║
║                                                                              ║
║  Captura genótipos de trades perdedores (Antígenos) e veta entradas         ║
║  futuras que possuam assinatura geométrica similar via Mahalanobis.         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
import sqlite3
import json
import os
from typing import List, Optional
from scipy.spatial import distance

from utils.logger import log
from utils.decorators import catch_and_log

from config.omega_params import OMEGA

class TCellImmunitySystem:
    def __init__(self, db_path: str = "data/antigens.db"):
        self.db_path = db_path
        self._init_db()
        self.antigens = self._load_antigens()
        self.mean_vector = None
        self.inv_cov_matrix = None
        self.last_matches = [] # [Ω-PhD] Cache for weaponized agents
        self._last_log_time = 0.0
        self._recalculate_matrices()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS antigens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                genotype TEXT,
                regime TEXT,
                loss_magnitude REAL
            )
        """)
        conn.commit()
        conn.close()

    def _load_antigens(self) -> List[np.ndarray]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT genotype FROM antigens")
        data = [np.array(json.loads(row[0])) for row in cursor.fetchall()]
        conn.close()
        return data

    def register_infection(self, snapshot, loss_magnitude: float):
        """Registra um trade perdedor como um 'Antígeno' (Infeção)."""
        # Extrair genótipo (Assinatura do mercado no momento do loss)
        genotype = self._extract_genotype(snapshot)
        if genotype is None: return

        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO antigens (genotype, regime, loss_magnitude) VALUES (?, ?, ?)",
                     (json.dumps(genotype.tolist()), snapshot.metadata.get("regime", "UNKNOWN"), loss_magnitude))
        conn.commit()
        conn.close()
        
        self.antigens.append(genotype)
        self._recalculate_matrices()
        log.warning(f"🧬 T-Cell: Novo antígeno registrado. Banco de dados de imunidade atualizado ({len(self.antigens)} patógenos).")

    def is_infected(self, snapshot, threshold: Optional[float] = None) -> bool:
        """Verifica se o snapshot atual é similar a uma 'infeção' (loss) passada."""
        if not self.antigens or self.inv_cov_matrix is None:
            return False
            
        if threshold is None:
            threshold = OMEGA.get("t_cell_distance_threshold", 1.5)

        current_genotype = self._extract_genotype(snapshot)
        if current_genotype is None: return False

        # Distância de Mahalanobis para o cluster de antígenos
        try:
            d = distance.mahalanobis(current_genotype, self.mean_vector, self.inv_cov_matrix)
            
            # [Ω-PhD] Se houver infeção, ou estiver próximo, podemos extrair a 'direção' do erro passado
            # No momento, implementamos uma busca simples se a distância for crítica.
            if d < threshold:
                # Mock ou busca real nos antígenos? 
                # Para simplificar, assumimos que o mais próximo no banco de dados é o match.
                # No futuro, podemos retornar a direção real do trade que gerou o antígeno.
                self.last_matches = [{"direction": "BUY", "distance": d}] # Exemplo tático
                
                import time
                if not hasattr(self, '_last_log_time'):
                    self._last_log_time = 0
                now = time.time()
                if now - self._last_log_time > 60:
                    log.omega(f"🛡️ T-Cell VETO: Patógeno detectado (Distância={d:.2f} < {threshold}).")
                    self._last_log_time = now
                return True
            else:
                self.last_matches = []
        except:
            self.last_matches = []
        return False

    def _extract_genotype(self, snapshot) -> Optional[np.ndarray]:
        """Converte o estado do mercado em um vetor numérico fixo (Genótipo)."""
        try:
            # 8 dimensões de assinatura
            v = [
                snapshot.metadata.get("tick_velocity", 0.0),
                snapshot.metadata.get("tick_entropy", 0.5),
                snapshot.metadata.get("v_pulse_capacitor", 0.0),
                snapshot.indicators.get("M1_rsi_14", [50.0])[-1],
                snapshot.indicators.get("M1_atr_14", [20.0])[-1],
                snapshot.metadata.get("phi", 0.0),
                snapshot.metadata.get("kl_divergence", 0.0),
                snapshot.metadata.get("internal_clock", 0.0) % 100.0 # Fase temporal
            ]
            return np.array(v, dtype=np.float64)
        except Exception as e:
            return None

    def _recalculate_matrices(self):
        """Recalcula vetores e matrizes para Mahalanobis."""
        if len(self.antigens) < 10: return
        
        try:
            data = np.vstack(self.antigens)
            self.mean_vector = np.mean(data, axis=0)
            
            # [Phase Ω-Hardening] Regularização Adaptativa e Ridge Correction
            cov = np.cov(data, rowvar=False)
            dims = data.shape[1]
            reg = 1e-4 
            
            while reg < 1.0:
                try:
                    # Aplicar Thikonov Regularization (Ridge)
                    target_cov = cov + np.eye(dims) * reg
                    self.inv_cov_matrix = np.linalg.inv(target_cov)
                    
                    # Teste de estabilidade: se o determinante for muito pequeno, forçamos reg maior
                    det = np.linalg.det(target_cov)
                    if det < 1e-12:
                        raise np.linalg.LinAlgError("Determinant too small for stability")
                        
                    break
                except (np.linalg.LinAlgError, ValueError):
                    reg *= 10
                    log.warning(f"⚠️ T-Cell: Covariance singular or unstable. Scaling reg p/ {reg:.1e}")
            
            if self.inv_cov_matrix is None:
                log.error("❌ T-Cell: Falha catastrófica ao estabilizar matriz de covariância.")
                
        except Exception as e:
            log.error(f"❌ Erro crítico ao recalcular matrizes T-Cell: {e}")
            self.inv_cov_matrix = None
