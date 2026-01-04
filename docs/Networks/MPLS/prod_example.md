##### Пример конфига для реализации L3VPN
```
vrf definition <имя_клиента>
	rd <наша_AS>:2649
	route-target export <наша_AS>:2649
	route-target import <наша_AS>:2649

interface TenGigabitEthernet0/2/0.1686140
	vrf forwarding <имя_клиента>
	ip address 192.168.12.2 255.255.255.252
	

router bgp [наша AS]
	no bgp default ipv4-unicast
	neighbor [ip соседа] remote-as [соседняя AS]
	address-family vpnv4
		neighbor [ip соседа] activate
		neighbor [ip соседа] send-community both
	address-family ipv4 vrf <имя_клиента>
		redistribute connected
		redistribute static
	address-family ipv4 vrf INTERNET
		network 188.168.15.0 mask 255.255.255.0 [route-map SET-COMMUNITY-<?_AS>:164]
		network 188.168.33.0 mask 255.255.255.0 [route-map SET-COMMUNITY-<?_AS>:264]
		network 213.80.248.0 mask 255.255.248.0 [route-map SET-COMMUNITY-<наша_AS>:64]
		network 217.23.64.0 mask 255.255.224.0 [route-map SET-COMMUNITY-<наша_AS>:64]
```