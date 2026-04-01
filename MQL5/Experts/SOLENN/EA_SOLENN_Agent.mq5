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
input string    InpHost     = "127.0.0.1"; // Matrix Host
input int       InpPort     = 9888;        // Matrix Port (Ω-9888)
input int       InpRes      = 1000;        // Heartbeat (ms) refresh ms

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
        // [Ω-V5.5.3] Active Pulse (1Hz)
        if(!hftp_client.Heartbeat()) {
            Print("☢️ [Ω-HFT] Pulse LOST. Heartbeat fail.");
        }
        sensors.StreamAccountSnapshot();
        
        // 2. [Ω-V5.5.4] Process ALL Commands in Buffer (Streaming Mode)
        if(hftp_client.Readable()) {
            uchar buf[];
            ArrayResize(buf, 4096);
            int read = hftp_client.Receive(buf);
            if(read > 0) {
                hftp_client.UnpackData(buf, read);
                
                // Process multiple MsgPack objects in the same read buffer
                while(hftp_client.GetPacker().Remaining() > 0) {
                    int members = hftp_client.GetPacker().UnpackMapHeader();
                    if(members <= 0) break;
                    
                    string type = "";
                    string action = "";
                    
                    for(int i=0; i<members; i++) {
                        string key = hftp_client.GetPacker().ReadString();
                        if(key == "type") type = hftp_client.GetPacker().ReadString();
                        else if(key == "action") action = hftp_client.GetPacker().ReadString();
                        else {
                            uchar t = hftp_client.GetPacker().GetType();
                            if(t == 0xCF) hftp_client.GetPacker().ReadInt();
                            else if(t == 0xCB) hftp_client.GetPacker().ReadDouble();
                            else hftp_client.GetPacker().ReadString();
                        }
                    }
    
                    if(type == "ORDER") {
                        Alert("🔥 [Ω-SOLENN] ORDER SIGNAL: ", action);
                        if(action == "BUY") oms.Execute("TEST_B", _Symbol, ORDER_TYPE_BUY, 0.01, 0, 0);
                        else if(action == "SELL") oms.Execute("TEST_S", _Symbol, ORDER_TYPE_SELL, 0.01, 0, 0);
                    }
                    
                    // Check if we reached the end of the current read
                    if(hftp_client.GetPacker().Remaining() <= 0) break;
                }
            }
        }
    }
}
