/*
╔══════════════════════════════════════════════════════════════════════════════╗
║              SOLÉNN — EXPERT ADVISOR AGENT Ω (PERCEPTION-ACTION)             ║
║     The Sovereign Inhabitant of the MetaTrader 5 Terminal                    ║
║     Implementing: Sensory Streaming, Atomic Execution, Pulse Sync            ║
║     Framework 3-6-9: Phase 5(Ω-21) - Sovereign EA Agent                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
*/

#property copyright "SOLÉNN Ω - Sovereign Capital"
#property link      "https://solenn.ai"
#property version   "2.00"
#property strict

#include <SOLENN\HFTP_Client.mqh>
#include <SOLENN\Telemetry_Streamer.mqh>
#include <SOLENN\Order_Executor.mqh>

// [Ω-V5.5.0] Parameters
input string   InpHost = "127.0.0.1";
input int      InpPort = 9999;
input int      InpRes  = 1000; // Telegram refresh ms

CHFTPClient       *hftp_client;
CTelemetryStreamer *sensors;
COrderExecutor     *oms;

int OnInit() {
    Print("💎 [Ω-EA] Initializing SOLÉNN Agent Ω...");
    
    hftp_client = new CHFTPClient(InpHost, InpPort);
    sensors     = new CTelemetryStreamer(hftp_client, Symbol());
    oms         = new COrderExecutor(hftp_client);
    
    EventSetMillisecondTimer(InpRes);
    return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason) {
    Print("🛑 [Ω-EA] Shutting down Agent Ω...");
    delete hftp_client;
    delete sensors;
    delete oms;
    EventKillTimer();
}

void OnTick() {
    MqlTick last_tick;
    if(SymbolInfoTick(Symbol(), last_tick)) {
        sensors.StreamTick(last_tick);
    }
}

void OnTimer() {
    // 1. [Ω-V5.5.2] Automatic Connection Persistence
    if(!hftp_client.IsConnected()) {
        static uint last_recon = 0;
        if(GetTickCount() - last_recon > 3000) {
            if(hftp_client.Connect()) {
               Alert("✅ [Ω-SYNC] HFTP-P Matrix Active.");
            }
            last_recon = GetTickCount();
        }
    } else {
        hftp_client.Heartbeat();
        sensors.StreamAccountSnapshot();
        
        // 2. [Ω-V5.5.3] Process Commands from SOLÉNN Brain (Python)
        if(hftp_client.Readable()) {
            uchar buf[];
            ArrayResize(buf, 4096);
            int read = hftp_client.Receive(buf);
            if(read > 0) {
                string raw = CharArrayToString(buf, 0, read, CP_UTF8);
                Print("📥 [Ω-HFTP-P] Packet Received: ", read, " bytes. Content: ", raw);
                
                if(StringFind(raw, "ORDER") >= 0) {
                    Alert("🔥 [Ω-SOLENN] ORDER SIGNAL DETECTED!");
                    Print("📈 [Ω-EA] FOUND Signature: ORDER. Action scan...");
                    
                    if(StringFind(raw, "BUY") >= 0) {
                        Alert("🚀 [Ω-EXECUTION] ATTEMPTING BUY 0.01 BTCUSD");
                        if(CheckPointer(oms) != POINTER_INVALID)
                            oms.Execute("TEST_B_"+IntegerToString(TimeLocal()), _Symbol, ORDER_TYPE_BUY, 0.01, 0, 0);
                        else
                            Print("☢️ [Ω-ERROR] OrderExecutor (oms) is NULL!");
                    } else if(StringFind(raw, "SELL") >= 0) {
                        if(CheckPointer(oms) != POINTER_INVALID)
                            oms.Execute("TEST_S_"+IntegerToString(TimeLocal()), _Symbol, ORDER_TYPE_SELL, 0.01, 0, 0);
                    }
                }
            }
        }
    }
}
