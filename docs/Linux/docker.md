##### Остановить все docker-контейнеры, удалить всю неиспользуемую инфу
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
* **Volumes**: If you want to also remove all unused volumes, you can use `docker system prune --volumes`, but remember this will also delete any data stored in those volumes permanently.  


##### Как скопировать файл из запущенного КОНТЕЙНЕРА в локальную фс
```
docker cp <container_id>:<абсолютный_путь_до_файла_в_контейнере> <путь_КУДА_СОХРАНИТЬ_в_локальной_фс>
```
*Пример:*
```
docker cp 2d22e790546b:/home/rundeck/server/config/log4j2.properties ./log4j.properties
```
Файл `log4j.properties` будет сохранен из контейнера `2d22e790546b` в папку, откуда запущена команда  


##### Как скопировать файл из ОБРАЗА в локальную фс  
```
docker run --rm --entrypoint sh -v "<путь_до_локальной_папки>":/<имя_временной_папки> <имя_образа> -c 'cp <что_копируем> <имя_временной_папки>'
```
*Пример:*  
```
docker run --rm --entrypoint sh -v "/docker/data/haproxy/":/dest haproxy -c 'cp /usr/local/etc/haproxy/haproxy.cfg /dest'
```
*Что происходит:*  
Запускается контейнер на основе указанного образа. Локальная папка `/docker/data/haproxy/` монтируется в созданный контейнер. Выполняется произвольная команда, в нашем случае `cp /usr/local/etc/haproxy/haproxy.cfg /dest`, контейнер останавливается и удаляется. В результате `/usr/local/etc/haproxy/haproxy.cfg` из контейнера будет скопирован в локальную папку `/docker/data/haproxy/`


##### Настройка подсети в docker compose
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