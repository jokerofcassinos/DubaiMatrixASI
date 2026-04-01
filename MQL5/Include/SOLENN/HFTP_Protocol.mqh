/*
╔══════════════════════════════════════════════════════════════════════════════╗
║              SOLÉNN — HFTP PROTOCOL Ω (BINARY SERIALIZER)                    ║
║     MessagePack (Simplified) Encoder & Decoder for MQL5                      ║
║     Implementing: High Performance Binary Packing, Zero-GC Allocation        ║
║     Framework 3-6-9: Phase 5(Ω-21) - Concept 1.1 (C++)                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
*/

#property copyright "SOLÉNN Ω - Sovereign Capital"
#property link      "https://solenn.ai"
#property version   "2.00"
#property strict

#include <Arrays\ArrayObj.mqh>

// [Ω-V5.1.1] Binary Type Identifiers (MessagePack-like)
enum ENUM_MSGPACK_TYPE {
    MP_TYPE_INT      = 0xCF, // uint64
    MP_TYPE_DOUBLE   = 0xCB, // float64
    MP_TYPE_STRING   = 0xDB, // string32
    MP_TYPE_MAP      = 0xDF, // map32
    MP_TYPE_TRUE     = 0xC3,
    MP_TYPE_FALSE    = 0xC2,
    MP_TYPE_NULL     = 0xC0
};

union DoubleToBytes {
    double val;
    uchar  bytes[8];
};

class CMsgPack {
private:
    uchar m_buf[];
    int m_pos;   // Current R/W pointer
    int m_total; // Effective size of data in buffer

public:
    CMsgPack() { m_pos = 0; m_total = 0; ::ArrayResize(m_buf, 0, 4096); }
    void Clear() { m_pos = 0; m_total = 0; ::ArrayResize(m_buf, 0); }
    
    int  Pos()   { return m_pos; }
    int  Size()  { return m_total; }
    int  Remaining() { return m_total - m_pos; }

    void GetData(uchar &out_buf[]) { 
        ::ArrayResize(out_buf, m_total);
        ::ArrayCopy(out_buf, m_buf, 0, 0, m_total); 
    }
    
    void SetData(uchar &in_buf[], int len=-1) { 
        int bytes = (len == -1) ? ::ArraySize(in_buf) : len;
        ::ArrayResize(m_buf, bytes);
        ::ArrayCopy(m_buf, in_buf, 0, 0, bytes); 
        m_pos = 0; 
        m_total = bytes; 
    }

    // [Ω-V5.1.4] Decoding Logic (Big-Endian)
    uchar GetType() { if(m_pos >= m_total) return 0; return m_buf[m_pos]; }
    
    long ReadInt() {
        if(m_pos + 9 > m_total) return 0;
        if(m_buf[m_pos++] != MP_TYPE_INT) return 0;
        long val = 0;
        for(int i=7; i>=0; i--) val |= ((long)m_buf[m_pos++] << (i*8));
        return val;
    }

    double ReadDouble() {
        if(m_pos + 9 > m_total) return 0.0;
        if(m_buf[m_pos++] != MP_TYPE_DOUBLE) return 0.0;
        DoubleToBytes conv;
        ZeroMemory(conv);
        for(int i=7; i>=0; i--) conv.bytes[i] = m_buf[m_pos++];
        return conv.val;
    }

    string ReadString() {
        if(m_pos >= m_total) return "";
        uchar type = m_buf[m_pos++];
        int len = 0;
        if(type >= 0xA0 && type <= 0xBF) {
            len = type - 0xA0;
        } else if(type == 0xD9) { // Str8
            len = m_buf[m_pos++];
        } else if(type == 0xDA) { // Str16
            if(m_pos + 2 > m_total) return "";
            len = (m_buf[m_pos++] << 8) | m_buf[m_pos++];
        } else if(type == MP_TYPE_STRING || type == 0xDB) { // Str32
            if(m_pos + 4 > m_total) return "";
            for(int i=3; i>=0; i--) len |= (m_buf[m_pos++] << (i*8));
        } else return "";
        
        if(len <= 0 || m_pos + len > m_total) return "";
        string val = CharArrayToString(m_buf, m_pos, len, CP_UTF8);
        m_pos += len;
        return val;
    }

    int UnpackMapHeader() {
        if(m_pos >= m_total) return 0;
        uchar type = m_buf[m_pos++];
        if(type >= 0x80 && type <= 0x8F) return (type - 0x80);
        if(type == 0xDE) {
            if(m_pos + 2 > m_total) return 0;
            int members = 0;
            for(int i=1; i>=0; i--) members |= (m_buf[m_pos++] << (i*8));
            return members;
        }
        if(type == 0xDF) {
            if(m_pos + 4 > m_total) return 0;
            int members = 0;
            for(int i=3; i>=0; i--) members |= (m_buf[m_pos++] << (i*8));
            return members;
        }
        return 0;
    }

    void PackInt(long val) {
        ::ArrayResize(m_buf, m_pos + 9);
        m_buf[m_pos++] = (uchar)MP_TYPE_INT;
        for(int i=7; i>=0; i--) m_buf[m_pos++] = (uchar)(val >> (i*8));
        if(m_pos > m_total) m_total = m_pos;
    }

    void PackDouble(double val) {
        ::ArrayResize(m_buf, m_pos + 9);
        m_buf[m_pos++] = (uchar)MP_TYPE_DOUBLE;
        DoubleToBytes conv;
        conv.val = val;
        for(int i=7; i>=0; i--) m_buf[m_pos++] = conv.bytes[i];
        if(m_pos > m_total) m_total = m_pos;
    }

    void PackString(string val) {
        uchar str_bytes[];
        int len = StringToCharArray(val, str_bytes, 0, -1, CP_UTF8) - 1;
        if(len < 32) {
            ::ArrayResize(m_buf, m_pos + 1 + len);
            m_buf[m_pos++] = (uchar)(0xA0 | len);
        } else {
            ::ArrayResize(m_buf, m_pos + 5 + len);
            m_buf[m_pos++] = (uchar)MP_TYPE_STRING;
            for(int i=3; i>=0; i--) m_buf[m_pos++] = (uchar)(len >> (i*8));
        }
        ArrayCopy(m_buf, str_bytes, m_pos, 0, len);
        m_pos += len;
        if(m_pos > m_total) m_total = m_pos;
    }

    void PackMapHeader(int members) {
        ::ArrayResize(m_buf, m_pos + 5);
        m_buf[m_pos++] = (uchar)MP_TYPE_MAP;
        for(int i=3; i>=0; i--) m_buf[m_pos++] = (uchar)(members >> (i*8));
        if(m_pos > m_total) m_total = m_pos;
    }
};
