#### Минимальный рабочий конфиг ASR IOS XE (classic record)
```
flow exporter <EXPORTER-NAME>
 destination <ip_netflow_коллектора>
 transport udp <порт_netflow_коллектора>
 template data timeout 60   # пока коллектор не получит шаблон, он не сможет парсить получаемые данные

flow monitor <MON-NAME>
 exporter <EXPORTER-NAME>
 record netflow-original    # выбор шаблона собираемых полей

interface <IF-NAME>
 ip flow monitor <MON-NAME> input   # вешаем на трафик, который терминируется на интерфейсе
```
`sh flow exporter <EXPORTER-NAME>` покажет `Source IP address`, если необходимо