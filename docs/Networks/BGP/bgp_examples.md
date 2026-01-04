##### Иллюстрация лабораторной настройки соседства
###### Сторона ISP
```
router bgp 65530
 neighbor 10.10.1.4 remote-as 65512
 neighbor 10.10.1.4 description R4
 neighbor 10.10.1.4 default-originate	# транслируем себя как дэфолтный маршрут
 neighbor 10.10.1.4 prefix-list defaultExclude in	# применяем префикс-лист на входящие маршруты
```
Дропаем дэфолтный маршрут, остальное пропускаем:
```
ip prefix-list defaultExclude seq 5 deny 0.0.0.0/0
ip prefix-list defaultExclude seq 10 permit 0.0.0.0/0 le 24	# пропускаем только префиксы от /24 и выше (best practice)
```
###### Сторона клиента (с мультихоумингом)
```
router bgp 65512
 network 172.16.0.0 mask 255.255.255.0
 neighbor 10.10.1.1 remote-as 65520
 neighbor 10.10.1.1 description R1
 neighbor 10.10.1.1 weight 10	# Присваиваем вес маршрутам пира (больше вес - выше приоритет)
 neighbor 10.10.1.1 route-map lowerMetric out	# модифицируем метрику исходящих маршрутов
 neighbor 10.10.1.2 remote-as 65520
 neighbor 10.10.1.2 description R2
 neighbor 10.10.1.2 weight 20
 neighbor 10.10.1.2 route-map lowerMetric out
 neighbor 10.10.1.5 remote-as 65530
 neighbor 10.10.1.5 description R3
 neighbor 10.10.1.5 weight 30
 neighbor 10.10.1.5 route-map higherMetric out

ip prefix-list Our_Networks seq 5 permit 172.16.0.0/24
!
route-map higherMetric permit 10
 match ip address prefix-list Our_Networks
 set metric 20
!
route-map lowPriority permit 10	# роут-мэп, добавляющий лишнюю AS в атрибуты маршрута
 match ip address prefix-list Our_Networks
 set as-path prepend 65512
!
route-map lowerMetric permit 10
 match ip address prefix-list Our_Networks
 set metric 10
```

##### Демонстрация настройки связки eBGP-PE-CE-iBGP
###### eBGP-PE:
*аналогично eBGP-CE, но очевидно без указания дэфолтного маршрута на интерфейс BGP-соседа*

###### eBGP-CE:
```
router bgp 414	# наша AS
 network 4.4.4.4 mask 255.255.255.255	# что анонсим в BGP (что должно быть доступно через BGP)
 neighbor 10.0.64.5 remote-as 1	# интерфейс соседа вышестоящей AS
 neighbor 10.0.64.5 description R5
 neighbor 10.0.64.5 prefix-list defaultExclude in	# дропаем дэфолтный маршрут, если приходит
ip prefix-list defaultExclude seq 5 deny 0.0.0.0/0
ip prefix-list defaultExclude seq 10 permit 0.0.0.0/0 le 24
ip route 0.0.0.0 0.0.0.0 GigabitEthernet0/0 10.0.64.5	# делаем интерфейс вышестоящей AS дэфольным
```
###### iBGP:
```
router bgp 414
 neighbor 14.14.14.14 remote-as 414
 neighbor 14.14.14.14 update-source Loopback0	#  слать анонсы от имени лупбэка
 neighbor 14.14.14.14 next-hop-self	# подставлять себя в качестве некс-хопа при передаче анонса по iBGP
router ospf 1	# настраиваем динамику для распространения инфы о лупбэках по iBGP-домену
 passive-interface default	# по-дэфолту подсети ospf-интерфейсов анонсятся, но сами интерфейсы не анонсят
 no passive-interface GigabitEthernet0/0.414	# интерфейс между iBGP-железками распространяет ospf-анонсы
```