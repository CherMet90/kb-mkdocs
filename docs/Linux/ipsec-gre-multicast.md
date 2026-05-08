---
title: IPsec GRE поверх tunnel mode для мультикаста
date: 2025-04-09
---

# IPsec GRE поверх tunnel mode для мультикаста

## Ключевые особенности

### Почему не работают подходы

| Подход | Причина несовместимости |
|--------|-------------------------|
| **VTI на Cisco** (`tunnel mode ipsec ipv4`) | P2P-туннель игнорирует IGMP Reports — только `ip igmp static-group`. Динамическая подписка невозможна |
| **XFRM-интерфейс strongSwan** | XFRM — layer-3 интерфейс **без MULTICAST**. PIM не стартует |
| **GRE + IPsec transport mode** | Из-за `1:1 NAT` в облаке strongSwan не может согласовать traffic selectors (TS_UNACCEPT). NAT искажает внутренний IP, а transport mode шифрует без внешней инкапсуляции |

### Как это решает GRE + IPsec tunnel mode

```mermaid
packet-beta
  0-31: "Внешний IP-заголовок (src=<PUB_IP_CLOUD>, dst=<PUB_IP_ONPREM>)"
  32-63: "IPsec ESP (tunnel mode)"
  64-95: "GRE-заголовок"
  96-127: "Внутренний IP-пакет (multicast)"
```

- **Tunnel mode** шифрует **весь** входящий пакет (GRE+IP) — внешний заголовок остаётся неизменным.
- **Анонсируемый TS:** публичные IP конечных точек, которые NAT не затрагивает.
- **GRE-интерфейс** в Linux по умолчанию имеет флаг `MULTICAST` — IGMP-запросы уходят через туннель нативно, без дополнительных демонов.
- **Cisco** видит IGMP-запрос от адреса `gre-corp` и создаёт динамическую подписку.

---

## Кейс: Настройка GRE over IPsec tunnel mode с мультикастом

### Исходные данные

| Параметр | Значение |
|----------|----------|
| Облачный инстанс (Ubuntu + strongSwan) | Локальный адрес: `10.99.0.3`. Публичный адрес: получен через `1:1 NAT` |
| Loopback-интерфейс на Linux | `lo:pub` — держит публичный IP (`<PUB_IP_CLOUD>`) для привязки GRE |
| On-Prem маршрутизатор | Cisco ASR1002, публичный адрес `<PUB_IP_ONPREM>` |
| Транспорт | IPsec IKEv2, PSK, tunnel mode |
| Мультикаст-группа | Например `239.1.1.1` |

**Предусловие:** базовый деплой strongSwan выполнен по инструкции [failover-vpn.md](../failover-vpn.md) — разделы «Устанавливаем пакеты», «sysctl.conf», «Служба для поднятия интерфейсов». strongSwan запущен. Остальное (GRE, loopback, swanctl) настраивается по шагам ниже.

---

### 1. Loopback-интерфейс для публичного IP

Поскольку облачный инстанс получает публичный IP через `1:1 NAT`, Linux не видит его на физическом интерфейсе (`eth0`). GRE требует локальный адрес для привязки — создаём loopback:

```bash
# Добавить публичный IP на lo
sudo ip addr add <PUB_IP_CLOUD>/32 dev lo label lo:pub
```

---

### 2. Создание GRE-интерфейса

GRE привязывается к публичным IP (не к внутренним!) для избежания проблем с NAT при IPsec-инкапсуляции.

```bash
# Создать GRE-интерфейс
sudo ip tunnel add gre-corp mode gre \
  local <PUB_IP_CLOUD> \
  remote <PUB_IP_ONPREM> \
  ttl 64

# MTU = 1500 - 20 (IP) - 4 (GRE) - 24 (ESP tunnel mode) = 1452
# В безопасном режиме: 1400 - 24 (IPsec) = 1376
sudo ip link set gre-corp mtu 1376 up

# Назначить туннельные адреса
sudo ip addr add 10.158.255.58/30 dev gre-corp
sudo ip addr add 10.158.25.2/24 dev gre-corp

# Sysctl для корректной работы мультикаста
sudo sysctl -w net.ipv4.conf.all.rp_filter=0
sudo sysctl -w net.ipv4.conf.lo.rp_filter=0
sudo sysctl -w net.ipv4.conf.gre-corp.rp_filter=0
sudo sysctl -w net.ipv4.conf.gre-corp.force_igmp_version=2

# Добавить маршруты до удалённых сетей (если нужно)
sudo ip route add <REMOTE_SUBNET>/<MASK> dev gre-corp
```

**Важно:** `rp_filter=0` отключает strict reverse path filtering на интерфейсе — исходящие IGMP-пакеты и мультикаст-трафик не отбрасываются. `force_igmp_version=2` — для совместимости со старыми IGMP-реализациями.

---

### 2.5. Systemd-юнит для автоматизации (не проверен)

Создайте unit-файл `/etc/systemd/system/ipsec-gre-interfaces.service`:

```ini
[Unit]
Description=Create IPsec GRE interfaces and loopback
After=network-online.target
Before=strongswan.service
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/sh -c '\
  ip addr add <PUB_IP_CLOUD>/32 dev lo label lo:pub 2>/dev/null; \
  ip tunnel show gre-corp >/dev/null 2>&1 || \
    (ip tunnel add gre-corp mode gre local <PUB_IP_CLOUD> remote <PUB_IP_ONPREM> ttl 64 && \
     ip link set gre-corp mtu 1376 up && \
     ip addr add 10.158.255.58/30 dev gre-corp && \
     ip addr add 10.158.25.2/24 dev gre-corp); \
  sysctl -w net.ipv4.conf.all.rp_filter=0; \
  sysctl -w net.ipv4.conf.gre-corp.rp_filter=0; \
  sysctl -w net.ipv4.conf.lo.rp_filter=0; \
  sysctl -w net.ipv4.conf.gre-corp.force_igmp_version=2'

ExecStop=/bin/sh -c '\
  ip tunnel del gre-corp 2>/dev/null; \
  ip addr del <PUB_IP_CLOUD>/32 dev lo label lo:pub 2>/dev/null'

[Install]
WantedBy=multi-user.target
```

