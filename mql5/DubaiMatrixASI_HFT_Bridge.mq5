//+------------------------------------------------------------------+
//|                                  DubaiMatrixASI_HFT_Bridge.mq5   |
//|                    Superintelligência Financial Omega-Class      |
//|               Zero-Latency TCP Socket Bridge to Python ASI       |
//+------------------------------------------------------------------+
#property copyright "DubaiMatrixASI"
#property link      "Omega-Level Architecture"
#property version   "1.00"
#property strict

// ---
// INPUTS
// ---
input string   InpPythonIP    = "127.0.0.1";  // IP do Python ASI
input int      InpPythonPort  = 5555;         // Porta do Python ASI
input int      InpMagicNumber = 88888888;     // Magic Number
input int      InpSlippage    = 10;           // Slippage máximo

int socket_handle = INVALID_HANDLE;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
   Print("🚀 DubaiMatrixASI HFT Bridge Inicializando...");
   Print("Tentando conectar a TCP ", InpPythonIP, ":", InpPythonPort);
   
   ConnectToASI();
   
   // Timer de 1 milissegundo para latência ultra-baixa de leitura
   EventSetMillisecondTimer(1);
   
   return(INIT_SUCCEEDED);
  }

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   EventKillTimer();
   if(socket_handle != INVALID_HANDLE)
     {
      SocketClose(socket_handle);
      socket_handle = INVALID_HANDLE;
      Print("🔴 DubaiMatrixASI Bridge Desconectado.");
     }
  }

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
   // Envia o Tick instantaneamente para a ASI Python
   if(socket_handle == INVALID_HANDLE) return;
   
   MqlTick last_tick;
   if(SymbolInfoTick(_Symbol, last_tick))
     {
      string tick_data = "TICK|" + _Symbol + "|" + 
                         DoubleToString(last_tick.bid, _Digits) + "|" + 
                         DoubleToString(last_tick.ask, _Digits) + "|" +
                         DoubleToString(last_tick.last, _Digits) + "|" +
                         DoubleToString(last_tick.volume_real, 2) + "|" + 
                         IntegerToString(last_tick.time_msc) + "\n";
                         
      SendTCP(tick_data);
     }
  }

//+------------------------------------------------------------------+
//| Timer function: Lê comandos da ASI em Sub-ms                   |
//+------------------------------------------------------------------+
void OnTimer()
  {
   if(socket_handle == INVALID_HANDLE)
     {
      // Reconexão a cada 1000ms
      static uint last_reconnect = 0;
      if(GetTickCount() - last_reconnect > 1000)
        {
         ConnectToASI();
         last_reconnect = GetTickCount();
        }
      return;
     }
     
   uint bytes_readable = SocketIsReadable(socket_handle);
   if(bytes_readable > 0)
     {
      uchar buffer[];
      // Lê tudo disponível
      int read_len = SocketRead(socket_handle, buffer, bytes_readable, 10);
      if(read_len > 0)
        {
         string commands = CharArrayToString(buffer, 0, read_len);
         ParseCommands(commands);
        }
     }
  }

bool is_socket_sending = false;

//+------------------------------------------------------------------+
//| Conecta socket TCP                                               |
//+------------------------------------------------------------------+
void ConnectToASI()
  {
   if(socket_handle != INVALID_HANDLE) SocketClose(socket_handle);
   
   socket_handle = SocketCreate();
   if(socket_handle != INVALID_HANDLE)
     {
      bool connected = SocketConnect(socket_handle, InpPythonIP, InpPythonPort, 500);
      if(!connected)
        {
         SocketClose(socket_handle);
         socket_handle = INVALID_HANDLE;
         if(is_socket_sending)
           {
            is_socket_sending = false;
           }
        }
     }
  }

//+------------------------------------------------------------------+
//| Envia mensagem TCP                                               |
//+------------------------------------------------------------------+
void SendTCP(string msg)
  {
   if(socket_handle != INVALID_HANDLE)
     {
      uchar data[];
      StringToCharArray(msg, data);
      int sent = SocketSend(socket_handle, data, ArraySize(data)-1);
      
      if(sent > 0)
        {
         if(!is_socket_sending)
           {
            Print("✅ Conexão Data-Stream Matrix (TCP) Estabilizada. ASI operante.");
            is_socket_sending = true;
           }
        }
      else if(sent < 0)
        {
         if(is_socket_sending)
           {
            Print("🔴 Fluxo TCP interrompido (Erro ", GetLastError(), "). ASI Node offline? Aguardando reconexão...");
            is_socket_sending = false;
           }
         SocketClose(socket_handle);
         socket_handle = INVALID_HANDLE;
        }
     }
  }

//+------------------------------------------------------------------+
//| Parsing de múltiplos comandos recebidos                          |
//+------------------------------------------------------------------+
void ParseCommands(string raw_data)
  {
   string lines[];
   int count = StringSplit(raw_data, '\n', lines);
   
   for(int i=0; i<count; i++)
     {
      if(StringLen(lines[i]) > 0)
         ProcessSingleCommand(lines[i]);
     }
  }

