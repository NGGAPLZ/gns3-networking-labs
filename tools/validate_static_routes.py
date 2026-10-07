"""Check saved lab addresses and modeled forwarding; does not run GNS3."""
import ipaddress as ip
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / 'static-routing' / 'gns3'


def main():
    topology = json.loads((ROOT / 'static-routing.gns3').read_text())['topology']
    nodes = {n['node_id']: n for n in topology['nodes']}
    assert len(nodes) == len(topology['nodes']), 'Duplicate node IDs'
    for link in topology['links']:
        assert len(link['nodes']) == 2
        assert all(n['node_id'] in nodes for n in link['nodes'])
    routers, hosts = {}, {}
    for node in nodes.values():
        name, uid = node['name'], node['node_id']
        if node['node_type'] == 'dynamips':
            configs = list((ROOT / 'project-files' / 'dynamips' / uid / 'configs').glob('*.cfg'))
            assert len(configs) == 1, name
            text = configs[0].read_text()
            addresses = [ip.ip_interface(f'{a}/{m}') for a, m in
                         re.findall(r'^ ip address (\S+) (\S+)$', text, re.M)]
            routes = [(ip.ip_network(f'{a}/{m}'), ip.ip_address(via)) for a, m, via in
                      re.findall(r'^ip route (\S+) (\S+) (\S+)$', text, re.M)]
            assert addresses, name
            routers[name] = (addresses, routes)
        elif node['node_type'] == 'vpcs':
            text = (ROOT / 'project-files' / 'vpcs' / uid / 'startup.vpc').read_text()
            match = re.search(r'^ip (\S+) (\S+) (\S+)$', text, re.M)
            assert match, f'{name}: no saved IP'
            addr = ip.ip_interface(f'{match[1]}/{match[2]}')
            gateway = ip.ip_address(match[3])
            assert gateway in addr.network, name
            hosts[name] = (addr, gateway)
    assert len(routers) == 4 and len(hosts) == 4
    owners = {a.ip: name for name, (addresses, _) in routers.items() for a in addresses}
    assert len(owners) == sum(len(a) for a, _ in routers.values()), 'Duplicate router IP'
    for name, (addresses, routes) in routers.items():
        for _, via in routes:
            assert via in owners and owners[via] != name, f'{name}: unknown next hop'
            assert any(via in a.network for a in addresses), f'{name}: next hop not on-link'
    for addr, gateway in hosts.values():
        assert gateway in owners and addr.ip not in owners

    def trace(source, destination):
        src, gateway = hosts[source]
        dst, _ = hosts[destination]
        if dst.ip in src.network:
            return [source, destination]
        current, seen, path = owners[gateway], set(), [source]
        while current not in seen:
            seen.add(current)
            path.append(current)
            addresses, routes = routers[current]
            if any(dst.ip in a.network for a in addresses):
                return path + [destination]
            matches = [(net, via) for net, via in routes if dst.ip in net]
            assert matches, f'{current}: no route to {destination}'
            _, via = max(matches, key=lambda pair: pair[0].prefixlen)
            current = owners[via]
        raise AssertionError(f'Routing loop: {path}')

    count = 0
    for source in sorted(hosts):
        for destination in sorted(hosts):
            if source != destination:
                print(' -> '.join(trace(source, destination)))
                count += 1
    print(f'PASS: 4 router configs, 4 PC configs, {count} directed modeled paths.')
    print('Offline configuration check only; link state and live ping are not tested.')


if __name__ == '__main__':
    main()
