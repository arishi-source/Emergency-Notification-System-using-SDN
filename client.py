#!/usr/bin/env python3
import socket, argparse, time

ap = argparse.ArgumentParser()
ap.add_argument('--server', required=True)
ap.add_argument('--sport', type=int, default=5000)
ap.add_argument('--port', type=int, default=9999)
args = ap.parse_args()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', args.port))
sock.settimeout(1)
srv = (args.server, args.sport)

# register (retry until server confirms, UDP can lose packets)
while True:
    sock.sendto(b'REGISTER', srv)
    try:
        d, _ = sock.recvfrom(2048)
        if d == b'REG_OK':
            break
    except socket.timeout:
        print('retrying registration...')
print('Registered. Waiting for emergency alerts (Ctrl-C to quit)')

seen, lats = set(), []
try:
    while True:
        try:
            data, _ = sock.recvfrom(2048)
        except socket.timeout:
            continue
        p = data.decode(errors='ignore').split('|', 3)
        if p[0] != 'ALERT':
            continue
        seq, ts, text = int(p[1]), float(p[2]), p[3]
        sock.sendto(f'ACK|{seq}'.encode(), srv)      # always ack (even duplicates)
        if seq in seen:
            continue
        seen.add(seq)
        lats.append((time.time() - ts) * 1000)
        print(f'ALERT #{seq}: {text}  ({lats[-1]:.1f} ms)')
except KeyboardInterrupt:
    sock.sendto(b'UNREGISTER', srv)
    if lats:
        print(f'\nreceived {len(seen)} unique alerts, avg latency {sum(lats)/len(lats):.1f} ms')
