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
python3 server.py --interval 0.2 --timeout 0.3 --retries 3 --label normal
```
Enter number of alerts (or q to quit): 20
Enter number of alerts (or q to quit): 50
Enter number of alerts (or q to quit): 100

## PART 2: Congestion Testing (Fresh Setup)

### Step 1: Continue in mininet terminal

At `mininet>`:

```
xterm h2 h3
```

### Step 2: Start Background UDP Receiver

**In New h3 terminal:**

```bash
iperf -s -u -p 6000
```

### Step 6: Start Congestion

**In h4 terminal:**

```bash
iperf -c 10.0.0.3 -u -p 6000 -b 5M -t 60
```

### Step 7: Send Emergency Alert During Congestion

Enter number of alerts (or q to quit): 20
Enter number of alerts (or q to quit): 50
Enter number of alerts (or q to quit): 100

### Check RYU TERMINAL TO CONFIRM IF THE EMERGENCY FLOW IS SENT BETWEEN CONGESTION

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
