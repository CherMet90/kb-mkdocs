---
title: Mikrotik RouterOS
date: 2026-05-04
---

# Mikrotik RouterOS

## IPsec (GRE over IPsec)

В обычной ситуации достаточно создать интерфейс типа GRE Tunnel - всё необходимое будет создаваться автоматически  
Если же это не подходит, например мы хотим включить режим response-only (passive), то при создании интерфейса GRE Tunnel не задаём пароль ipsec и предварительно создаём вручную динамические сущности для тунеля:  

```
/ip ipsec peer
add name=new-peer address=X.X.X.X/32 local-address=Y.Y.Y.Y passive=yes
```
```
/ip ipsec identity
add peer=new-peer auth-method=pre-shared-key secret="ВАШ_PSK"
```
```
/ip ipsec policy
add src-address=Y.Y.Y.Y/32 dst-address=X.X.X.X/32 protocol=gre \
    action=encrypt tunnel=no peer=new-peer proposal=default
```

<!-- more -->

## BGP

1. Создаём префикс-листы
    ```
    /routing filter rule
    add chain=bgp-in disabled=no rule=\
        "if ((dst in <принимаемый_префикс>/15) || (dst in <принимаемый_префикс>/15)) { accept }"
    ```
2. Настраиваем нашу ASN
    ```
    /routing bgp template
    set default as=<номер_локальной_asn> disabled=no router-id=<ip_адрес_роутера> routing-table=main
    ```
3. Создаём соединение с соседом
    ```
    /routing bgp connection
    add as=<номер_локальной_asn> disabled=no input.filter=bgp-in local.address=\
        <локальный_тунельный_ip> .role=ebgp name=connection-name output.network=<адрес-лист_анонсируемых_подсетей> \
        remote.address=<тунельный_ip_соесда>/32 .as=<asn_соседа> \
        templates=default
    ```

## VPN users

Команды для быстрого получения списка PPP и WireGuard учёток:

```
/ppp secret print proplist=name,service,last-logged-out
/interface wireguard peers print proplist=name,client-address,last-handshake
```

## NAT / Connection Tracking

Просмотр активных NAT-трансляций (маскарад, проброс портов):

```
# Все активные соединения
/ip firewall connection print

# Только srcnat (маскарад)
/ip firewall connection print where src-nat

# Только dstnat (проброс портов)
/ip firewall connection print where dst-nat

# Фильтр по подсети назначения
/ip firewall connection print where dst-address in 10.156.0.0/16

# Фильтр по подсети источника (кто ходит наружу)
/ip firewall connection print where src-address in 10.156.0.0/16 && src-nat

# Статистика срабатываний правил NAT
/ip firewall nat print stats
```
