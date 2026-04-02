---
title: Работа с Docker на Ubuntu
date: 2026-04-02
---

# Работа с Docker на Ubuntu

## Установка Docker
Команда для установки через официальный скрипт:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

## Базовые практики

### Используйте Docker Compose
Всегда используйте `docker compose` вместо одиночных `docker run` команд. Это обеспечивает:  
- Воспроизводимость конфигурации
- Управление зависимостями между сервисами
- Простоту развертывания на других серверах

### Проекты размещайте в /opt
Все docker-проекты разворачивайте в папке `/opt`:
```bash
sudo mkdir -p /opt/<project-name>
```
<!-- more -->
### Ограничение размера логов
Глобально ограничьте рост лог-файлов контейнеров. Создайте конфиг daemon:
```bash
sudo cat > /etc/docker/daemon.json <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "5",
    "compress": "true"
  },
  "log-level": "warn"
}
EOF
sudo systemctl restart docker
```
**Параметры:**  
- `max-size` — максимальный размер одного лог-файла (10 MB)
- `max-file` — количество хранимых файлов (5 шт.)
- `compress` — сжатие старых логов


## Остановка и очистка Docker

**Step 1: Stop All Running Containers**  
First, stop all the currently running Docker containers:
```
docker stop $(docker ps -q)
```
**Step 2: Remove All Containers**  
Then, remove all Docker containers:
```
docker rm $(docker ps -a -q)
```
**Step 3: Prune Docker System**  
Next, clean up (prune) your Docker system, which will remove all stopped containers, unused networks, images, and cached layers:
```
docker system prune -a
```
**Step 4: Confirm the Cleanup**  
You can confirm the cleanup by listing any remaining containers and images (both should show nothing):
```
docker ps -a
docker images
```
**Combined Commands**  
For convenience, you can combine these commands into a single command sequence:
```
docker stop $(docker ps -q) && docker rm $(docker ps -a -q) && docker system prune -a -f
```
**Notes:**  
- **Volumes**: If you want to also remove all unused volumes, you can use `docker system prune --volumes`, but remember this will also delete any data stored in those volumes permanently.  


## Извлечение данных: работа с файлами
Часто возникает необходимость извлечь файлы из Docker-окружения. Важно различать источник: **контейнер** (актуальное состояние исполнения) или **образ** (исходный шаблон).

### 1. Из контейнера (Recovery/Debugging)
Используется, когда данные не были вынесены на хост через `volumes` или `bind mounts`.

*   **Назначение**: Экстренное извлечение логов, дампов БД или конфигов, которые были изменены или созданы в процессе работы контейнера.
*   **Trade-off**: **Антипаттерн.** Если вы используете этот метод для получения конфигов, которые вы правили внутри контейнера — значит, у вас не настроены `volumes`. В случае удаления контейнера все эти изменения будут потеряны.

```bash
docker cp <container_id>:<абсолютный_путь_в_контейнере> <путь_на_хосте>
```
*Пример:*
```bash
docker cp 2d22e790546b:/home/rundeck/server/config/log4j2.properties ./log4j.properties
```

### 2. Из образа (Initialization/Template Extraction)
Используется на этапе первичной настройки сервиса.

*   **Назначение**: Получение "дефолтных" файлов конфигурации (например, `nginx.conf`, `haproxy.cfg`) из образа. Вы достаете файл, чтобы изучить его структуру, изменить под свои нужды и затем подключить к контейнеру через `volumes`.
*   **Trade-off**: Одноразовая процедура. После того как файл скопирован на хост, его нужно монтировать в контейнер через `volumes:`, иначе изменения не будут применены.

```bash
# Запускаем временный контейнер, монтируем текущую папку и копируем файл
docker run --rm --entrypoint sh -v "$(pwd)":/dest <image_name> -c 'cp /path/to/file /dest'
```
*Пример:*
```bash
docker run --rm --entrypoint sh -v "/docker/data/haproxy/":/dest haproxy -c 'cp /usr/local/etc/haproxy/haproxy.cfg /dest'
```


## Настройка подсети в docker compose

```
services:
  <service_name>:
    networks:
      - <network_name>

networks:
  <network_name>:
    driver: bridge
    ipam:
      config:
        - subnet: 172.18.0.0/24
          gateway: 172.18.0.1
```
