---
title: Mikrotik RouterOS
date: 2026-05-19
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

---
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

---

## DNS-based Policy Routing (Geo‑unblock)

Задача: направить трафик к определённым интернет‑ресурсам через альтернативный шлюз (SSTP‑туннель к другому провайдеру), чтобы обойти географические ограничения или блокировки.  
Решение основано на динамическом добавлении IP‑адресов в адрес‑лист при разрешении имён через локальный DNS роутера.

**Схема работы:**

1. Клиент отправляет DNS‑запрос (UDP/53).
2. Правило `dstnat` с действием `redirect` перехватывает запрос и отправляет на локальный DNS‑сервер RouterOS.
3. В `/ip dns static` созданы записи типа `FWD` для нужных доменов с флагом `Match Subdomain` и указанием `address-list`. При резолве роутер добавляет IP‑адрес из ответа в заданный адрес‑лист.
4. Правило `mangle` в цепочке `prerouting` помечает пакеты, у которых `dst-address` входит в этот адрес‑лист, меткой routing‑mark (например, `to-tunnel`).
5. В `/ip route` существует маршрут по умолчанию в таблице `to-tunnel`, указывающий на интерфейс SSTP‑туннеля.
6. Трафик к целевым ресурсам уходит через туннель, остальной трафик идёт через стандартный шлюз.

**Проблема:** устройства домена используют DDNS (RFC 2136) для регистрации своих имён на контроллере домена, посылая DNS UPDATE. Пакеты UPDATE перехватываются тем же `redirect`, но статические записи их не обрабатывают — регистрация ломается.  

**Решение:** с помощью Layer7‑фильтра идентифицировать DNS‑запросы типа `UPDATE` (opcode 5) и пропускать их мимо `redirect`, давая пройти напрямую к контроллеру домена.

### Настройка перенаправления трафика по доменным именам

**Исходные данные (обезличены):**

- Локальный контроллер домена: `10.0.0.10`
- SSTP‑туннель: интерфейс `sstp-out1`, удалённый шлюз `10.255.255.1`
- Целевые домены: `example-geo.com`, `another-blocked.org`
- Адрес‑лист для подмены маршрута: `unblock-hosts`
- Имя маршрутной метки: `to-tunnel`

#### Шаг 1 – DNS Static записи

```bash
/ip dns static
add name=example-geo.com type=FWD forward-to=10.0.0.10 match-subdomain=yes \
    address-list=unblock-hosts comment="Geo-unblock example"
add name=another-blocked.org type=FWD forward-to=10.0.0.10 match-subdomain=yes \
    address-list=unblock-hosts comment="Geo-unblock another"
```

**Важно:** `forward-to` указывает на ваш существующий DNS‑сервер (контроллер домена), который выполняет фактический рекурсивный запрос.

#### Шаг 2 – Mangle правило для маркировки трафика

```bash
/ip firewall mangle
add chain=prerouting dst-address-list=unblock-hosts action=mark-routing \
    new-routing-mark=to-tunnel passthrough=yes \
    comment="Маршрутизация через SSTP для unblock-hosts"
```

#### Шаг 3 – Дополнительная таблица маршрутизации и маршрут по умолчанию через туннель

```bash
/ip route
add dst-address=0.0.0.0/0 gateway=10.255.255.1 routing-table=to-tunnel \
    comment="Default route via SSTP"
```

#### Шаг 4 – Перехват DNS-запросов (redirect)

```bash
/ip firewall nat
add chain=dstnat protocol=udp dst-port=53 action=redirect \
    comment="Redirect DNS to RouterOS local server"
```

После этого трафик к IP‑адресам, которые вернул DNS для `example-geo.com` и `another-blocked.org`, пойдёт через SSTP‑туннель.

### Исключение DNS Dynamic Update из перехвата

**Проблема:** после включения `redirect` доменные устройства не могут зарегистрироваться в DNS на контроллере домена.

**Причина:** пакеты DDNS (тип `UPDATE`, opcode 5) попадают в `redirect` и не обрабатываются статикой.

**Решение:** добавить Layer7‑сигнатуру для `UPDATE` и пропускать такие пакеты до срабатывания `redirect`.

#### Шаг 1 – Создать Layer7 протокол для DNS UPDATE

```bash
/ip firewall layer7-protocol
add name=dns-update regexp="^..[()*+,./-]" comment="Detect DNS UPDATE (opcode 5)"
```

#### Шаг 2 – Разместить разрешающее правило перед redirect

```bash
/ip firewall nat
add chain=dstnat protocol=udp dst-port=53 layer7-protocol=dns-update \
    action=accept comment="Пропуск DDNS UPDATE на DC" \
    place-before=[find where action=redirect protocol=udp dst-port=53]
```

**Результат:** обычные DNS‑запросы по‑прежнему заворачиваются на локальный DNS роутера и пополняют адрес‑лист, а обновления DDNS прозрачно доходят до контроллера домена.

