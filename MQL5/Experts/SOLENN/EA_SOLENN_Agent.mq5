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
input int      InpPort = 5555;
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
    // 1. Connection Check & Sync
    if(!hftp_client.IsConnected()) {
        hftp_client.Connect();
    } else {
        hftp_client.Heartbeat();
        sensors.StreamAccountSnapshot();
        
        // 2. [Ω-V5.5.3] Process Commands from SOLÉNN Brain (Python)
        if(hftp_client.Readable()) {
            uchar buf[];
            int read = hftp_client.Receive(buf);
            if(read > 0) {
                // Simplified command parsing [Ω-V5.5.4]
                // Look for "ORDER" keyword in binary stream
                string msg = CharArrayToString(buf, 0, read, CP_UTF8);
                if(StringFind(msg, "ORDER") >= 0) {
                     // In real PhD scenario, use full binary unpacker. 
                     // For Phase 5 activation, we use fast-tagging.
                     Print("📈 [Ω-EA] Received ORDER command from Brain.");
                     // Trigger dummy order for now or parse real params
                }
            }
        }
    }
}
