---
title: "WAF for Network Engineers: From Zero to Hero"
date: 2026-09-26
---

# WAF for Network Engineers: From Zero to Hero

<!-- more -->

Курс по Web Application Firewall (WAF) для сетевых инженеров: от базового понимания HTTP/TLS до enterprise-дизайнов развёртывания WAF и эксплуатации в production.

## Для кого этот курс

Для сетевых инженеров, которые:

- уже уверенно работают с L2–L4 (routing, firewalling, VPN, load balancing);
- хотят освоить L7-безопасность и application delivery;
- проектируют или эксплуатируют DMZ, edge и публичные веб-сервисы.

WAF — это **L7 reverse proxy**, поэтому навыки в L4 (NAT, HA, SSL-termination, load balancing) переносятся напрямую. Главная новая концепция — работа с **HTTP-семантикой** (заголовки, cookie, тело запроса), а не с пакетами.

## Пререквизиты

- HTTP/1.1 (методы, заголовки, статус-коды), основы HTTPS и TLS.
- Понимание reverse proxy и load balancer (L4 vs L7).
- Базовое представление об OWASP Top 10.
- Смежные материалы KB: [nginx — SNI-роутинг](../../Утилиты/nginx.md), [Fortinet](../../Networks/Vendors/fortigate.md), [TCP](../../Networks/L4/tcp.md), [CrowdSec](../../Linux/crowdsec.md).

## Карта курса

| Этап | Тема | Статус |
|------|------|--------|
| 00 | [Основы: HTTP, TLS и безопасность приложений](00_foundations.md) | 🚧 в работе |
| 01 | [Что такое WAF и чем он не является](01_what_is_waf.md) | 🚧 в работе |
| 02 | [Режимы развёртывания WAF](02_deployment_modes.md) | 🚧 в работе |
| 03 | [SSL/TLS и WAF](03_ssl_tls.md) | 🚧 в работе |
| 04 | [Enterprise-дизайны WAF](04_enterprise_designs.md) | 🚧 в работе |
| 05 | [Политики и правила WAF](05_policies_rules.md) | 🚧 в работе |
| 06 | [Интеграции в enterprise-стек](06_integrations.md) | 🚧 в работе |
| 07 | [Эксплуатация и тюнинг](07_operations.md) | 🚧 в работе |
| 08 | [Вендоры и их особенности](08_vendors.md) | 🚧 в работе |
| 09 | [Продвинутые темы](09_advanced.md) | 🚧 в работе |
| — | [Лабораторные работы](labs.md) | 🚧 в работе |

## Как пользоваться курсом

1. Проходи этапы по порядку — каждый опирается на предыдущий.
2. Параллельно поднимай лабораторные из [labs.md](labs.md) (ModSecurity + OWASP CRS — отправная точка).
3. Конвенции оформления материалов курса описаны в [guideline](guideline.md).

## Источники

- [OWASP — Web Application Firewall](https://owasp.org/www-community/WAF)
- [OWASP Core Rule Set](https://coreruleset.org/)
- [PCI DSS Requirement 6.6](https://www.pcisecuritystandards.org/)
