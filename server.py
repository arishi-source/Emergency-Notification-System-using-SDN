#!/usr/bin/env python3
import socket, threading, time, argparse, statistics

ap = argparse.ArgumentParser()
ap.add_argument('--port', type=int, default=5000)
ap.add_argument('--count', type=int, default=0, help='auto-send N alerts (0 = interactive)')
ap.add_argument('--interval', type=float, default=0.1)
ap.add_argument('--wait', type=float, default=5, help='seconds to wait for subscribers')
ap.add_argument('--timeout', type=float, default=0.3, help='retransmit timeout')
ap.add_argument('--retries', type=int, default=3, help='0 = no retransmit (raw loss)')
ap.add_argument('--label', default='run')
args = ap.parse_args()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0xB8)   # DSCP 46 (EF) = emergency
sock.bind(('0.0.0.0', args.port))

subs, pending, lat = set(), {}, []
sent = acked = first_ok = retx = 0
lock = threading.Lock()


def rx():
    global acked, first_ok
    while True:
        data, addr = sock.recvfrom(2048)
        parts = data.decode(errors='ignore').split('|')
        if parts[0] == 'REGISTER':
            with lock:
                subs.add(addr)
            sock.sendto(b'REG_OK', addr)
            print(f'[+] subscriber registered: {addr}')
        elif parts[0] == 'UNREGISTER':
            with lock:
                subs.discard(addr)
        elif parts[0] == 'ACK':
            with lock:
                p = pending.pop((int(parts[1]), addr), None)
                if p:
                    acked += 1
                    lat.append((time.time() - p['first']) * 1000)
                    if p['tries'] == 1:
                        first_ok += 1


def retransmit():
    global retx
    while True:
        time.sleep(0.05)
        now = time.time()
        with lock:
            for key, p in list(pending.items()):
                if now - p['last'] > args.timeout:
                    if p['tries'] > args.retries:
                        del pending[key]            # gave up -> lost
                    else:
                        sock.sendto(p['msg'], key[1])
                        p['tries'] += 1
                        p['last'] = now
                        retx += 1


def send_alert(seq, text):
    global sent
    ts = time.time()
    msg = f'ALERT|{seq}|{ts}|{text}'.encode()
    with lock:
        targets = list(subs)
        for a in targets:
            pending[(seq, a)] = {'msg': msg, 'first': ts, 'last': ts, 'tries': 1}
            sent += 1
    for a in targets:
        sock.sendto(msg, a)
    return len(targets)


threading.Thread(target=rx, daemon=True).start()
threading.Thread(target=retransmit, daemon=True).start()
print(f'Emergency server on UDP {args.port}. Waiting for subscribers...')

if args.count:
    time.sleep(args.wait)
    print(f'Sending {args.count} alerts to {len(subs)} subscribers')
    for i in range(args.count):
        send_alert(i, 'EMERGENCY: evacuate building')
        time.sleep(args.interval)
    time.sleep(args.timeout * (args.retries + 2))
    lost_first = 100 * (sent - first_ok) / max(sent, 1)
    lost_final = 100 * (sent - acked) / max(sent, 1)
    print('\n===== RESULTS [%s] =====' % args.label)
    print(f'sent={sent} acked={acked} retransmissions={retx}')
    print(f'packet loss (first transmission): {lost_first:.1f}%')
    print(f'undelivered after retries:        {lost_final:.1f}%')
    if lat:
        lat.sort()
        print(f'latency ms: avg={statistics.mean(lat):.1f} '
              f'p95={lat[int(0.95 * len(lat)) - 1]:.1f} max={lat[-1]:.1f}')
    with open('results.csv', 'a') as f:
        f.write(f'{args.label},{sent},{acked},{retx},{lost_first:.1f},{lost_final:.1f},'
                f'{statistics.mean(lat) if lat else 0:.1f}\n')
else:
    seq = 0
    while True:
        text = input('alert> ')
        n = send_alert(seq, text)
        print(f'sent alert #{seq} to {n} subscribers')
        seq += 1
