
#!/usr/bin/env python3

import socket
import threading
import time
import argparse
import statistics
import math

ap = argparse.ArgumentParser()
ap.add_argument('--port', type=int, default=5000)
ap.add_argument('--interval', type=float, default=0.2)
ap.add_argument('--timeout', type=float, default=0.3)
ap.add_argument('--retries', type=int, default=3)
ap.add_argument('--label', default='run')
args = ap.parse_args()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0xB8)
sock.bind(('0.0.0.0', args.port))

subs = set()
pending = {}

lock = threading.Lock()

sent = 0
acked = 0
first_ok = 0
retx = 0

seq = 0
batch_no = 0


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

            print(f'[-] subscriber unregistered: {addr}')

        elif parts[0] == 'ACK':
            with lock:
                p = pending.pop((int(parts[1]), addr), None)

                if p:
                    acked += 1
                    p['latency'] = (time.time() - p['first']) * 1000
                    p['acked'] = True

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
                        del pending[key]

                    else:
                        sock.sendto(p['msg'], key[1])
                        p['tries'] += 1
                        p['last'] = now
                        retx += 1


def send_alert(number):
    global sent

    ts = time.time()

    msg = (
        f'ALERT|{number}|{ts}|'
        'EMERGENCY: evacuate building'
    ).encode()

    with lock:
        targets = list(subs)

        for addr in targets:
            pending[(number, addr)] = {
                'msg': msg,
                'first': ts,
                'last': ts,
                'tries': 1
            }

            sent += 1

    for addr in targets:
        sock.sendto(msg, addr)


def run_batch(count):
    global seq, batch_no

    with lock:
        if not subs:
            print('No subscribers registered. Start h2 and h3 first.')
            return

        subscriber_count = len(subs)

        start_sent = sent
        start_acked = acked
        start_first = first_ok
        start_retx = retx

    start_seq = seq

    print(f'\nSending {count} alerts to {subscriber_count} subscribers...')

    for i in range(count):
        send_alert(seq)
        seq += 1
        time.sleep(args.interval)

    end_seq = seq

    deadline = time.time() + args.timeout * (args.retries + 2) + 1

    while time.time() < deadline:

        with lock:
            remaining = any(
                start_seq <= key[0] < end_seq
                for key in pending
            )

        if not remaining:
            break

        time.sleep(0.05)

    with lock:
        batch_sent = sent - start_sent
        batch_acked = acked - start_acked
        batch_first = first_ok - start_first
        batch_retx = retx - start_retx

        batch_lat = []

        for key, p in list(pending.items()):
            if start_seq <= key[0] < end_seq:
                del pending[key]

        # Latencies are collected from ACKs received during this batch.
        # See the batch latency collection below.

    # Collect batch ACK latencies from the ACK records.
    # Each completed ACK is recorded separately by the receive thread.

    batch_no += 1

    loss_first = (
        100 * (batch_sent - batch_first) / max(batch_sent, 1)
    )

    loss_final = (
        100 * (batch_sent - batch_acked) / max(batch_sent, 1)
    )

    with lock:
        batch_lat = [
            p['latency']
            for p in completed
            if start_seq <= p['seq'] < end_seq
        ]

        completed[:] = [
            p for p in completed
            if not (start_seq <= p['seq'] < end_seq)
        ]

    if batch_lat:
        batch_lat.sort()
        avg = statistics.mean(batch_lat)
        p95 = batch_lat[math.ceil(0.95 * len(batch_lat)) - 1]
        maximum = batch_lat[-1]
    else:
        avg = p95 = maximum = 0

    print(f'\n===== RESULTS [{args.label}_{batch_no}] =====')
    print(f'sent={batch_sent} acked={batch_acked} retransmissions={batch_retx}')
    print(f'packet loss (first transmission): {loss_first:.1f}%')
    print(f'undelivered after retries:        {loss_final:.1f}%')
    print(f'latency ms: avg={avg:.1f} p95={p95:.1f} max={maximum:.1f}')

    with open('results.csv', 'a') as f:
        f.write(
            f'{args.label}_{batch_no},{batch_sent},{batch_acked},'
            f'{batch_retx},{loss_first:.1f},{loss_final:.1f},'
            f'{avg:.1f},{p95:.1f},{maximum:.1f}\n'
        )

    print('\nSubscribers remain registered.')


completed = []


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

            print(f'[-] subscriber unregistered: {addr}')

        elif parts[0] == 'ACK':
            with lock:
                key = (int(parts[1]), addr)
                p = pending.pop(key, None)

                if p:
                    acked += 1
                    latency = (time.time() - p['first']) * 1000

                    completed.append({
                        'seq': int(parts[1]),
                        'latency': latency
                    })

                    if p['tries'] == 1:
                        first_ok += 1


threading.Thread(target=rx, daemon=True).start()
threading.Thread(target=retransmit, daemon=True).start()

print(f'Emergency server running on UDP {args.port}')
print('Waiting for subscribers to register...')

while True:
    try:
        value = input('\nEnter number of alerts (or q to quit): ').strip()

        if value.lower() == 'q':
            break

        count = int(value)

        if count <= 0:
            print('Enter a positive number.')
            continue

        run_batch(count)

    except ValueError:
        print('Enter a valid number.')

    except KeyboardInterrupt:
        break

sock.close()
print('Server stopped.')
