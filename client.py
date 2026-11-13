import websocket
import threading
import sys

# غير هالرابط بالرابط اللي طلعلك من Render
# لازم تبدل https بـ wss
SERVER_URL = "wss://teagdi.onrender.com/ws"

def on_message(ws, message):
    print(message, end='', flush=True)

def on_error(ws, error):
    print(f"\n[-] Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("\n[*] Connection closed.")
    sys.exit(0)

def on_open(ws):
    def run():
        while True:
            try:
                msg = input()
                if msg:
                    ws.send(msg)
            except:
                break
    threading.Thread(target=run, daemon=True).start()

if __name__ == "__main__":
    print(f"[*] Connecting to {SERVER_URL}...")
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(SERVER_URL,
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
    ws.run_forever()