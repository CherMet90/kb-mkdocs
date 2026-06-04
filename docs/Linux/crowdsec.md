---
title: CrowdSec
date: 2026-06-04
---

# CrowdSec

CrowdSec — система обнаружения и предотвращения атак, аналогичная fail2ban, но с централизованным обменом данными о нарушителях. Блокировка реализуется через bouncer (iptables/nftables), который добавляет IP нарушителей в ipset.

## Кейс: диагностика и снятие блокировки IP

Когда до сервера доходят пакеты (`tcpdump` видит SYN), но ответа нет и демон (например, sshd) не регистрирует попытки — возможно, IP заблокирован CrowdSec.

### 1. Проверка активных решений (банов)

```bash
sudo cscli decisions list
```

Вывод покажет заблокированные IP, причину и оставшееся время.

### 2. Просмотр ipset

```bash
sudo ipset list crowdsec-blacklists-0
sudo ipset list crowdsec-blacklists-1
```
<!-- more -->
### 3. Снятие бана по IP

```bash
sudo cscli decisions delete -i <IP>
```

После удаления IP мгновенно исключается из ipset, и трафик снова разрешён.

**Важно:** если причина бана — `ssh-slow-bf` (медленный перебор), а IP используется легитимно (например, SSH‑туннель без ключа), достаточно однократно разблокировать и настроить аутентификацию по ключу, чтобы избежать повторной блокировки.

---

**Источники:**

- [CrowdSec: decisions management](https://docs.crowdsec.net/u/user_guides/decisions_mgmt/)
- [CrowdSec: unban IP](https://discourse.crowdsec.net/t/unblock-ip-from-firewall-bouncer/1039)