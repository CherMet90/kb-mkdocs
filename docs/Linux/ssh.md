---
title: Работа с SSH на Ubuntu
date: 2026-03-30
---

# Работа с SSH на Ubuntu

## Создание ssh-ключей (RSA)
1. На клиенте создаем RSA-ключи. На Windows утилиты должны быть доступны через Git Bash  
```
ssh-keygen -t rsa -b 4096 -C "<коментарий>"
```  
2. Конвертируем приватный ключ в pem-формат (при необходимости)
```
ssh-keygen -p -f rundeck -m pem
```
<!-- more -->
3. Содержимое публичного ключа копируем в конец файла `~/.ssh/authorized_keys` на сервере  
4. Современные Ubuntu не разрешают авторизацию по RSA-ключам. Редактируем файл `/etc/ssh/sshd_config`. В конец файла добавляем:
```
# Если требуется глобально разрешить rsa
PubkeyAcceptedAlgorithms +ssh-rsa
# Либо разрешить ssh-rsa для определенных адресов/подсетей
Match Address 172.18.0.0/24,192.168.1.100
    PubkeyAcceptedAlgorithms +ssh-rsa
```
5. Рестарт службы ssh для применения изменений конфигурации:  
```
sudo systemctl restart sshd
```

## Решение для "WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!"

Эта ошибка возникает после переноса IP-адреса на новый инстанс, когда на клиенте в файле `~/.ssh/known_hosts` сохранен старый ключ хоста.

**Удалить старую запись из known_hosts**
```
ssh-keygen -R <IP_адрес_или_домен>
```
