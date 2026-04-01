/*
╔══════════════════════════════════════════════════════════════════════════════╗
║              SOLÉNN — HFTP CLIENT Ω (SOVEREIGN PORTAL)                       ║
║     Socket Communication & Heartbeat Synchronization for MQL5                ║
║     Implementing: Non-blocking WinAPI-Grade Sockets (Ω-21)                   ║
║     Framework 3-6-9: Phase 5(Ω-21) - Concept 1.2 (C++)                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
*/

#property copyright "SOLÉNN Ω - Sovereign Capital"
#property strict

#include <SOLENN\HFTP_Protocol.mqh>

class CHFTPClient {
private:
    int m_socket;
    string m_host;
    int m_port;
    bool m_is_connected;
    CMsgPack m_packer;

public:
    CHFTPClient(string host="127.0.0.1", int port=5555) {
        m_host = host; m_port = port; m_socket = INVALID_HANDLE; m_is_connected = false;
    }

    ~CHFTPClient() { Disconnect(); }

    bool Connect() {
        if(m_is_connected) return true;
        m_socket = SocketCreate();
        if(m_socket == INVALID_HANDLE) {
            Print("☢️ [Ω-HFT] Socket Create FAIL: ", GetLastError());
            return false;
        }

        if(!SocketConnect(m_socket, m_host, m_port, 1000)) {
            Print("☣️ [Ω-HFT] Socket Connect FAIL: ", GetLastError());
            SocketClose(m_socket);
            return false;
        }

        m_is_connected = true;
        // [Ω-V5.2.1] Hello Handshake
        SendPacket("HELLO", "MQL5_AGENT_V2");
        return true;
    }

    void Disconnect() {
        if(m_socket != INVALID_HANDLE) {
            SocketClose(m_socket);
            m_socket = INVALID_HANDLE;
            m_is_connected = false;
        }
    }

    // [Ω-V5.2.3] High Performance Sender
    bool SendBuffer(uchar &data[]) {
        if(!m_is_connected) return false;
        int sent = SocketSend(m_socket, data, ArraySize(data));
        return (sent > 0);
    }

    // [Ω-V5.2.4] Packet Helper (Type-Safe Command)
    void SendPacket(string cmd, string payload) {
        m_packer.Clear();
        m_packer.PackMapHeader(2);
        m_packer.PackString("type");
        m_packer.PackString(cmd);
        m_packer.PackString("payload");
        m_packer.PackString(payload);
        
        uchar buf[];
        m_packer.GetData(buf);
        SendBuffer(buf);
    }

    void Heartbeat() {
        if(m_is_connected) SendPacket("PONG", IntegerToString((int)TimeCurrent()));
    }

    bool Readable() { return SocketIsReadable(m_socket); }
    int  Receive(uchar &data[]) { return SocketRead(m_socket, data, 4096, 0); }
    bool IsConnected() { return m_is_connected; }
};
