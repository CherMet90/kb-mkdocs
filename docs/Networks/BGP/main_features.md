```
router bgp [наша AS]
	no bgp default ipv4-unicast
	neighbor [ip eBGP-соседа] remote-as [соседняя AS] 	# Объявляем eBGP-соседа
	neighbor RR_CLIENTS peer-group						# Для оптимизации можем объединять соседей в пир-группы и применять настройки сразу ко всем её членам. В данном случае объединим всех клиентов RR
	neighbor RR_CLIENTS remote-as [наша AS]		
	neighbor RR_CLIENTS update-source Loopback0		# Анонс маршрутов в iBGP от имени Lo0. Лупбэк никогда не падает и позволит поддерживать full-mesh связность
	neighbor RR_CLIENTS next-hop-self				# Подставлять себя в качестве next-hop, т.к. у iBGP-соседа нет маршрута до eBGP-соседа
	neighbor RR_CLIENTS route-reflector-client		# В случае если роутер выполняет роль RR, этой командой объявляем RR-клиентов
	neighbor <client_IP> peer-group RR_CLIENTS		# Добавляем соседа в группу
	address-family ipv4
		aggregate-address [ip mask агрегированного] as-set summary-only
		# summary-only - указывает не анонсить сагрегированные маршруты
		# as-set - без этой команды роутер затирает весь AS_Path и подставляет свою AS (BGP atomic aggregate).
		network [айпишник] mask [маска] # анонсим подсетку
		neighbor [ip соседа] activate
```
<br>

##### Способы фильтрации маршрутов
###### Distribution list
```
ip access-list extended ACL_NAME
 permit ip 172.16.0.0 0.0.255.255 255.255.255.0 0.0.0.255
router bgp 65100
 address-family ipv4
  neighbor 10.12.1.2 distribute-list ACL_NAME in
```
Пропускаем все 172.16.х.х подсетки с префиксами от /24 до /32  
(*ip wildcard mask wildcard*)

###### Prefix list
```
ip prefix-list defaultExclude seq 5 deny 0.0.0.0/0
ip prefix-list defaultExclude seq 10 permit 0.0.0.0/0 le 24
```
```
router bgp 65530
 neighbor 10.10.1.4 prefix-list defaultExclude in
```
пропускаем только префиксы от /24 и выше

###### AS_Path filtering
```
ip as-path access-list 1 permit ^$	# locally originated routes
ip as-path access-list 2 permit ^300_	# routes advertised by AS300
ip as-path access-list 3 permit _40$	# routes originated from AS40
```
```
router bgp 65530
 neighbor 10.10.1.4 filter-list 1 out
```

###### Route maps
```
ip prefix-list default_route permit 0.0.0.0/0
ip prefix-list RFC1918 permit 10.0.0.0/8 le 32
ip prefix-list RFC1918 permit 172.16.0.0/12 le 32
ip prefix-list RFC1918 permit 192.168.0.0/16 le 32
ip prefix-list proper_prefixes permit 0.0.0.0/0 le 24
ip prefix-list LIST_NAME permit 100.64.0.0/0 le 24
ip as-path access-list 1 permit _65200$
!
route-map AS65200IN deny 10
 match ip address prefix-list RFC1918 default_route
route-map AS65200IN permit 20
 match ip address prefix-list LIST_NAME
 match as-path 1
 set local-preference 222
route-map AS65200IN permit 30
 match as-path 1
 set weight 65200
route-map AS65200IN permit 40
 match ip address prefix-list proper_prefixes
!
router bgp 65100
 address-family ipv4
  neighbor 10.12.1.2 route-map AS65200IN in
```
Route maps позволяют работать одновременно с префикс листами, фильтрацией по AS и манипулировать с path атрибутами.  
В приведенном примере на первом этапе дропаются приватные подсети и дэфолтный маршрут.  
Затем для подсетей, подходящих одновременно для префикс листа и AS-фильтра, устанавливается значение атрибута local-preference.  
У подсетей из AS-фильтра, но не из префикс-листа, задается атрибут weight.  
Сети из prefix-list proper_prefixes пропускаются без изменений, остальные соответственно дропаются из-за *explicit deny*

**Note:** принцип *explicit deny* в целом распространяется на все приведенные здесь способы фильтрации