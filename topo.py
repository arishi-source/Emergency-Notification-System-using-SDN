#!/usr/bin/env python3
import subprocess
from functools import partial
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel

RATE = 2000000  # bottleneck 2 Mbps


def add_qos(intf):
    """HTB on the s1->s2 port: queue1 = emergency (reserved), queue0 = default."""
    cmd = (
        f"ovs-vsctl set port {intf} qos=@q -- "
        f"--id=@q create qos type=linux-htb other-config:max-rate={RATE} "
        f"queues:0=@q0 queues:1=@q1 -- "
        f"--id=@q0 create queue other-config:min-rate=100000 "
        f"other-config:max-rate={RATE} other-config:priority=2 -- "
        f"--id=@q1 create queue other-config:min-rate=1500000 "
        f"other-config:max-rate={RATE} other-config:priority=1"
    )
    subprocess.run(cmd, shell=True, check=True)


def run():
    net = Mininet(controller=None,
                  switch=partial(OVSSwitch, protocols='OpenFlow13'))
    net.addController('c0', controller=RemoteController,
                      ip='127.0.0.1', port=6653)
    s1 = net.addSwitch('s1')
    s2 = net.addSwitch('s2')
    h1 = net.addHost('h1', ip='10.0.0.1/24')  # emergency server
    h2 = net.addHost('h2', ip='10.0.0.2/24')  # subscriber
    h3 = net.addHost('h3', ip='10.0.0.3/24')  # subscriber
    h4 = net.addHost('h4', ip='10.0.0.4/24')  # background traffic

    # order matters: s1-eth1=h1, s1-eth2=h4, s1-eth3=s2
    net.addLink(h1, s1)
    net.addLink(h4, s1)
    net.addLink(s1, s2)
    net.addLink(h2, s2)
    net.addLink(h3, s2)

    net.start()
    add_qos('s1-eth3')
    print("Bottleneck s1-eth3 limited to 2 Mbps with emergency queue ready")
    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run()
