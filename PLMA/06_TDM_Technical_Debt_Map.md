# TECHNICAL DEBT MAP (TDM)
## PLMA LAYER 6 — DUBAI MATRIX ASI

> "Aentropia técnica corrói sistemas em silêncio. Identificá-la é o primeiro passo da erradicação."

### DÍVIDA TÉCNICA 01: Position Manager Simplório — [RESOLVIDO]
- **Localização:** `execution/position_manager.py` (Reescrito em Phase 18).
- **Status:** Resolvido com a implementação do sistema Smart TP de 5 gatilhos e integração com socket CLOSE.

### DÍVIDA TÉCNICA 02: Resoluções Assíncronas Inacabadas (Data Engine Background)
- **Localização:** `market/data_engine.py` / `_background_worker()`.
- **Descrição:** O `_background_worker` foi implementado para atenuar as latências brutais da API em processamento NumPy de longo escopo. Houve spikes severos reportados de >200ms recentemente que provocaram esse refactoring de Zero-Latency.
- **Risco:** [VERDE] Monitorar ativamente se a Race Condition entre a Thread Principal do `ASIBrain` lendo o `snapshot` e a atualização do `.copy()` do worker está cem por cento Thread-Safe sem Locking prolongado (`self._lock`).

### DÍVIDA TÉCNICA 03: Veto Cascade Kinematics / Datetime Imports
- **Localização:** Componentes secundários recentes (`laplace_demon.py`, `whale_profiler.py`).
- **Descrição:** Erros de Namespace/Import (`NameError`) e referências cíclicas em componentes periféricos recém introduzidos (Kinematics Engine, DateTime missing import) afetaram a integridade do framework anterior.
- **Risco:** [VERDE] Maior parte absorvida pelas correções correntes. Todavia, atesta falta da adoção de tipagens sólidas e TDD nessas raízes experimentais.
- **Solução Proposta:** Impor rotinas de Type Checking (Mypy) nos commits automáticos da ASI.

### DÍVIDA TÉCNICA 04: Falta de Tipagem Estrita nos Sinais de Agentes (Dict vs AgentSignal) — [RESOLVIDO]
- **Localização:** `core/consciousness/agents/meta_swarm.py` e interação com `quantum_thought.py`.
- **Descrição:** Agentes de segunda ordem (`ConfidenceAggregatorAgent` e `ExecutionScalerAgent`) estavam retornando dicionários crus (`{"signal": 0.0, ...}`) ao invés de instâncias instanciadas e tipadas de `AgentSignal`, causando o crash letal `AttributeError: 'dict' object has no attribute 'confidence'` no motor Quântico que tentava iterar pelas propriedades dos objetos.
- **Risco:** [RESOLVIDO] Erro sanado em 2026-03-05. A persistência de tipagem flexiva (duck typing) em zonas críticas de colapso quântico cria Single Points of Failure grotescos.
- **Solução Futura:** Estabelecer decorators de `@validate_return_type(AgentSignal)` explícito na interface da classe base.

*(Atualizado: 2026-03-05. Versão: 7.0.1-omega)*
