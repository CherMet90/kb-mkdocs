Для работы роутерных функций ipv6 не забываем включить глобально:
`ipv6 unicast-routing`  
<br>

##### PE:
Пример искусственный, поэтому учетка pppoe-клиента создаётся локально на сервере:
```
username R2 password 0 PAP
```
Создаём bba pppoe группу:
```
bba-group pppoe PPPOE_28
 virtual-template 28        # cсылаемся на нужный шаблон
 sessions per-mac limit 1   # устанавливаем ограничение на количество сессий на мак
```
Создаём шаблон интерфейса:
```
interface Virtual-Template28
 mtu 1492
 ip unnumbered Loopback28                   # при создании экземпляра интерфейса будет клонирован ip указанного интерфейса
 ip nat inside
 peer default ip address pool PPPOE_POOL_V4 # указываем имя пула для ipv4 пиринга
 peer default ipv6 pool PPPOE_POOL_V6       # указываем имя пула для ipv6 пиринга
 ipv6 enable
 no ipv6 nd ra suppress                     # включаем для раздачи адресов в режиме SLAAC
 ipv6 nd ra lifetime 60
 ipv6 nd ra interval 10 5
 ipv6 dhcp server DHCP_POOL_V6              # указываем имя пула для работы prefix-deligation(PD)
 ppp authentication pap callin              # включение требования аутентификации методом PAP
```
```
interface Loopback28
 ip address 209.2.8.99 255.255.255.0
```
Создаём ip-пулы:
```
ip local pool PPPOE_POOL_V4 209.2.8.100 209.2.8.149
ipv6 local pool PPPOE_POOL_V6 2001:10:2:80::/60 64
ipv6 local pool PD_POOL_V6 2001:192:168:80::/60 64
```
Линкуем dhcp-пул для PD с локальным:
```
ipv6 dhcp pool DHCP_POOL_V6
 prefix-delegation pool PD_POOL_V6
```
Включаем pppoe на интерфейсе:
```
interface Ethernet0/0
 description CE
 no ip address
 pppoe enable group PPPOE_28
```
Указываем внешний интерфейс для NAT:
```
interface Ethernet0/3
 description Uplink
 ip nat outside
```
Создаём правило натирования:
```
ip nat inside source list 100 interface Ethernet0/3 overload
access-list 100 permit ip 209.2.8.0 0.0.0.255 any   # указываем диапазон ip для натирования
```
<br>

##### CE:
Включаем pppoe на интерфейсе:
```
interface Ethernet0/0
 description -Uplink=PE8--
 no ip address
 pppoe enable group global
 pppoe-client dial-pool-number 28
```
Создаём pppoe-подключение:
```
interface Dialer28
 mtu 1492 
 ip address negotiated                      # указываем необходимость получения ip по pppoe
 ip nat outside                             # указываем подключение как внешнее для NAT
 encapsulation ppp                          # включаем pppoe
 dialer pool 28                             # линкуемся с номером пула указанного в pppoe-интерфейсе
 dialer idle-timeout 0                      # отключаем автоматическое прерывании pppoe-сессии при отсутствии трафика
 dialer persistent                          # включаем реконект при падении сессии
 ipv6 address autoconfig default            # включаем получение ipv6 методом SLAAC
 ipv6 dhcp client pd PPPOE_ISP_PREFIX       # указываем имя куда поместим префиксы для prefix-deligation
 ppp pap sent-username R2 password 0 PAP    # логин/пароль для pppoe-соединения
 ppp ipcp route default                     # использовать подключение как маршрут по-умолчанию
```
Интерфейс в сторону LAN-клиента:
```
interface Ethernet0/1
 description client
 ip address 192.168.2.2 255.255.255.0
 ip nat inside
 ipv6 address FE80::2 link-local
 ipv6 address PPPOE_ISP_PREFIX ::2/64   # используем для формирования IPv6-адреса PD-префикс, полученный по pppoe
 ipv6 nd ra lifetime 30
 ipv6 nd ra interval 10 5
```
Объявляем dhcp-pool для ipv4-клиентов:
```
ip dhcp excluded-address 192.168.2.0 192.168.2.20
ip dhcp pool DHCP_POOL_V4
 network 192.168.2.0 255.255.255.0
 default-router 192.168.2.2 
```
Правило для NAT:
```
ip nat inside source list NAT_ACL interface Dialer28 overload
ip access-list standard NAT_ACL
 permit 192.168.2.0 0.0.0.255
```