/*
╔══════════════════════════════════════════════════════════════════════════════╗
║              SOLÉNN — ORDER EXECUTOR Ω (SOVEREIGN OMS)                       ║
║     MetaTrader 5 Native Execution & Trade Feedback Loop                      ║
║     Implementing: Atomic Order Execution & Trace-to-Ticket Sync              ║
║     Framework 3-6-9: Phase 5(Ω-21) - Concept 1.4 (C++)                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
*/

#property copyright "SOLÉNN Ω - Sovereign Capital"
#property strict

#include <Trade\Trade.mqh>
#include <SOLENN\HFTP_Client.mqh>

class COrderExecutor {
private:
    CTrade        m_trade;
    CHFTPClient  *m_client;
    CMsgPack      m_packer;

public:
    COrderExecutor(CHFTPClient *client) {
        m_client = client; m_trade.SetExpertMagicNumber(777); 
        m_trade.SetAsyncMode(false); // Synchronous for precise acknowledgment
    }

    // [Ω-V5.4.1] Order Execution logic from MasterBridge command
    bool Execute(string trace_id, string symbol, int action, double lot, double sl, double tp) {
        if(!m_client.IsConnected()) return false;
        bool res = false;

        if(action == ORDER_TYPE_BUY) res = m_trade.Buy(lot, symbol, 0, sl, tp, trace_id);
        else if(action == ORDER_TYPE_SELL) res = m_trade.Sell(lot, symbol, 0, sl, tp, trace_id);

        uint res_code = m_trade.ResultRetcode();
        ulong ticket = m_trade.ResultOrder();
        
        // [Ω-V5.4.3] Instant Feedback to OMSEngine
        m_packer.Clear();
        m_packer.PackMapHeader(6);
        m_packer.PackString("type");     m_packer.PackString("ORDER_ACK");
        m_packer.PackString("trace_id"); m_packer.PackString(trace_id);
        m_packer.PackString("ticket");   m_packer.PackInt(ticket);
        m_packer.PackString("success");  m_packer.PackString(res ? "TRUE" : "FALSE");
        m_packer.PackString("error");    m_packer.PackInt(res_code);
        m_packer.PackString("time");     m_packer.PackInt(TimeLocal());
        
        uchar buf[];
        m_packer.GetData(buf);
        m_client.SendBuffer(buf);
        return res;
    }
};
