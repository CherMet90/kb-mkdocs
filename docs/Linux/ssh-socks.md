---
title: SOCKS5‑прокси через SSH-туннель
date: 2026-06-04
---

# SOCKS5‑прокси через SSH-туннель

SSH‑туннель в режиме Dynamic Forwarding (`-D`) позволяет превратить удалённый SSH‑хост в SOCKS5‑прокси без установки дополнительных сервисов. Приложения направляют трафик на `localhost:1080`, а SSH‑клиент пробрасывает его через зашифрованное соединение к удалённой машине, которая уже выпускает запросы в сеть.

## Кейс: постоянный SOCKS5‑прокси для сервиса

Когда SOCKS5 нужен не разово, а постоянно (например, для `mtg`), SSH‑туннель оформляется в виде systemd‑сервиса с входом по ключу (без пароля).

### 1. SSH-ключ

```bash
# Создать пару ключей без парольной фразы (если ещё нет)
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""
```

Публичный ключ (`~/.ssh/id_ed25519.pub`) добавить на удалённый сервер:

```bash
# На удалённом сервере
mkdir -p ~/.ssh && chmod 700 ~/.ssh
echo "ssh-ed25519 AAAAC3..." >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

**Важно:** вход по ключу обязателен — systemd‑сервис не может вводить пароль интерактивно.
<!-- more -->
### 2. Проверка входа без пароля

```bash
ssh -i ~/.ssh/id_ed25519 -o BatchMode=yes user@remote-host echo OK
```

Ожидаемый вывод: `OK`.

### 3. systemd-юнит

```ini title="/etc/systemd/system/ssh-socks5.service"
[Unit]
Description=SSH SOCKS5 tunnel
After=network.target

[Service]
Type=simple
User=localuser
Environment=HOME=/home/localuser
ExecStart=/usr/bin/ssh -N \
  -D 127.0.0.1:1080 \
  -i /home/localuser/.ssh/id_ed25519 \
  -o BatchMode=yes \
  -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=60 \
  -o StrictHostKeyChecking=accept-new \
  user@remote-host -p 22
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

- `BatchMode=yes` — исключает любые интерактивные запросы; если ключ не работает, сервис упадёт явно.
- `StrictHostKeyChecking=accept-new` — автоматически принимает ключ хоста при первом подключении (удобно для автоматизации).

### 4. Запуск и проверка

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ssh-socks5
systemctl status ssh-socks5

# Проверить, что порт 1080 слушается
ss -tlnp | grep 1080

# Протестировать SOCKS5
curl --socks5 127.0.0.1:1080 https://ifconfig.me
```

**Ограничение:** если на удалённом сервере настроен CrowdSec/fail2ban, частые неудачные попытки SSH могут привести к блокировке IP. Перед запуском сервиса убедитесь, что ключевая аутентификация работает стабильно.

---

**Источники:**

- [mtg issue #524 (использование simple-run с SOCKS5)](https://github.com/9seconds/mtg/issues/524)