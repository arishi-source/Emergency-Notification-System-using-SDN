# Running Instructions – Emergency Notification System using SDN

## PART 1: Normal Operation (Without Congestion)

### Step 1: Start Ryu Controller (Terminal 1)

```bash
cd ~/emergency-sdn
MODE=priority ~/ryuenv/bin/ryu-manager controller.py
```

### Step 2: Start Mininet (Terminal 2)

```bash
cd ~/emergency-sdn
sudo python3 topo.py
```

At the `mininet>` prompt:

```text
pingall
xterm h2 h3
```

### Step 3: Start Subscribers

**h2 terminal:**

```bash
cd ~/emergency-sdn
python3 client.py --server 10.0.0.1 --port 9999
```

**h3 terminal:**

```bash
cd ~/emergency-sdn
python3 client.py --server 10.0.0.1 --port 9998
```

### Step 4: Start Emergency Server

At `mininet>`:

```text
xterm h1
```

**h1 terminal:**

```bash
cd ~/emergency-sdn
python3 server.py
```

### Step 5: Send Emergency Alert

At the h1 `alert>` prompt:

```text
TEST EMERGENCY ALERT
```

Verify that both h2 and h3 receive the alert.

---

## PART 2: Congestion Testing (Fresh Setup)

### Step 1: Keep Ryu Running and Close Mininet

At the existing `mininet>` prompt:

```text
exit
```

In a normal Ubuntu terminal:

```bash
sudo mn -c
```

### Step 2: Start Fresh Mininet

```bash
cd ~/emergency-sdn
sudo python3 topo.py
```

At `mininet>`:

```text
pingall
xterm h2 h3
```

### Step 3: Register Subscribers Again

**h2 terminal:**

```bash
cd ~/emergency-sdn
python3 client.py --server 10.0.0.1 --port 9999
```

**h3 terminal:**

```bash
cd ~/emergency-sdn
python3 client.py --server 10.0.0.1 --port 9998
```

### Step 4: Start Fresh Emergency Server

At `mininet>`:

```text
xterm h1
```

**h1 terminal:**

```bash
cd ~/emergency-sdn
python3 server.py
```

Wait for both subscribers to register.

### Step 5: Start Background UDP Receiver

At `mininet>`:

```text
xterm h3 h4
```

**New h3 terminal:**

```bash
iperf -s -u -p 6000
```

### Step 6: Start Congestion

**h4 terminal:**

```bash
iperf -c 10.0.0.3 -u -p 6000 -b 5M -t 60
```

### Step 7: Send Emergency Alert During Congestion

In the original h1 server terminal, at `alert>`:

```text
EMERGENCY ALERT DURING CONGESTION
```

Check whether both subscribers receive the alert.

### Step 8: Verify SDN Priority and Queue Statistics

In a normal Ubuntu terminal:

```bash
sudo ovs-ofctl -O OpenFlow13 dump-flows s1

sudo ovs-ofctl -O OpenFlow13 queue-stats s1 3
```

Check the Ryu terminal for congestion monitoring messages.

---

## Network Configuration

| Parameter | Value |
|---|---|
| Emergency server | h1 – 10.0.0.1 |
| Subscriber 1 | h2 – 10.0.0.2 |
| Subscriber 2 | h3 – 10.0.0.3 |
| Background traffic | h4 – 10.0.0.4 |
| Protocol | UDP |
| DSCP | 46 (EF) |
| Bottleneck | s1-eth3 |
| Bandwidth | 2 Mbps |
| Emergency queue | Queue 1 |
| Minimum reserved rate | 1.5 Mbps |
| Maximum rate | 2 Mbps |
