#### Настройка flow-коллектора (nfdump / nfcapd)

nfcapd — демон-коллектор, nfdump — инструмент анализа.

##### Установка (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install nfdump
```

##### Создание папки
```
sudo mkdir -p /var/log/netflow
sudo chown $USER:$USER /var/log/netflow
```

##### Запуск nfcapd как сервиса
```
sudo nfcapd -D -p 2055 -w /var/log/netflow -t 14400 # параметр указывает периодичность в секундах (4 часа в данном примере), с которой будут сохранятся файлы
```

##### Примеры анализа с nfdump
```
# Топ-10 источников по байтам за последний файл
nfdump -r /var/netflow/nfcapd.* -s srcip/bytes -n 10

# Фильтр по порту 443
nfdump -r /var/netflow/nfcapd.* 'port 443' -s record -n 20
```
