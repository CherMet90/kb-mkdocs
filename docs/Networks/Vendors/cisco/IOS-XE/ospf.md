##### Redistribute static

```
ip route <номер_подсети> 255.255.255.0 <известный_ip_connected_подсети> name AWS

ip prefix-list s2o seq 5 permit <номер_подсети>/24

route-map s2o permit 10
 match ip address prefix-list s2o

router ospf 156
 redistribute static subnets route-map s2o
```