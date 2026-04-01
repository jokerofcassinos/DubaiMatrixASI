# 🛠️ SOLÉNN Ω: MetaTrader 5 Connection Checklist

O servidor Python (SOLÉNN Master) está **ativo e aguardando** no endereço `127.0.0.1:9999`. Se o MetaTrader 5 ainda não conectou, siga rigorosamente estes 5 passos:

### 1. Adicionar 127.0.0.1 à Lista de Permissões
O MT5 bloqueia conexões de rede por padrão.
- Vá para: **Ferramentas (Tools) > Opções (Options) > Expert Advisors**.
- Selecione: **"Permitir WebRequest para as URLs listadas"**.
- Adicione as seguintes URLs:
  - `http://127.0.0.1:9999`
  - `http://localhost:9999`
  - `127.0.0.1`

### 2. Permitir Importação de DLL (WinAPI Sockets)
Embora usemos funções nativas, por precaução:
- No mesmo menu de OPÇÕES, selecione: **"Permitir importação de DLL"**.
- Ao carregar o EA no gráfico, certifique-se que na aba **"Comum"** também esteja selecionado **"Permitir importação de DLL"**.

### 3. Recompilar o Expert Advisor (Ω-V5)
Como eu alterei o código `.mq5`, o MetaTrader precisa gerar um novo `.ex5`.
- Abra o MetaEditor (F4).
- Clique em **MQL5\Experts\SOLENN\EA_SOLENN_Agent.mq5**.
- Pressione **F7 (Compilar)**. Certifique-se de que não há erros.

### 4. Verificar Inputs do EA
Ao arrastar o EA para o gráfico (ou abrir suas propriedades):
- Verifique se o parâmetro `InpPort` está em **9999**.
- Verifique se o parâmetro `InpHost` está em **127.0.0.1**.

### 5. Checar a aba "Experts" (Aba de Logs)
No rodapé do MT5, vá na aba **"Experts"**. Lá deve aparecer um destes erros:
- `☢️ [Ω-HFT] Socket Create FAIL: 4014` (Sistema impediu o socket, verifique Passo 1).
- `☣️ [Ω-HFT] Socket Connect FAIL: 5273` (Conexão recusada, verifique se o script `main.py` ainda está rodando).
- `💎 [Ω-HFT] Socket Success` (Se tudo estiver correto).

---
**Observação:** O script de autodiagnóstico (`check_hftp_server.py`) confirmou que o servidor Python está OK. O bloqueio está ocorrendo dentro do ambiente MetaTrader.