Применение:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ipsec-gre-interfaces.service
sudo systemctl start ipsec-gre-interfaces.service
```

---

### 3. Конфигурация strongSwan (swanctl.conf)

**Ключевые изменения по сравнению с обычным XFRM-подходом:**

- `mode = tunnel`
- `local_ts / remote_ts` — селекторы с протоколом `gre`
- `if_id_in / if_id_out` — **отсутствуют** (XFRM не используется)
- `local_addrs` — внутренний адрес инстанса (`10.99.0.3`) — через него IKE ходит до маршрутизатора

```ini
# /etc/swanctl/swanctl.conf

connections {
  corp-multicast {
    version = 2
    mobike = no
    reauth_time = 28800
    dpd_delay = 30s

    local_addrs = 10.99.0.3
    remote_addrs = <PUB_IP_ONPREM>

    local {
      auth = psk
      id = <PUB_IP_CLOUD>
    }
    remote {
      auth = psk
      id = <PUB_IP_ONPREM>
    }

    children {
      corp-gre {
        mode = tunnel
        local_ts = 0.0.0.0/0[gre]
        remote_ts = 0.0.0.0/0[gre]
        life_time   = 3600s
        rekey_time  = 3300s
        dpd_action  = restart
        start_action = start
      }
    }
  }
}

secrets {
  ike-multicast {
    id = <PUB_IP_ONPREM>
    secret = "<PSK_KEY>"
  }
}
```

#### Применить конфигурацию

```bash
# Проверка синтаксиса
sudo swanctl --load-conns

# Загрузить все конфиги
sudo swanctl --load-all

# Или перезапустить службу
sudo systemctl restart strongswan
```

### 4. Изменения на Cisco ASR1002

```text
interface Tunnel15825
 ip address 10.158.255.57 255.255.255.252
 ip mtu 1376
 ip pim sparse-mode
 tunnel source <PUB_IP_ONPREM>
 tunnel mode gre ip                 ! изменение: было ipsec ipv4
 tunnel destination <PUB_IP_CLOUD>
 tunnel vrf INTERNET_DN
 tunnel protection ipsec profile PARTNER
```

**Важно:** профиль `PARTNER` должен поддерживать **tunnel mode** — обычно это значение по умолчанию для VTI/static profile. Проверить:

```text
show crypto ipsec profile PARTNER
```

**После изменений:**

```text
blr-asr1002# clear crypto sa
```

---

### 5. Проверка

| # | Команда | На узле | Ожидаемый результат |
|---|---------|---------|---------------------|
| 1 | `sudo swanctl --list-sas` | Linux | IKE_SA ESTABLISHED, CHILD_SA INSTALLED (tunnel mode) |
| 2 | `ping 10.158.255.57 -I gre-corp` | Linux | Ответы |
| 3 | `sudo tcpdump -i eth0 -n host <PUB_IP_ONPREM>` | Linux | Видны ESP-пакеты |
| 4 | `show crypto session` | ASR | Active SA |
| 5 | `ping 10.158.255.58` | ASR | Ответы |
| 6 | `sudo ip igmp join <MCAST_GROUP>` на gre-corp (или старт приложения) | Linux | |
| 7 | `show ip igmp groups Tunnel15825` | ASR | Группа отображается динамически |
| 8 | `show ip mroute <MCAST_GROUP>` | ASR | `(*,G)` с OIF Tunnel15825 |

**Тестирование IGMP join** можно выполнить с помощью `smcroute` или `mcjoin`:

```bash
# Установить mcjoin
sudo apt install mcjoin
# Запрос на присоединение к группе
mcjoin -i gre-corp <MCAST_GROUP>
```

---

### Примечания

- **Важно:** Если инстанс имеет публичный IP на eth0 (без NAT) — loopback не нужен.
- **Ограничение:** TS с `[gre]` фильтрует только GRE-трафик (protocol 47). Остальной трафик между теми же хостами шифроваться не будет, если не добавить отдельный child SA.
- **Расчёт MTU:** 1500 (физический интерфейс) - 20 (IP) - 24 (ESP tunnel mode) - 4 (GRE) = 1452. Рекомендуется установить 1376 для запаса (с учётом `tcp-mss-clamping` на промежуточных маршрутизаторах).

---

### Источники

- **Route‑based VPN (GRE + tunnel mode)** — [strongSwan Docs](https://docs.strongswan.org/docs/latest/features/routeBasedVpn.html)
- **GRE + NAT → TS_UNACCEPT** — [GitHub Discussion #1915](https://github.com/strongswan/strongswan/discussions/1915)
- **Transport mode + NAT (IKEv2 TS_UNACCEPT)** — [strongSwan Mailing List](https://lists.strongswan.org/pipermail/dev/2013-December/000852.html)
- **GRE Tunnel на IOS‑XE** — [Cisco IOS XE Tunneling](https://www.cisco.com/c/en/us/td/docs/routers/ios/config/17-x/ip-multicast/b-ip-multicast/m_imc_tunnel.html)
- **man ip-tunnel** — [man7.org](https://man7.org/linux/man-pages/man8/ip-tunnel.8.html)
- **Базовая настройка IPsec с резервированием** — [failover-vpn.md](../failover-vpn.md)