---
title: Харденинг (ASR1K)
description: Приёмы ограничения доступа и защиты Management Plane IOS-XE на примере ASR1K
date: 2026-04-30
---

# Харденинг (ASR1K)

## Терминология

### VTY (Virtual Teletype)

**VTY** — это виртуальные терминальные линии, предназначенные для удалённого управления устройством по протоколам SSH, Telnet или Rlogin. Каждая активная сессия администратора занимает одну VTY-линию. Количество линий (`line vty 0 4`, `0 30` и т.д.) определяет максимальное количество одновременно подключённых пользователей.

Доступ к VTY-линиям может быть ограничен через:

- **access-class** — ACL, фильтрующий входящие соединения по IP-адресу источника.
- **transport input** — протокол, разрешённый для подключения (рекомендуется только `ssh`).

### CoPP (Control Plane Policing) — общий принцип

CoPP (Control Plane Policing) — это механизм QoS-фильтрации, применяемый к трафику, предназначенному **control plane** (CPU) устройства. Позволяет ограничить или заблокировать нежелательный трафик **до** того, как он достигнет CPU.

CoPP строится по архитектуре MQC (Modular QoS CLI):

```
ACL (классификация трафика) → Class-Map (группировка) → Policy-Map (действия: transmit/drop/police) → Control-Plane (применение)
```

**Задачи, которые решает CoPP:**

- Защита CPU от DoS-атак.
- Ограничение частоты (rate-limit) протоколов управления.
- Освобождение ресурсов CPU для критических процессов (маршрутизация, сигнализация).
- Дополнительный рубеж защиты после ACL (defence-in-depth).

<!-- more -->

## Базовые параметры SSH и отключение веб-интерфейса

```cisco
no ip http server
no ip http secure-server
!
ip ssh time-out 15          ! Таймаут на установление сессии
ip ssh version 2
```

**Важно:** Отключение HTTP/HTTPS убирает дополнительные векторы атак на management plane и исключает ложные срабатывания `login block-for` от веб-сканеров.

## Настройка VTY ACL

```cisco
ip access-list standard ACL-VTY
remark === hosts ===
permit 10.20.1.10
remark === OOB net ===
permit 10.50.1.0 0.0.0.255
permit 10.50.2.0 0.0.0.255
remark === admin nets ===
permit 10.100.10.0 0.0.0.255
permit 10.100.20.0 0.0.0.255
permit 10.100.30.164 0.0.0.1     ! /31 маска в wildcard
permit 10.100.30.248 0.0.0.3     ! /30 маска в wildcard
permit 172.16.10.0 0.0.0.255
permit 198.51.100.0 0.0.0.255
deny   any log
!
line vty 0 30
access-class ACL-VTY in vrf-also
transport input ssh
```

**Ограничение:** Стандартный ACL не фильтрует по L4-порту. Это допустимо для VTY, так как `line vty` принимает только терминальные протоколы.

**Важно:** Параметр `vrf-also` обязателен при использовании Management VRF для OOB-доступа. Без него подключения через `Mgmt-intf` будут блокироваться на уровне IOS, независимо от правил ACL.

## Настройка CoPP для SNMP

ACL строится по принципу «запретить NMS, разрешить всё остальное» — CoPP дропнет трафик, не прошедший проверку.

```cisco
ip access-list extended SNMP-UNTRUSTED
deny   udp host 10.100.10.50 any eq snmp
deny   udp host 10.100.10.90 any eq snmp
deny   udp 10.100.30.0 0.0.0.255 any eq snmp
permit udp any any eq snmp
!
class-map match-all COPP-DROP-SNMP
match access-group name SNMP-UNTRUSTED
!
policy-map COPP-POLICY
class COPP-DROP-SNMP
police 8000 conform-action drop exceed-action drop
!
control-plane
service-policy input COPP-POLICY
```

**Важно:** CoPP использует «перевёрнутую» логику ACL. `deny` для NMS означает «пропускаем». `permit` для остальных — «этот трафик надо дропнуть».

## Настройка CoPP для SSH

```cisco
ip access-list extended COPP-SSH
remark === SSH to/from router ===
permit tcp any any eq 22
permit tcp any eq 22 any
!
class-map match-any COPP-SSH
match access-group name COPP-SSH
!
policy-map COPP-POLICY
class COPP-SSH
police rate 200 pps burst 100 packets conform-action transmit exceed-action drop
```

**Важно:** Класс `COPP-SSH` автоматически встраивается в `policy-map` перед `class-default`. Специфичные классы должны идти выше общего catch-all.

**Ограничение:** При вставке больших портянок (>50 строк) возможен рост счётчика `exceeded` из-за превышения burst. Это приводит к замедлению отрисовки ввода, но не к потере команд: TCP выполнит retransmit.

## Итоговая CoPP-политика

| Класс | Действие | Назначение |
|:---|---|:---|
| `COPP-DROP-SNMP` | police 8000, drop | Блокировка SNMP от неавторизованных хостов |
| `COPP-SSH` | police 200 pps, transmit/drop | Rate-limit SSH |
| `class-default` | match any (пропуск) | Весь остальной трафик без ограничений |

## Верификация

```bash
show policy-map control-plane | section COPP
show access-lists SNMP-UNTRUSTED
```

**Примечание:** Нулевое `exceeded` в штатном режиме подтверждает корректность лимита. Резкий рост `conformed` и `exceeded` — признак сканирования или флуда.
