import os
import time
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4
from ryu.lib import hub

MODE = os.environ.get('MODE', 'priority')   # priority | baseline
EF = 46                                      # DSCP value of emergency traffic
EMERGENCY_QUEUE = 1
BOTTLENECK = {1: 3}                          # dpid 1 (s1), port 3 -> s2 (has queues)


class EmergencySDN(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.dps = {}
        self.last = {}
        self.logger.info("=== CONTROLLER MODE: %s ===", MODE)
        hub.spawn(self._monitor)

    # ---------- setup ----------
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def features_handler(self, ev):
        dp = ev.msg.datapath
        ofp, parser = dp.ofproto, dp.ofproto_parser
        self.dps[dp.id] = dp
        actions = [parser.OFPActionOutput(ofp.OFPP_CONTROLLER, ofp.OFPCML_NO_BUFFER)]
        self.add_flow(dp, 0, parser.OFPMatch(), actions)

    def add_flow(self, dp, prio, match, actions, idle=0):
        ofp, parser = dp.ofproto, dp.ofproto_parser
        inst = [parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]
        dp.send_msg(parser.OFPFlowMod(datapath=dp, priority=prio, match=match,
                                      instructions=inst, idle_timeout=idle))

    # ---------- classification + forwarding ----------
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofp, parser = dp.ofproto, dp.ofproto_parser
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        if eth.ethertype == 0x88cc:      # ignore LLDP
            return

        self.mac_to_port.setdefault(dp.id, {})[eth.src] = in_port
        out_port = self.mac_to_port[dp.id].get(eth.dst, ofp.OFPP_FLOOD)

        ip = pkt.get_protocol(ipv4.ipv4)
        dscp = (ip.tos >> 2) if ip else 0
        emergency = (dscp == EF)

        actions = []
        if out_port != ofp.OFPP_FLOOD:
            prio = 10
            if emergency and MODE == 'priority':
                prio = 100
                if BOTTLENECK.get(dp.id) == out_port:
                    actions.append(parser.OFPActionSetQueue(EMERGENCY_QUEUE))
                self.logger.info("EMERGENCY flow: s%d %s -> port %d (queue %d)",
                                 dp.id, eth.src, out_port, EMERGENCY_QUEUE)
            actions.append(parser.OFPActionOutput(out_port))

            fields = dict(in_port=in_port, eth_dst=eth.dst)
            if ip:
                fields.update(eth_type=0x0800, ip_dscp=dscp)
            self.add_flow(dp, prio, parser.OFPMatch(**fields), actions, idle=30)
        else:
            actions.append(parser.OFPActionOutput(ofp.OFPP_FLOOD))

        dp.send_msg(parser.OFPPacketOut(datapath=dp, buffer_id=msg.buffer_id,
                                        in_port=in_port, actions=actions,
                                        data=msg.data))

    # ---------- congestion monitoring ----------
    def _monitor(self):
        while True:
            hub.sleep(2)
            dp = self.dps.get(1)
            if dp:
                dp.send_msg(dp.ofproto_parser.OFPPortStatsRequest(dp, 0, BOTTLENECK[1]))

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def stats_handler(self, ev):
        now = time.time()
        for s in ev.msg.body:
            prev = self.last.get(s.port_no)
            self.last[s.port_no] = (s.tx_bytes, now)
            if prev:
                mbps = (s.tx_bytes - prev[0]) * 8 / (now - prev[1]) / 1e6
                state = "CONGESTED" if mbps > 1.6 else "ok"
                self.logger.info("[monitor] s1 port %d: %.2f Mbps  %s",
                                 s.port_no, mbps, state)
