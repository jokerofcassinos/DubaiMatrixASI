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
    uchar buffer[];
    int offset;

public:
    CMsgPack() { offset = 0; ArrayResize(buffer, 0, 1024); }
    void Clear() { offset = 0; ArrayResize(buffer, 0); }
    int  Size() { return offset; }
    void GetData(uchar &out_buf[]) { ArrayCopy(out_buf, buffer, 0, 0, offset); }

    // [Ω-V5.1.2] Packing Logic (Big-Endian per MsgPack spec)
    void PackInt(long val) {
        ArrayResize(buffer, offset + 9);
        buffer[offset++] = (uchar)MP_TYPE_INT;
        for(int i=7; i>=0; i--) buffer[offset++] = (uchar)(val >> (i*8));
    }

    void PackDouble(double val) {
        ArrayResize(buffer, offset + 9);
        buffer[offset++] = (uchar)MP_TYPE_DOUBLE;
        DoubleToBytes convert;
        convert.val = val;
        for(int i=7; i>=0; i--) buffer[offset++] = convert.bytes[i]; // Reverse for BE
    }

    void PackString(string val) {
        uchar str_bytes[];
        int len = StringToCharArray(val, str_bytes, 0, -1, CP_UTF8) - 1; // Null char removed
        ArrayResize(buffer, offset + 5 + len);
        buffer[offset++] = (uchar)MP_TYPE_STRING;
        // 4 bytes length (BE)
        for(int i=3; i>=0; i--) buffer[offset++] = (uchar)(len >> (i*8));
        ArrayCopy(buffer, str_bytes, offset, 0, len);
        offset += len;
    }

    // [Ω-V5.1.3] Map Header (Simplified for N members)
    void PackMapHeader(int members) {
        ArrayResize(buffer, offset + 5);
        buffer[offset++] = (uchar)MP_TYPE_MAP;
        for(int i=3; i>=0; i--) buffer[offset++] = (uchar)(members >> (i*8));
    }
};
