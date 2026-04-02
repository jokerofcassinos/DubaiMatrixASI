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
    bool m_is_connecting;
    bool m_handshaked;
    CMsgPack *m_packer;

public:
    CHFTPClient(string host, int port) { 
        m_host = host; m_port = port; m_socket = INVALID_HANDLE; 
        m_is_connected = false; m_is_connecting = false; m_handshaked = false; 
        m_packer = new CMsgPack();
    }
    void UnpackData(uchar &data[], int len) { m_packer.SetData(data, len); }
    CMsgPack* GetPacker() { return m_packer; }

    ~CHFTPClient() { Disconnect(); delete m_packer; }

    bool IsConnected() { return m_handshaked; }

    bool Connect() {
        if(m_is_connected || m_is_connecting) return true;
        m_is_connecting = true;
        
        Print("📡 [Ω-HFT] Contacting Matrix... ", m_host, ":", m_port);
        m_socket = SocketCreate();
        if(m_socket == INVALID_HANDLE) { m_is_connecting = false; return false; }
        
        bool connected = SocketConnect(m_socket, m_host, m_port, 5000);
        if(!connected) {
            Print("⚠️ [Ω-HFT] SocketConnect Timeout. Port: ", m_port);
            SocketClose(m_socket);
            m_is_connecting = false;
            return false;
        }
        
        // [Ω-V5.2.1] Hello Handshake (Pure Binary Mode)
        SendPacket("HELLO", "MQL5_AGENT_V2", "SOLENN_OMEGA_SECURE");
        Print("📤 [Ω-HFT] Hello Handshake Dispatched.");
        
        // [Ω-V5.2.2] Wait for WELCOME ACK (v2.8)
        uchar buf[];
        ArrayResize(buf, 1024);
         uint start = GetTickCount();
         while(GetTickCount() - start < 5000) {
              uint readable = SocketIsReadable(m_socket);
              if(readable > 0) {
                  int read = SocketRead(m_socket, buf, readable, 0);
                  if(read > 0) {
                      m_packer.SetData(buf, read);
                      int members = m_packer.UnpackMapHeader();
                      Print("📩 [Ω-HFT] Bytes: ", read, ", Map: ", members, " (Type: 0x", StringFormat("%02X", buf[0]), ")");
                      
                      for(int i=0; i<members; i++) {
                          if(m_packer.Remaining() <= 0) break;
                          string key = m_packer.ReadString();
                          uchar next_type = m_packer.GetType();
                          string val = "";
                          
                          // Robust parsing to avoid offset corruption
                          if((next_type >= 0xA0 && next_type <= 0xBF) || next_type == 0xD9 || next_type == 0xDA || next_type == 0xDB) {
                              val = m_packer.ReadString();
                          } else {
                              // Skip non-string values to maintain alignment
                              if(next_type == 0xCF) m_packer.ReadInt();
                              else if(next_type == 0xCB) m_packer.ReadDouble();
                              else m_packer.ReadString(); // At least try to skip 1 byte
                          }
                          
                          Print("   [Ω-DECODE] Index: ", i, " Key: ", key, " Val: ", val, " (NextType: 0x", StringFormat("%02X", next_type), ")");
                          
                          if(key == "type" && val == "WELCOME") {
                              m_handshaked = true;
                              m_is_connected = true;
                              m_is_connecting = false;
                              Print("💎 [Ω-SYNC] HFTP-P Handshake SECURED.");
                              return true;
                          }
                      }
                  } else if(read < 0) {
                      Print("☢️ [Ω-HFT] SocketRead Error: ", GetLastError());
                  }
              } else {
                 // Removido o cancelamento prematuro por _LastError vazado. Em vez disso,
                 // ResetLastError ou apenas espera (Sleep(200)).
                 ResetLastError();
             }
             Sleep(200);
         }
        
        Print("☢️ [Ω-HFT] Handshake ACK TIMEOUT. Protocol failure.");
        Disconnect();
        return false;
    }

    void Disconnect() {
        if(m_socket != INVALID_HANDLE) {
            SocketClose(m_socket);
            m_socket = INVALID_HANDLE;
        }
        m_is_connected = false;
        m_is_connecting = false;
        m_handshaked = false;
    }

    // [Ω-V5.2.3] High Performance Sender
    bool SendBuffer(uchar &data[]) {
        if(!m_is_connected) return false;
        int sent = SocketSend(m_socket, data, ArraySize(data));
        return (sent > 0);
    }
    
    bool SendRaw(string msg) {
        uchar buf[];
        StringToCharArray(msg, buf, 0, StringLen(msg), CP_UTF8);
        return SendBuffer(buf);
    }

    // [Ω-V5.2.4] Packet Helper (Type-Safe Command)
    bool SendPacket(string type, string payload="", string token="") {
        if(m_socket == INVALID_HANDLE) return false;
        
        m_packer.Clear();
        int fields = (token == "") ? 2 : 3;
        m_packer.PackMapHeader(fields);
        m_packer.PackString("type");
        m_packer.PackString(type);
        
        if(token != "") {
            m_packer.PackString("token");
            m_packer.PackString(token);
        }
        
        m_packer.PackString("payload");
        m_packer.PackString(payload);
        
        uchar buf[];
        m_packer.GetData(buf);
        int len = m_packer.Size();
        
        if(len > 0) {
            uint sent = SocketSend(m_socket, buf, len);
            if(sent > 0) return true;
            Print("☢️ [Ω-HFT] SocketSend FAILED. Error: ", GetLastError());
        }
        return false;
    }

    bool Heartbeat() {
        if(!m_handshaked) return false;
        return SendPacket("HEARTBEAT", DoubleToString(TimeCurrent(), 0));
    }

    bool Readable() { 
        if(!m_is_connected) return false;
        return (SocketIsReadable(m_socket) != 0); 
    }
    int Receive(uchar &data[]) { 
        uint readable = SocketIsReadable(m_socket);
        if (readable == 0) return 0;
        return SocketRead(m_socket, data, readable, 0); 
    }
};
