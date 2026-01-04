# Настройка SNMP на коммутаторах Huawei (VRP)

**Предварительные требования:**
- Доступ к CLI коммутатора в режиме конфигурации (используйте `< >` для входа в режим просмотра, `system-view` для редактирования).
- SNMP-сервер (например, PRTG, Zabbix или Nagios) должен быть настроен и доступен.
- Убедитесь, что сеть позволяет UDP-трафик на порт SNMP (по умолчанию 161).
- Подготовьте community string (аналог пароля) для аутентификации. Избегайте простых строк, таких как "public", для безопасности.
- Знание версий SNMP: v1/v2c (нешифрованные, устаревшие) vs. v3 (с шифрованием и аутентификацией). Здесь фокус на v1/v2c, как в примере.

**Trade-offs:**
- SNMP v1/v2c прост в настройке, но передаёт данные в plaintext (риск перехвата). Рекомендуется v3 для production.
- Ограничение ACL и интерфейсов повышает безопасность, но может усложнить отладку, если правила слишком строгие.
- Включение SNMP увеличивает нагрузку на устройство (минимально), но критично для мониторинга.

## 1. Создание ACL для SNMP

Создайте ACL (Access Control List) для ограничения источников, которые могут запрашивать SNMP. Это предотвращает несанкционированный доступ.

В режиме конфигурации:

```bash
acl name SNMP 3999  # Создаёт именованный ACL с номером 3999 (диапазон advanced ACL: 3000-3999)
 rule 5 permit ip source 198.51.200.8 0  # Разрешает трафик только от указанного IP (маска 0 — точный матч). Добавьте больше правил для других серверов.
```

**Пояснение:** 
- Номер ACL (3999) — произвольный в диапазоне. Используйте `deny` для явного запрета других источников (например, `rule 10 deny ip` в конце).
- Источник — IP вашего SNMP-сервера. Для подсетей используйте маску (e.g., `source 198.51.200.0 0.0.0.255` для /24).
- ACL применяется позже к SNMP-агенту.

**Проверка:** `display acl name SNMP` для просмотра правил.

## 2. Включение и настройка SNMP-агента

Включите SNMP-агент, примените ACL, настройте community string и системную информацию. Ограничьте интерфейсы для прослушивания.

В режиме конфигурации:

```bash
snmp-agent  # Включает SNMP-агент на устройстве
snmp-agent acl 3999  # Применяет ACL для ограничения доступа (замените на ваш номер ACL)
snmp-agent community read cipher %^%#<encrypted_community_string>%^%#  # Устанавливает community string для чтения (в зашифрованном виде; укажите plaintext при вводе — система зашифрует)
snmp-agent sys-info contact <your_contact_info>  # Устанавливает контактную информацию (e.g., "admin@example.com")
snmp-agent sys-info location <your_location_info>  # Устанавливает местоположение (e.g., "Data Center Rack 5")
snmp-agent sys-info version v1 v2c  # Указывает поддерживаемые версии (v1 и v2c; добавьте v3 при необходимости)

# Ограничение интерфейсов для прослушивания SNMP
undo snmp-agent protocol source-status all-interface  # Отключает прослушивание на всех интерфейсах (IPv4)
snmp-agent protocol source-interface Vlanif3518  # Ограничивает на указанный интерфейс (замените на ваш, e.g., VlanifX)
undo snmp-agent protocol source-status ipv6 all-interface  # Отключает для IPv6 (если не используется)
```

**Пояснение:** 
- `snmp-agent community read` ограничивает на чтение (для мониторинга). Для записи добавьте `write`.
- Community string шифруется в конфигурации для безопасности. При вводе используйте plaintext — Huawei зашифрует.
- Ограничение интерфейсов (e.g., management VLAN) предотвращает экспозицию SNMP на публичных интерфейсах.
- Версии: v1/v2c совместимы с большинством инструментов, но небезопасны. Для v3 настройте пользователей с `snmp-agent usm-user v3`.

**Проверка:** `display snmp-agent sys-info` для системной информации и `display snmp-agent community` для community strings.

## Пост-настройка действия
- **Тестирование:** С SNMP-сервера выполните запрос (e.g., `snmpwalk -v 1 -c <community> -On -Cc <device_ip> 1.3.6.1.2.1.1.5.0`). Проверьте, работает ли с разрешённого IP и блокируется с других.
- **Мониторинг и логи:** Просматривайте статистику с `display snmp-agent statistics`. Включите traps для уведомлений: `snmp-agent trap enable`.
- **Безопасность:** Регулярно ротируйте community strings. Перейдите на SNMPv3 для аутентификации/шифрования: `snmp-agent usm-user v3 <user> group <group> authentication-mode sha <password> privacy-mode aes-128 <privacy_password>`.
- **Откат:** Отключите SNMP с `undo snmp-agent`. Удалите ACL с `undo acl name SNMP`.
- **Расширения:** Для уведомлений (traps) настройте `snmp-agent target-host trap address udp-domain <server_ip> params securityname <community> v2c`.