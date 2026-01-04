# Настройка RADIUS на коммутаторах Huawei (VRP)

**Предварительные требования:**
- Доступ к CLI коммутатора в режиме конфигурации (используйте `< >` для входа в режим просмотра, `system-view` для редактирования).
- RADIUS-сервер (например, на базе FreeRADIUS или Windows NPS) должен быть настроен и доступен.
- Убедитесь, что сеть позволяет трафик UDP на порт RADIUS (по умолчанию 1812 для аутентификации).
- Подготовьте shared-key (общий секрет) для безопасного обмена данными между коммутатором и сервером.

## 1. Объявление RADIUS-сервера

Создайте шаблон RADIUS-сервера для определения параметров соединения. Это включает IP-адрес сервера, порт и shared-key.

В режиме конфигурации:

```bash
radius-server template default
 radius-server shared-key cipher <encrypted_shared_key>  # Замените на зашифрованный ключ
 radius-server authentication <radius_server_ip> 1812  # IP сервера и порт (по умолчанию 1812)
 undo radius-server user-name domain-included  # Удаляет суффикс домена из имени пользователя в запросах (если серверу он не требуется)
```

## 2. Настройка модели AAA

Настройте схемы аутентификации и авторизации, а также домен для применения RADIUS. Это интегрирует RADIUS с локальной аутентификацией в качестве fallback.

В режиме конфигурации:

```bash
aaa
 authentication-scheme radius-local
  authentication-mode radius local  # Сначала RADIUS, затем локальная аутентификация
 authorization-scheme radius-local
  authorization-mode if-authenticated local  # Авторизация после аутентификации, с fallback на локальную
 domain corp.example.com  # Создайте домен (замените на ваш, e.g., corp.example.com)
  authentication-scheme radius-local
  authorization-scheme radius-local
  radius-server default  # Примените шаблон RADIUS
```

**Пояснение:** 
- `authentication-scheme` определяет порядок: RADIUS как primary, локальная как secondary.
- `authorization-scheme` позволяет авторизацию после успешной аутентификации.
- Домен группирует настройки и применяется к пользователям.

**Проверка:** `display aaa configuration` или `display domain name corp.example.com`.

## 3. Настройка vendor-specific параметров на RADIUS-сервере

Для повышения прав пользователя (например, предоставления admin-привилегий) настройте vendor-specific атрибуты (VSA) на RADIUS-сервере. Huawei использует Vendor ID 2011.

- **Пример для FreeRADIUS или подобного:** В файле users добавьте атрибут, такой как `Huawei-Priv-Level = 3` (где 3 — уровень привилегий для полного доступа).
- **Пример для Windows NPS:** В политике сети добавьте Vendor-Specific атрибут с Vendor ID 2011 и атрибутом для уровня привилегий (см. скриншоты ниже).

![radius_ayytributes_vendor_specific](../../../images/radius_ayytributes_vendor_specific.jpg)
![add_vendor_specific_attribute](../../../images/add_vendor_specific_attribute.jpg)
![attribute_info_list](../../../images/attribute_info_list.jpg)
![configure_attribute_information](../../../images/configure_attribute_information.jpg)

**Пояснение:** Это позволяет серверу возвращать атрибуты, которые Huawei интерпретирует для назначения ролей. Без этого пользователи могут получить только базовый доступ

## 4. Упрощение логина (без суффикса домена)

Чтобы пользователи не вводили доменный суффикс при логине (например, просто "username" вместо "username@corp.example.com"), примените домен как административный. Это отключает локальную аутентификацию admin-аккаунтов.

```bash
domain corp.example.com admin
```

**Пояснение:** Полезно для удобства, но теряется возможность логина под локальными учетками. Если нужно, создайте отдельные домены или используйте fallback.

## 5. Включение SSH и отключение Telnet

```bash
stelnet server enable  # Включает SSH-сервер
ssh server-source -i Vlanif3518  # Ограничивает прослушивание на указанном интерфейсе (замените на ваш, e.g., VlanifX)
undo telnet server enable  # Отключает Telnet
```

**Проверка:** `display ssh server status` и `display telnet server status`.
