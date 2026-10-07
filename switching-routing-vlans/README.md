# Switching, dual-stack routing and VLAN isolation

An anonymized write-up of **collaborative coursework**. NGGAPLZ participated in
the project; the source does not separate each person's contributions. The
results below describe the original report. The matching GNS3 project folders
were not supplied, and these three topologies were not rebuilt during preparation.

## 1. MAC learning and ARP

Two C3725 EtherSwitch devices with NM-16ESW modules connected four VPCS endpoints
on 10.1.2.0/24. The switches used VLAN 1 management addresses 10.1.2.101 and
10.1.2.102. PC addresses were 10.1.2.11, .12, .21 and .22.

| Device alias | Management or host address | Relevant ports |
|---|---|---|
| Switch A | 10.1.2.101/24 | Fa1/0, Fa1/2, Fa1/15 |
| Switch B | 10.1.2.102/24 | Fa1/0, Fa1/1, Fa1/15 |
| PC-A1 / PC-A2 | 10.1.2.11 / 10.1.2.12 | Switch A |
| PC-B1 / PC-B2 | 10.1.2.21 / 10.1.2.22 | Switch B |

The original VPCS settings used 10.1.2.101 as a gateway. Same-subnet traffic does
not require a gateway, and a switch management address by itself does not prove
that the switch can route to other networks.

The workflow was to configure VLAN 1 interfaces, enable the access/inter-switch
ports, assign VPCS addresses, then generate ping traffic. Verification used:

```text
show ip interface brief
show mac-address-table dynamic
show arp
```

The report records dynamic MAC entries appearing after traffic, with ARP mapping
IP addresses to MAC addresses and the switching table mapping MAC addresses to
ports. Shutting down Switch B Fa1/0 removed the learned entry for the attached PC;
the port was restored with `no shutdown` afterward.

**Limitation:** one secondary VPCS showed intermittent connectivity. The report's
main demonstration used the stable PC-A1-to-PC-B1 path. This is preserved rather
than presenting every endpoint as consistently verified.

## 2. IPv4 static routes and IPv6 OSPFv3

Two routers connected separate LANs through a transit link. Basic Ethernet
switches connected the PCs to each router's LAN interface.

| Segment | Endpoint | IPv4 | IPv6 |
|---|---|---|---|
| LAN A | R1 Fa0/1 | 192.168.15.65/27 | fc00:0:0:abc0::1/64 |
| LAN A | PC-A | 192.168.15.66/27 | fc00:0:0:abc0::11/64 |
| Transit | R1 Fa0/0 | 192.168.15.97/30 | fc00:0:0:abc1::1/64 |
| Transit | R2 Fa0/0 | 192.168.15.98/30 | fc00:0:0:abc1::2/64 |
| LAN B | R2 Fa0/1 | 192.168.15.101/30 | fc00:0:0:abc2::1/64 |
| LAN B | PC-B | 192.168.15.102/30 | fc00:0:0:abc2::22/64 |

LAN A's /27 provides 30 conventional usable hosts. The transit and LAN B use /30
networks. All three IPv4 subnets fit inside 192.168.15.64/26.

R1 sent LAN B traffic through 192.168.15.98; R2 sent LAN A traffic through
192.168.15.97. IPv6 used OSPFv3 process 10, with router IDs 1.1.1.1 and 2.2.2.2.
The report records a FULL OSPF neighbor state, a learned remote IPv6 LAN route,
and successful IPv4/IPv6 pings in both directions.

```text
show ip route
show ipv6 ospf neighbor
show ipv6 route
```

The fc00 prefixes reproduce historical lab addressing, not a recommendation for
allocating new production IPv6 prefixes. Complete device configurations were not
supplied for this topology, so the summary is not a drop-in configuration file.

## 3. VLAN isolation and a port-security limitation

One C3725 EtherSwitch with an NM-16ESW module separated endpoints into VLAN 10
and VLAN 20. Fa1/1-Fa1/4 were switch-module ports; Fa0/0-Fa0/1 were routed ports.

| Endpoint alias | Access port | VLAN | Address |
|---|---|---|---|
| PC-A1 | Fa1/1 | 10 | 192.168.10.11/24 |
| PC-A2 | Fa1/2 | 10 | 192.168.10.12/24 |
| PC-B1 | Fa1/3 | 20 | 192.168.20.21/24 |
| PC-B2 | Fa1/4 | 20 | 192.168.20.22/24 |

`show vlan-switch brief` showed the intended port membership. Same-VLAN pings
succeeded; cross-VLAN pings failed with no inter-VLAN routing configured.

The attempt to configure `switchport port-security` did not succeed because the
command was unavailable in the tested IOS/interface environment. **Port security
was not implemented or proven.** Confirming support on a suitable switch image
and repeating the test would be the next step.

## Subnetting calculations

- /24 leaves eight host bits: 2^8 - 2 = 254 conventional usable hosts.
- Changing a /16 allocation to /23 borrows seven bits.
- Splitting a /24 into /28 networks gives 16 subnets with 14 conventional usable
  hosts each, satisfying a requirement for at least ten subnets and ten hosts.

These calculations are framed in CIDR terms. The original classful worksheet
terminology was not carried over as a general addressing rule.
