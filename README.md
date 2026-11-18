# Emergency Notification System using Software Defined Networking (SDN)

## Project Overview

The **Emergency Notification System using SDN** is a network-based application designed to prioritize emergency notifications over ordinary network traffic.

The project uses **Software Defined Networking (SDN)** to identify emergency UDP packets, assign them higher forwarding priority, and provide preferential bandwidth allocation during network congestion.

By combining UDP communication, the Ryu SDN controller, OpenFlow rules, and Quality of Service (QoS), the system demonstrates how critical notifications can receive preferential network treatment.

## Objectives

- Develop a UDP-based emergency notification system.
- Allow multiple subscribers to register with an emergency server.
- Deliver emergency notifications to registered subscribers.
- Identify emergency packets using DSCP marking.
- Prioritize emergency traffic using SDN and OpenFlow.
- Implement QoS-based queue management.
- Monitor network traffic and detect congestion.
- Demonstrate preferential treatment of emergency traffic during competing network traffic.

## System Architecture

The network consists of four hosts connected through two Open vSwitch switches.

| Component | Function |
|---|---|
| h1 | Emergency notification server |
| h2 | Subscriber 1 |
| h3 | Subscriber 2 |
| h4 | Background traffic generator |
| s1 | First OpenFlow switch |
| s2 | Second OpenFlow switch |
| Ryu Controller | Centralized SDN control and traffic prioritization |

The connection between s1 and s2 acts as the network bottleneck, with a configured bandwidth limit of 2 Mbps.

## Technologies Used

- **Python 3** – Application development
- **UDP (User Datagram Protocol)** – Emergency notification communication
- **Ryu SDN Controller** – Centralized network control
- **OpenFlow 1.3** – Flow management and packet forwarding
- **Open vSwitch (OVS)** – Software-based network switching
- **Mininet** – Network topology emulation
- **Linux HTB Queuing** – Bandwidth management and QoS
- **Ubuntu** – Development and execution environment

## Key Features

### 1. Subscriber Registration

Subscribers connect to the emergency notification server and register to receive emergency messages. The server maintains a list of active subscribers.

### 2. UDP-Based Emergency Notifications

The server sends emergency notifications using UDP, enabling lightweight and fast communication across the emulated network.

### 3. DSCP-Based Emergency Identification

Emergency packets are marked with **DSCP value 46 (Expedited Forwarding – EF)**.

This allows the SDN controller to distinguish emergency traffic from ordinary network traffic.

### 4. SDN-Based Traffic Prioritization

The Ryu controller monitors packet-in events and installs OpenFlow forwarding rules.

Emergency flows are assigned a higher priority than ordinary flows, allowing the network to handle critical traffic preferentially.

### 5. QoS and Queue Management

The bottleneck link is configured with a total bandwidth capacity of 2 Mbps.

Two queues are configured:

- **Queue 0:** Default traffic queue.
- **Queue 1:** Emergency traffic queue with a configured minimum rate of 1.5 Mbps and maximum rate of 2 Mbps.

The controller assigns identified emergency traffic to Queue 1 at the bottleneck switch port.

### 6. Congestion Monitoring

The Ryu controller periodically monitors traffic statistics on the bottleneck link and reports the network congestion status.

Background UDP traffic is generated to simulate network load and evaluate emergency traffic prioritization.

## Network Topology

```text
              h1
      Emergency Server
              |
              |
             s1 -------- h4
              |       Background
              |        Traffic
       2 Mbps Bottleneck
              |
             s2
            /  \
           /    \
         h2      h3
      Subscriber Subscriber
          1         2

        Ryu SDN Controller
          (OpenFlow 1.3)
```

## Project Structure

```text
Emergency-Notification-System/
│
├── server.py
├── client.py
├── controller.py
├── topo.py
└── README.md
```

## Execution Overview

1. Start the Ryu SDN controller in priority mode.
2. Launch the Mininet network topology.
3. Start subscriber clients on h2 and h3.
4. Start the emergency notification server on h1.
5. Verify subscriber registration.
6. Send emergency notifications from the server.
7. Generate background UDP traffic from h4.
8. Observe emergency traffic prioritization and queue statistics.
9. Monitor congestion through the Ryu controller.

## Expected Outcome

The project demonstrates an SDN-based emergency communication architecture in which:

- Multiple subscribers can register with the emergency server.
- Emergency notifications are transmitted using UDP.
- Emergency packets are identified through DSCP marking.
- OpenFlow rules assign higher priority to emergency traffic.
- QoS queues provide preferential bandwidth allocation.
- The controller monitors traffic conditions on the bottleneck link.

## Future Enhancements

- Web-based monitoring dashboard.
- Support for additional subscribers.
- Dynamic bandwidth allocation based on network conditions.
- Integration with real-world emergency alert applications.
- Advanced traffic analytics and performance visualization.

## Conclusion

This project demonstrates the application of Software Defined Networking in emergency communication systems.

By combining centralized network control, DSCP-based packet identification, OpenFlow forwarding rules, and QoS queue management, the system provides a framework for prioritizing critical notifications in bandwidth-constrained network environments.

---

**Platform:** Ubuntu, Mininet and Open vSwitch