**Источники:**
- [MikroTik Wiki: Layer7](https://help.mikrotik.com/docs/display/ROS/Layer7)
- [RFC 2136 – Dynamic Updates in the Domain Name System](https://datatracker.ietf.org/doc/html/rfc2136)

---

## WireGuard (гостевой доступ с белым списком)

Каждый экземпляр WireGuard на роутере слушает **свой UDP‑порт** и изолирован от других интерфейсов.  
Для гостей/подрядчиков заводят выделенный интерфейс, чтобы:

- не смешивать их трафик с сотрудниками и облачным доступом,
- управлять белым списком через отдельную цепочку firewall,
- при необходимости быстро отключить всю гостевую подсеть одним правилом.

Каждому гостю выделяется **персональный IP с маской /32** — запрещает подмену source‑IP внутри туннеля.  
Разрешённые ресурсы описываются **адрес‑листами**, что упрощает добавление новых гостей (один peer + правило под новый source‑IP без дублирования dst‑адресов).

### Настройка гостевого WireGuard‑сервера (RDP-доступ подрядчику)

**Исходные данные (обезличены):**

- Публичный IP роутера: `198.51.100.1`
- Гостевая WireGuard-подсеть: `10.255.250.0/24`
- Выбранный порт: `13232` (должен отличаться от портов других WireGuard-интерфейсов)
- Целевой RDP-сервер: `192.168.100.5`
- DNS-сервер для гостей: `192.168.100.1`
- WAN-интерфейс: `ether1`

#### Шаг 1 – Создание интерфейса и назначение IP

```bash
/interface wireguard
add name=wg-guests listen-port=13232 comment="Guest WG server"

/ip address
add address=10.255.250.1/24 interface=wg-guests comment="Guest WG subnet"
```

**Важно:** каждая пара ключей (private/public) генерируется автоматически. Посмотреть публичный ключ сервера — `:put [/interface wireguard get wg-guests public-key]`.

#### Шаг 2 – Открытие порта в chain=input

```bash
/ip firewall filter
add action=accept chain=input dst-port=13232 protocol=udp comment="Allow WireGuard guests" place-before=1
```

**Важно:** правило должно оказаться выше всех `drop`-правил в цепочке `input`.

#### Шаг 3 – Address‑листы для разрешённых ресурсов

```bash
/ip firewall address-list
add address=192.168.100.5 list=guest-rdp-servers comment="RDP Terminal Server"
add address=192.168.100.1 list=guest-dns comment="DNS server"
```

#### Шаг 4 – Цепочка guest-fwd и разрешающие правила

```bash
/ip firewall filter
# Прыжок из forward для всей гостевой подсети
add chain=forward src-address=10.255.250.0/24 action=jump jump-target=guest-fwd comment="Jump guest traffic"
```

**Примечание:** цепочка `guest-fwd` создастся автоматически при добавлении этого правила. Отдельно объявлять её (`/ip firewall filter add chain=guest-fwd`) не требуется.

```bash
/ip firewall filter
# Каждый гость — свой комплект разрешений (src-address уникален)
add chain=guest-fwd src-address=10.255.250.11 dst-address-list=guest-rdp-servers protocol=tcp dst-port=3389 action=accept comment="Allow RDP for guest #1"
add chain=guest-fwd src-address=10.255.250.11 dst-address-list=guest-dns protocol=udp dst-port=53 action=accept comment="Allow DNS UDP for guest #1"
add chain=guest-fwd src-address=10.255.250.11 dst-address-list=guest-dns protocol=tcp dst-port=53 action=accept comment="Allow DNS TCP for guest #1"

# В конце цепочки — запрет всего остального
add chain=guest-fwd action=drop comment="Drop all other guest traffic"
```

**Важно:** на каждого следующего гостя добавляется новый peer (см. шаг 5) и аналогичные три правила с его уникальным `src-address`.

#### Шаг 5 – Добавление гостя (peer)

```bash
/interface wireguard peers
add interface=wg-guests \
    public-key="<ПУБЛИЧНЫЙ_КЛЮЧ_КЛИЕНТА>" \
    allowed-address=10.255.250.11/32 \
    comment="Гость Иванов, RDP-доступ"
```

**Важно:** `allowed-address=.../32` жёстко привязывает этого пира к одному IP. Без этого гость может заявить любой адрес из подсети.

#### Шаг 6 – Запрет доступа гостей к самому роутеру

```bash
/ip firewall filter
add action=drop chain=input src-address=10.255.250.0/24 comment="Guests must not access router"
```

**Ограничение:** если гостям нужен DNS‑сервер самого роутера (`10.255.250.1`), разместите разрешающее правило для UDP/53 к `10.255.250.1` выше этого drop.

#### Шаг 7 – (Опционально) NAT для выхода гостей в интернет

```bash
/ip firewall nat
add chain=srcnat src-address=10.255.250.0/24 out-interface=ether1 action=masquerade comment="NAT for guests"
```

Если интернет гостям не нужен — правило не добавляйте.

#### Пример клиентского конфига (выдаётся гостю)

```ini
[Interface]
PrivateKey = <ПРИВАТНЫЙ_КЛЮЧ_КЛИЕНТА>
Address = 10.255.250.11/32
DNS = 192.168.100.1

[Peer]
PublicKey = <ПУБЛИЧНЫЙ_КЛЮЧ_ВАШЕГО_СЕРВЕРА>
Endpoint = 198.51.100.1:13232
AllowedIPs = 10.255.250.0/24, 192.168.100.5/32, 192.168.100.1/32
PersistentKeepalive = 25
```

**Примечание:** `AllowedIPs` на клиенте перечисляет только те подсети/IP, которые вы фактически разрешили в цепочке `guest-fwd`. Клиент не сможет маршрутизировать ничего другого через туннель.

**Источники:**
- [MikroTik Wiki: WireGuard](https://help.mikrotik.com/docs/display/ROS/WireGuard)
- [MikroTik Wiki: Firewall Filter](https://help.mikrotik.com/docs/display/ROS/Filter)
- [MikroTik Wiki: Address Lists](https://help.mikrotik.com/docs/display/ROS/Address-lists)