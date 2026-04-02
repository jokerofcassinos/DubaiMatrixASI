# [Plano] Estabilização de Terminal e Handshake MT5 (Ω-71)

O objetivo é resolver a bagunça visual no terminal e o travamento na inicialização do MetaTrader 5, garantindo que o SOLÉNN Ω seja resiliente mesmo quando componentes externos falham.

## User Review Required

> [!IMPORTANT]
> O redirecionamento de logs para a interface Matrix fará com que as mensagens de log apareçam dentro do quadro tático, em vez de rolar no terminal padrão. Isso manterá o design "Alien", mas exige que o terminal tenha pelo menos 95 colunas de largura.

## Proposed Changes

### [Componente] Terminal Matrix (UI)

#### [MODIFY] [solenn_terminal.py](file:///d:/DubaiMatrixASI/core/solenn_terminal.py)
- Implementar **Lock de Renderização** para evitar que múltiplas threads (Logging vs UI Thread) escrevam simultaneamente.
- Adicionar **Buffer de Log Rotativo** interno.
- Adicionar **Clear-to-EOL (ANSI [K)** em cada linha para apagar resíduos de logs antigos.
- Desativar a UI se o terminal for redimensionado para um tamanho inválido, evitando explosão de caracteres.

### [Componente] MetaBridge (MT5 Connector)

#### [MODIFY] [mt5_connector.py](file:///d:/DubaiMatrixASI/market/exchanges/mt5_connector.py)
- Adicionar flags de estado para evitar chamadas a métodos do MT5 se não estiver inicializado.

#### [MODIFY] [main.py](file:///d:/DubaiMatrixASI/main.py)
- Implementar **Timeout de Handshake (10s)**: Se o MT5 não responder em 10s, o bot cancela a tentativa e entra em modo `OBSERVAÇÃO`.
- **Redirecionamento de Root Logger**: Criar um `Handler` customizado que envia logs para `SolennTerminalMatrix.add_log()`, filtrando a saída do `StreamHandler` padrão quando a UI está ativa.

---

## Open Questions

- Você prefere que, em caso de erro no MT5, o bot **pare** ou continue apenas em modo **simulação/observação** (printando o que faria sem executar)? No plano, propus continuar em observação.

## Verification Plan

### Automated Tests
- Criar script `test_ui_resilience.py` que gera logs em alta frequência enquanto a UI renderiza para validar se o terminal permanece limpo.

### Manual Verification
- Rodar o bot com o MT5 fechado e verificar se ele cai para o modo observação em 10s sem travar.
- Redimensionar a janela do terminal durante a execução para ver se a UI se adapta ou desativa graciosamente.
