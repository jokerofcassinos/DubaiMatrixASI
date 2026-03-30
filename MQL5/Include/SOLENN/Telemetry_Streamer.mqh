/*
╔══════════════════════════════════════════════════════════════════════════════╗
║              SOLÉNN — TELEMETRY STREAMER Ω (CORTEX INPUT)                    ║
║     Real-time Sensory Data Streaming (Tick, Book, Account)                    ║
║     Implementing: High Resolution Tick Capture (Law III.3)                   ║
║     Framework 3-6-9: Phase 5(Ω-21) - Concept 1.3 (C++)                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
*/

#property copyright "SOLÉNN Ω - Sovereign Capital"
#property strict

#include <SOLENN\HFTP_Client.mqh>

class CTelemetryStreamer {
private:
    CHFTPClient *m_client;
    CMsgPack     m_packer;
    string       m_symbol;
    long         m_last_seq;

public:
    CTelemetryStreamer(CHFTPClient *client, string symbol) {
        m_client = client; m_symbol = symbol; m_last_seq = 0;
    }

    // [Ω-V5.3.1] Tick Binary Transmission (Law III.3)
    void StreamTick(MqlTick &tick) {
        if(!m_client.IsConnected()) return;
        m_packer.Clear();
        m_packer.PackMapHeader(7);
        m_packer.PackString("type");  m_packer.PackString("TICK");
        m_packer.PackString("symbol");m_packer.PackString(m_symbol);
        m_packer.PackString("bid");   m_packer.PackDouble(tick.bid);
        m_packer.PackString("ask");   m_packer.PackDouble(tick.ask);
        m_packer.PackString("last");  m_packer.PackDouble(tick.last);
        m_packer.PackString("vol");   m_packer.PackInt(tick.volume);
        m_packer.PackString("time_msc");m_packer.PackInt(tick.time_msc);
        
        uchar buf[];
        m_packer.GetData(buf);
        m_client.SendBuffer(buf);
    }

    // [Ω-V5.3.4] Account Vital Metrics (Margin, Equity)
    void StreamAccountSnapshot() {
        if(!m_client.IsConnected()) return;
        m_packer.Clear();
        m_packer.PackMapHeader(7);
        m_packer.PackString("type");    m_packer.PackString("ACCOUNT");
        m_packer.PackString("balance"); m_packer.PackDouble(AccountInfoDouble(ACCOUNT_BALANCE));
        m_packer.PackString("equity");  m_packer.PackDouble(AccountInfoDouble(ACCOUNT_EQUITY));
        m_packer.PackString("margin");  m_packer.PackDouble(AccountInfoDouble(ACCOUNT_MARGIN));
        m_packer.PackString("free");    m_packer.PackDouble(AccountInfoDouble(ACCOUNT_MARGIN_FREE));
        m_packer.PackString("leverage");m_packer.PackInt(AccountInfoInteger(ACCOUNT_LEVERAGE));
        m_packer.PackString("profit");  m_packer.PackDouble(AccountInfoDouble(ACCOUNT_PROFIT));

        uchar buf[];
        m_packer.GetData(buf);
        m_client.SendBuffer(buf);
    }
};
