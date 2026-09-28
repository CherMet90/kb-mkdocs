---
title: "Этап 04: Enterprise-дизайны WAF"
---

# Этап 04: Enterprise-дизайны WAF

> ⏳ Черновик. Контент в разработке.

Общепринятые паттерны размещения WAF в корпоративных и публичных средах.

## План раздела

- Классическая DMZ-топология: Internet → Edge FW → DMZ (WAF) → App FW → App Servers.
- WAF + Load Balancer: WAF перед LB / после LB / WAF = LB (объединено).
- WAF + CDN: edge WAF, origin protection, риск обхода через прямой доступ к origin IP.
- Распределённый/гибридный дизайн: edge WAF (cloud) + on-prem WAF, централизованный policy plane.
- WAF для API / microservices: API Gateway + WAF, sidecar-WAF, service mesh (Istio + Envoy filters).
- Multi-datacenter: GSLB + WAF в каждом DC, active-active vs active-passive, согласованность политик.

## Постановка задачи

_Будет добавлено._

## Разбор

_Будет добавлено._

## Что мы достигли

_Будет добавлено._

## Источники

- _Добавляются по готовности._
