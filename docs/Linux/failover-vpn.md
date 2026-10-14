---
title: Деплой IPsec на Ubuntu с резервированием
date: 2026-10-14
---

# Деплой IPsec на Ubuntu с резервированием

## Схема

```mermaid
graph LR
    subgraph Cloud["Cloud Instance (Ubuntu + FRR)"]
        IP1["172.16.0.1<br/>ipsec1 — BGP"]
        IP2["172.16.1.1<br/>ipsec2 — Static"]
    end

    IP1 -->|основной| DC1[("DC1<br/>AS65000")]
    IP2 -.->|резервный<br/>metric 250| DC2[("DC2<br/>AS65000")]

    style IP1 fill:#90EE90,stroke:#2E7D32
    style IP2 fill:#FFE4B5,stroke:#E65100
```
<!-- more -->
| Подсеть / IP | Роль |
|-------------|------|
| `10.10.10.0/24` | Локальная сеть инстанса (анонсируется в BGP) |
| `172.16.0.0/31` | Туннель 1 — основной (BGP пир: `.0`) |
| `172.16.1.0/31` | Туннель 2 — резервный (Static next-hop: `.0`) |
| `192.168.0.0/24` | Сеть назначения за туннелями (On-Prem) |

**Failover:** при падении BGP-сессии маршрут переключается на статический (metric 250).

## Устанавливаем пакеты

```bash
sudo apt update && sudo apt install -y \
  charon-systemd \
  strongswan-swanctl \
  strongswan-libcharon \
  libstrongswan-standard-plugins \
  frr \
  frr-pythontools \
  iproute2 \
  tcpdump
```

**Важно:** метапакет `strongswan` намеренно не ставим. В Ubuntu 24.04 он зависит от legacy-бэкенда (`strongswan-charon` + `strongswan-starter`, конфиг `/etc/ipsec.conf`) и **не** создаёт systemd-юнит `strongswan.service` — `systemctl enable strongswan` падает с «Unit strongswan.service not found». Юнит и демон `charon-systemd` даёт одноимённый пакет, а `/etc/swanctl/` и утилиту `swanctl` — `strongswan-swanctl`.

Проверка, что legacy не приехал:

```bash
apt list --installed 2>/dev/null | grep -E "charon|strongswan"
# Ожидаем: charon-systemd, libstrongswan, libstrongswan-standard-plugins,
# strongswan-libcharon, strongswan-swanctl
# Не должно быть: strongswan-charon, strongswan-starter
```

Если legacy на хосте уже стоял (например, до переустановки) — он должен быть выключен: два `charon` подерутся за UDP/500, 4500 и XFRM.

```bash
sudo systemctl disable --now strongswan-starter
sudo apt purge --auto-remove strongswan strongswan-charon strongswan-starter
```

**Важно:** если в системе есть митигация LPE, запрещающая загрузку `esp4` (`/etc/modprobe.d/blacklist-lpe.conf` — её создаёт, в частности, тулинг Yandex Cloud), то IKE_SA поднимется, а CHILD_SA — нет:

```text
[KNL] received netlink error: Requested type not found (93)
[IKE] unable to install inbound and outbound IPsec SA (SAD) in kernel
[IKE] failed to establish CHILD_SA, keeping IKE_SA
```

Со стороны Cisco это выглядит как пустая ошибка `IKEv2-ERROR` без деталей — в ответ уходит `NO_PROPOSAL_CHOSEN`.

```bash
# Что перекрывает загрузку модулей. В норме вывод пустой
modprobe -c | grep -E "^install (esp4|esp6)"
lsmod | grep -E "esp4|esp6"
# Фикс CVE-2026-43284 / CVE-2026-43500 есть в 24.04 LTS начиная с 6.8.0-124
uname -r
sudo mv /etc/modprobe.d/blacklist-lpe.conf /etc/modprobe.d/blacklist-lpe.conf.disabled
sudo modprobe esp4 esp6
```

**Ограничение:** снимать митигацию безопасно только если ядро не ниже исправленной версии. Иначе сначала обновить ядро.

## sysctl.conf

```bash
cat <<EOF | sudo tee /etc/sysctl.d/99-ipsec.conf
net.ipv4.ip_forward = 1
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
net.ipv6.conf.lo.disable_ipv6 = 1
EOF
sudo sysctl --system
```

## Служба для поднятия интерфейсов

```ini
# /etc/systemd/system/ipsec-xfrm-interfaces.service
# Предварительно проверяем название интерфейса инстанса, возможно его нужно будет зафиксировать через netplan

[Unit]
Description=Create IPsec XFRM interfaces
After=network-online.target
Before=strongswan.service
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/sh -c '\
  (ip link show ipsec1 >/dev/null 2>&1 || (ip link add ipsec1 mtu 1400 type xfrm dev eth0 if_id 1 && ip addr add 172.16.0.1/31 dev ipsec1 && ip link set ipsec1 up)) && \
  (ip link show ipsec2 >/dev/null 2>&1 || (ip link add ipsec2 mtu 1400 type xfrm dev eth0 if_id 2 && ip addr add 172.16.1.1/31 dev ipsec2 && ip link set ipsec2 up))'

ExecStop=/bin/sh -c '\
  ip link del ipsec1 2>/dev/null; \
  ip link del ipsec2 2>/dev/null'

[Install]
WantedBy=multi-user.target
```

