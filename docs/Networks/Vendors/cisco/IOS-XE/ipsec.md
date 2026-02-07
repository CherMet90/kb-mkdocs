# IPsec VPN на Cisco IOS-XE (IKEv2)

## Общая архитектура компонентов

### Control Plane — IKEv2

```mermaid
graph TD
    A[ikev2 proposal<br>• encryption<br>• integrity/PRF<br>• DH group] -->|множество в политике| B[ikev2 policy<br>• match fvrf / local-address<br>• список proposal + порядок]

    K[ikev2 keyring<br>• peer address / hostname<br>• pre-shared-key] --> D[ikev2 profile<br>• match identity / address<br>• authentication pre-share / rsa-sig<br>• identity local<br>• keyring reference<br>• lifetime / DPD]

    B -->|"глобальный scope<br>выбирается автоматически"| D

    classDef proposal fill:#e6f3ff,stroke:#0066cc
    classDef policy fill:#fff3e6,stroke:#cc6600
    classDef keyring fill:#e6ffe6,stroke:#006600
    class A proposal
    class B policy
    class K keyring
```

### Data Plane — IPsec

```mermaid
graph LR
    TS[ipsec transform-set<br>• esp-aes / esp-gcm<br>• esp-sha256-hmac / null<br>• mode tunnel / transport] -->|ссылка| PR[ipsec profile<br>• set transform-set<br>• set pfs groupX<br>• set security-association lifetime<br>• set ikev2-profile <name>]

    TUN[Virtual-Template / Tunnel<br>• ip address / unnumbered<br>• tunnel source<br>• tunnel destination / mode dynamic<br>• tunnel protection ipsec profile <name>] --> PR

    classDef ts fill:#fff0f5,stroke:#c71585
    classDef profile fill:#f0fff0,stroke:#228b22
    class TS ts
    class PR profile
```

## Последовательность настройки (рекомендуемый порядок)

1. **ikev2 proposal** — определяем крипто-алгоритмы (можно переиспользовать)
2. **ikev2 policy** — задаём match-условия и упорядоченный список proposal  
   > Важно: более специфичная политика (например, с `match local-address`) имеет приоритет
3. **ikev2 keyring** — пары peer → PSK (или сертификаты)
4. **ikev2 profile** — основной блок сопоставления, аутентификации, DPD, lifetime  
   > Обязательно указать `match identity remote` и `authentication`
5. **ipsec transform-set** — алгоритмы шифрования и целостности для фазы 2
6. **ipsec profile** — связывает transform-set, PFS, lifetime и **обязательно** ikev2-profile
7. **интерфейс Tunnel** — `tunnel protection ipsec profile <имя>`

> **Примечание**: transform-set, proposal и policy можно (и нужно) переиспользовать между несколькими туннелями.

## Полезные команды отладки

```bash
show crypto ikev2 sa
show crypto ipsec sa
show crypto ikev2 profile
show crypto ikev2 policy
debug crypto ikev2
```
