##### До Cisco ISR
1. Устанавливаем `strongswan`  
```
sudo apt update
sudo apt install strongswan
```
2. `/etc/ipsec.conf`:  
```
config setup
    charondebug="ike 2, knl 2, cfg 2, net 2, esp 2, dmn 2,  mgr 2"
    
conn %default
    keyexchange=ikev1
    authby=secret
    ike=aes128-sha256-modp2048
    esp=aes128-sha256-modp2048
    dpdaction=clear
    keyingtries=%forever
    
conn cisco-to-ubuntu
    left=%defaultroute
    leftid=<локальный_внешний_ip>
    right=<удаленный_внешний_ip>
    rightid=<удаленный_внешний_ip>
    type=tunnel
    auto=start
```
Если не указывать `leftsubnet` и `rightsubnet`, то сервер поднимет тунель, но принимать или отправлять трафик в него не будет  

3. `/etc/ipsec.secrets`:  
```
<локальный_внешний_ip> <удаленный_внешний_ip> : PSK "p@ssw0rd"
```
4. Перезапускаем службу, поднимаем тунель:  
```
sudo ipsec restart
sudo ipsec up cisco-to-ubuntu
```
5. Для автоматического запуска после загрузки включаем в `systemctl`:
```
sudo systemctl enable strongswan
```

##### VTI до pfSense
1. `/etc/ipsec.conf`:  
```
config setup
    charondebug="ike 2, knl 2, cfg 2, net 2, esp 2, dmn 2,  mgr 2"
    
conn %default
    keyexchange=ikev2
    authby=secret
    keyingtries=%forever
    
conn example
    keyexchange=ikev2
    ike=aes256gcm16-prfsha256-modp2048,aes256-sha256-modp2048,aes128-sha256-modp2048!
    esp=aes256gcm16-prfsha256-modp2048,aes256-sha256-modp2048,aes128-sha256-modp2048!
    leftupdown="/etc/ipsec.d/vti0.sh"
    left=%defaultroute
    leftid=<LOCAL_PUBLIC_IP>
    leftsubnet=0.0.0.0/0
    right=<REMOTE_PUBLIC_IP>
    rightid=<REMOTE_PUBLIC_IP>
    rightsubnet=0.0.0.0/0
    auto=start
    mark=42
    dpdaction=restart
    dpddelay=10s
    dpdtimeout=50s
    ikelifetime=24h
    lifetime=1h
```
2. `/etc/ipsec.secrets`:  
```
<локальный_внешний_ip> <удаленный_внешний_ip> : PSK "p@ssw0rd"
```
3. `/etc/sysctl.conf`:  
```
net.ipv4.ip_forward=1
```
4. `/etc/ipsec.d/vti0.sh`:  
```
#!/bin/bash
    
# Variables
VTI_INTERFACE="vti0"
LOCAL_IP="<LOCAL_PUBLIC_IP>"
REMOTE_IP="<REMOTE_PUBLIC_IP>"
VTI_LOCAL_ADDR="172.31.30.1/30"
VTI_KEY=42
# Define your networks here. Example: "192.168.100.0/24 10.10.10.0/24"
ROUTE_NETS=("192.168.100.0/24" "10.10.10.0/24")
    
function route_exists {
    # Check if the route already exists in the routing table
    # $1 - network
    ip route show $1 dev $VTI_INTERFACE > /dev/null 2>&1
}
    
case "$PLUTO_VERB" in
    up-client)
        # Set up VTI interface
        ip tunnel add $VTI_INTERFACE local $LOCAL_IP remote $REMOTE_IP mode vti key $VTI_KEY
        ip link set $VTI_INTERFACE up
        ip link set dev $VTI_INTERFACE mtu 1400
        ip addr add $VTI_LOCAL_ADDR dev $VTI_INTERFACE
        sysctl -w net.ipv4.conf.$VTI_INTERFACE.disable_policy=1
        
        # Add routes for each network in the list
        for NET in "${ROUTE_NETS[@]}"; do
            ip route add $NET dev $VTI_INTERFACE
        done
        ;;
    down-client)
        # Delete routes for each network in the list
        for NET in "${ROUTE_NETS[@]}"; do
            if route_exists $NET; then
                ip route del $NET dev $VTI_INTERFACE
            fi
        done
        
        # Tear down VTI interface
        ip tunnel del $VTI_INTERFACE
        ;;
esac
```
5.  
```
chmod +x /etc/ipsec.d/vti0.sh
sysctl -p
ipsec restart
ipsec status
systemctl enable strongswan
iptables -t nat -A POSTROUTING -o <интерфейс_в_интернет> -j MASQUERADE
iptables -t mangle -A FORWARD -i vti0 -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu
iptables -t mangle -A POSTROUTING -o vti0 -p tcp -m tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu
```
Последовательность если вдруг скрипт не рабоатет:  
```
ip tunnel add vti0 local <LOCAL_PUBLIC_IP> remote <REMOTE_PUBLIC_IP> mode vti key 42
ip link set vti0 up
ip addr add 172.31.30.1/30 dev vti0
ip route add 10.0.0.0/8 dev vti0
ip route add 192.168.0.0/16 dev vti0
ipsec restart
ping -c 3 172.31.30.2
```
