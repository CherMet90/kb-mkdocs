```
crypto isakmp policy 10	# настройки фазы 1
 encr aes
 hash sha
 authentication pre-share
 group 2
 lifetime 86400
crypto isakmp key cisco address 10.1.23.3 # Внешний айпи соседа
!
!
crypto ipsec transform-set TS esp-aes esp-sha-hmac	# настройка фазы 2
 mode transport	# включаем транспортный режим для случаев GRE over IPsec и VTI, позволяет уменьшить величину заголовков по сравнению с дэфолтным режимом tunnel
!
crypto ipsec profile IPSECPROFILE
 set transform-set TS 
!
interface Tunnel1
 ip address 10.10.100.1 255.255.255.252 # собственный тунельный адрес
 tunnel source GigabitEthernet0/1	# интерфейс, с которого строим тунель
 tunnel mode ipsec ipv4			# включаем режим VTI
 tunnel destination 10.1.23.3
 tunnel protection ipsec profile IPSECPROFILE
!
```