//+------------------------------------------------------------------+
//| Processa comando individual                                      |
//+------------------------------------------------------------------+
void ProcessSingleCommand(string cmd)
  {
   // Formato esperado: "ACTION|SYMBOL|LOT|SL|TP"
   string parts[];
   int count = StringSplit(cmd, '|', parts);
   if(count < 1) return;
   
   string action = parts[0];
   
   if(action == "PING")
     {
      SendTCP("PONG|OK\n");
      return;
     }
     
   if(action == "BUY" || action == "SELL")
     {
      if(count < 5) return;
      string symbol = parts[1];
      double lot = StringToDouble(parts[2]);
      double sl = StringToDouble(parts[3]);
      double tp = StringToDouble(parts[4]);
      
      ExecuteTrade(action, symbol, lot, sl, tp);
     }
   else if(action == "CLOSE")
     {
      if(count < 2) return;
      ulong ticket = (ulong)StringToInteger(parts[1]);
      ExecuteClose(ticket);
     }
  }

//+------------------------------------------------------------------+
//| Executa a Ordem                                                  |
//+------------------------------------------------------------------+
void ExecuteTrade(string action, string symbol, double lot, double sl, double tp)
  {
   MqlTradeRequest request;
   MqlTradeResult  result;
   ZeroMemory(request);
   ZeroMemory(result);
   
   request.action   = TRADE_ACTION_DEAL;
   request.symbol   = symbol;
   request.volume   = lot;
   request.type     = (action == "BUY") ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   
   // Pega preço com menor latência possível
   MqlTick last_tick;
   SymbolInfoTick(symbol, last_tick);
   request.price    = (action == "BUY") ? last_tick.ask : last_tick.bid;
   
   request.sl       = sl;
   request.tp       = tp;
   request.deviation= InpSlippage;
   request.magic    = InpMagicNumber;
   request.type_filling = ORDER_FILLING_FOK;
   request.comment  = "ASI_" + action;
   
   Print("⚡ ASI COMMAND: ", action, " ", DoubleToString(lot, 2), " ", symbol);
   
   bool success = OrderSend(request, result);
   if(success)
     {
      string msg = "RESULT|" + action + "|SUCCESS|" + IntegerToString(result.deal) + "|" + DoubleToString(result.price, _Digits) + "\n";
      SendTCP(msg);
      Print("✅ DEFERIDO: ", result.deal, " @ ", result.price);
     }
   else
     {
      string msg = "RESULT|" + action + "|ERROR|" + IntegerToString(result.retcode) + "\n";
      SendTCP(msg);
      Print("❌ REJEITADO: CÓDIGO ", result.retcode);
     }
  }

//+------------------------------------------------------------------+
//| Fechamento com Proteção Anti-Slippage                            |
//+------------------------------------------------------------------+
void ExecuteClose(ulong ticket)
  {
   if(!PositionSelectByTicket(ticket))
     {
      SendTCP("RESULT|CLOSE|ERROR|NOT_FOUND\n");
      return;
     }

   double current_profit = PositionGetDouble(POSITION_PROFIT);
   string symbol = PositionGetString(POSITION_SYMBOL);
   long type = PositionGetInteger(POSITION_TYPE);
   double lot = PositionGetDouble(POSITION_VOLUME);

   // --- PROTEÇÃO ANTI-SLIPPAGE ---
   // Se o ASI Python mandou fechar baseado num lucro que ele viu, 
   // mas no MQL5 o lucro atual já é <= 0 (negativo devido à latência/spread), ABORTAR.
   if(current_profit <= 0.0)
     {
      Print("⚠️ CLOSE ABORTADO: Preço derreteu (Slippage) | Ticket: ", ticket, " | Lucro atual: ", current_profit);
      SendTCP("RESULT|CLOSE|ERROR|SLIPPAGE_PROTECTION\n");
      return;
     }

   MqlTradeRequest request;
   MqlTradeResult  result;
   ZeroMemory(request);
   ZeroMemory(result);

   request.action   = TRADE_ACTION_DEAL;
   request.position = ticket;
   request.symbol   = symbol;
   request.volume   = lot;
   request.type     = (type == POSITION_TYPE_BUY) ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
   
   MqlTick last_tick;
   SymbolInfoTick(symbol, last_tick);
   request.price    = (type == POSITION_TYPE_BUY) ? last_tick.bid : last_tick.ask;

   request.deviation= InpSlippage;
   request.magic    = InpMagicNumber;
   request.type_filling = ORDER_FILLING_IOC;
   request.comment  = "ASI_FAST_CLOSE";
   
   Print("⚡ ASI FAST CLOSE: ", ticket, " | Profit: ", DoubleToString(current_profit, 2));

   bool success = OrderSend(request, result);
   if(success)
     {
      string msg = "RESULT|CLOSE|SUCCESS|" + IntegerToString(result.deal) + "|" + DoubleToString(result.price, _Digits) + "\n";
      SendTCP(msg);
      Print("✅ CLOSE DEFERIDO: ", result.deal, " @ ", result.price);
     }
   else
     {
      string msg = "RESULT|CLOSE|ERROR|" + IntegerToString(result.retcode) + "\n";
      SendTCP(msg);
      Print("❌ CLOSE REJEITADO: CÓDIGO ", result.retcode);
     }
  }
//+------------------------------------------------------------------+
