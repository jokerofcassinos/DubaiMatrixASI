import socket
import msgpack
import time

def test_connection():
    host = "127.0.0.1"
    port = 9999
    print(f"📡 Tentando conexão de teste em {host}:{port}...")
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((host, port))
        print("✅ Conexão TCP estabelecida.")
        
        # Enviar Handshake
        handshake = {"type": "HELLO", "payload": "PYTHON_TEST_AGENT"}
        s.sendall(msgpack.packb(handshake))
        print("📩 Handshake HELLO enviado.")
        
        # Receber ACK
        data = s.recv(1024)
        if data:
            resp = msgpack.unpackb(data)
            print(f"🚀 Resposta do Servidor: {resp}")
            if resp.get("status") == "AUTHORIZED":
                print("💎 CONEXÃO HFT-P VALIDADA COM SUCESSO!")
        
        s.close()
    except Exception as e:
        print(f"❌ Falha no teste: {e}")

if __name__ == "__main__":
    test_connection()