**Важно:** не возвращать в `Before=` токен `frr.service`. У FRR есть `Before=network.target`, а юнит упорядочен после `network-online.target` → ordering-цикл (`frr → network.target → network-online.target → юнит → frr`), и systemd молча удаляет задание `frr.service/start` при загрузке: FRR не стартует, в `journalctl -b` — `Found ordering cycle`. `systemd-analyze verify` циклы **не** проверяет.


## Создаём конфиг для strongswan
```conf
# /etc/swanctl/swanctl.conf
# Представлен вариант конфига с использованием общих для разных соединений настроек

conn-defaults {
  local_addrs = <INSTANCE-INTERNAL-IP>

  remote {
    auth = psk
  }

  local {
    id = <INSTANCE-PUB-IP>
    auth = psk
  }

  version = 2
  mobike = no
  proposals = aes256-sha256-prfsha256-modp2048
  dpd_delay = 30s
  rekey_time = 23h
  rand_time  = 5m
}

child-defaults {
  local_ts  = 0.0.0.0/0
  remote_ts = 0.0.0.0/0

  life_time  = 1800s
  rekey_time = 1620s
  rand_time  = 60s

  start_action = start
  close_action = restart
  dpd_action   = restart

  esp_proposals = aes256-sha1-modp2048,aes256-sha256-modp2048
}

connections {
  DC1 : conn-defaults {
    remote_addrs = <ONPREM-PUB-IP1>

    if_id_in  = 1
    if_id_out = 1

    remote {
      id = <ONPREM-PUB-IP1>
    }

    children {
      child : child-defaults {}
    }
  }

  DC2 : conn-defaults {
    remote_addrs = <ONPREM-PUB-IP2>

    if_id_in  = 2
    if_id_out = 2

    remote {
      id = <ONPREM-PUB-IP2>
    }

    children {
      child : child-defaults {}
    }
  }
}

secrets {

     ike-1 {
         id = <ONPREM-PUB-IP1>
         secret = "<secret-key>"
	}
     ike-2 {
         id = <ONPREM-PUB-IP2>
         secret = "<secret-key>"
	}
}

```

## Команды

```bash
# Проверяем синтаксис
systemd-analyze verify /etc/systemd/system/ipsec-xfrm-interfaces.service
# Загружаем конфиги
sudo systemctl daemon-reload
# Запускаем службу
sudo systemctl start ipsec-xfrm-interfaces.service
# Проверяем. Должны подняться интерфейсы ipsec1 и ipsec2
ip a
# Проверяем статус. Должно быть active (exited)
systemctl status ipsec-xfrm-interfaces.service
# Добавляем службы в автозагрузку
sudo systemctl enable ipsec-xfrm-interfaces.service
sudo systemctl enable strongswan

# Проверяем конфиг на наличие синтаксических ошибок
sudo swanctl --load-conns
# Загружаем конфиг
sudo swanctl --load-all
# Смотрим статус соединений
sudo swanctl --list-sas
# Тунельные адреса должны начать пинговаться
```

## FRR

```bash
# Включаем BGP
sudo sed -i 's/bgpd=no/bgpd=yes/' /etc/frr/daemons
# Перезапускаем и добавляем службу в автозагрузку
sudo systemctl restart frr
sudo systemctl enable frr
# Заходим в консоль конфигурации frr
sudo vtysh
```
```text
conf t
# Статический маршрут через резервный туннель (ipsec2)
ip route 192.168.0.0/24 172.16.1.0 250
!
# BGP на основном туннеле (ipsec1)
router bgp 65001
 bgp router-id 172.16.0.1
 bgp log-neighbor-changes
 no bgp ebgp-requires-policy
 neighbor 172.16.0.0 remote-as 65000
 !
 address-family ipv4 unicast
  # Есть сомнения, что здесь можно ограничить аноснируемые подсети. По факту анонсируются все подсети известные подчети, кроме 0.0.0.0/0
  network 10.10.10.0/24
  neighbor 172.16.0.0 soft-reconfiguration inbound
 exit-address-family
!
 # Если нужен BFD для быстрой сходимости
 neighbor 172.16.0.0 bfd
exit
!
bfd
 peer 172.16.0.0
 exit
!
end
wr
```

## Источники

- **strongSwan — charon-systemd** (имя юнита `strongswan`) — [docs.strongswan.org](https://docs.strongswan.org/docs/latest/daemons/charon-systemd.html)
- **strongSwan — Installation**: в Debian/Ubuntu вместо метапакета ставятся `charon-systemd` + `strongswan-swanctl` — [docs.strongswan.org](https://docs.strongswan.org/docs/latest/install/install.html)
- **CVE-2026-43284** (xfrm-ESP, «Dirty Frag») — [ubuntu.com/security](https://ubuntu.com/security/CVE-2026-43284)
- **CVE-2026-43500** (RxRPC, «Dirty Frag») — [ubuntu.com/security](https://ubuntu.com/security/CVE-2026-43500)