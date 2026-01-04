*Links:*
- [Official Documentation](https://docs.docker.com/engine/security/protect-access/#use-tls-https-to-protect-the-docker-daemon-socket)
- [Stackoverflow](https://stackoverflow.com/questions/44052054/unable-to-start-docker-after-configuring-hosts-in-daemon-json)

Создаем папку под сертификаты:
```bash
mkdir /docker/certs/
```

```bash
cd /docker/certs/
```

Создаем корневой ключ и сертификат:
```bash
openssl genrsa -aes256 -out ca-key.pem 4096
```

```bash
openssl req -new -x509 -days 3650 -key ca-key.pem -sha256 -out ca.pem
```

Указываем информацию для сертификата:
```
Country Name (2 letter code) [AU]:EX
State or Province Name (full name) [Some-State]:Example
Locality Name (eg, city) []:Example City
Organization Name (eg, company) [Internet Widgits Pty Ltd]:Example Company
Organizational Unit Name (eg, section) []:Example Department
Common Name (e.g. server FQDN or YOUR name) []:example.server.com
Email Address []:example@example.com
```

```bash
openssl genrsa -out server-key.pem 4096
```

```bash
openssl req -subj "/CN=example.server.com" -sha256 -new -key server-key.pem -out server.csr
```

Делаем конфиг:
```bash
echo subjectAltName = DNS:example.server.com,IP:192.168.1.100 >> extfile.cnf
```

```bash
echo extendedKeyUsage = serverAuth >> extfile.cnf
```

Генерим сертификат сервера:
```bash
openssl x509 -req -days 3650 -sha256 -in server.csr -CA ca.pem -CAkey ca-key.pem -CAcreateserial -out server-cert.pem -extfile extfile.cnf
``` 

Генерим ключ и сертификат и ключ для клиента:
```bash
openssl genrsa -out key.pem 4096
```

```bash
openssl req -subj '/CN=client' -new -key key.pem -out client.csr
```

```bash
echo extendedKeyUsage = clientAuth > extfile-client.cnf
```

```bash
openssl x509 -req -days 3650 -sha256 -in client.csr -CA ca.pem -CAkey ca-key.pem -CAcreateserial -out cert.pem -extfile extfile-client.cnf
```

Удаляем ненужные файлы:
```bash
rm -v client.csr server.csr extfile.cnf extfile-client.cnf
```

Устанавливаем права:
```bash
chmod -v 0400 ca-key.pem key.pem server-key.pem
```

Создаем папку для переопределения демона докера:
```bash
mkdir /etc/systemd/system/docker.service.d
```

Создаем файл переопределения:
```bash
nano /etc/systemd/system/docker.service.d/docker.conf
```

И указываем в нем:
```
[Service]
ExecStart=
ExecStart=/usr/bin/dockerd
```

Далее создаем папку, если отсутствует:
```bash
mkdir /etc/docker
```

Создаем конфиг докера:
```bash
nano /etc/docker/daemon.json
```

Указываем конфиг:
```
{
    "hosts": ["unix:///var/run/docker.sock", "tcp://0.0.0.0:2376"],
    "tls": true,
    "tlscacert": "/docker/certs/ca.pem",
    "tlscert": "/docker/certs/server-cert.pem",
    "tlskey": "/docker/certs/server-key.pem",
    "tlsverify": true
}
```

Делаем reload демона:
```bash
systemctl daemon-reload
```

Перезапускаем docker:
```bash
systemctl restart docker
```

### Для систем, требующих ручной настройки файрвола
##### Пример для систем на основе iptables:
Открываем порт 2376 (используется для TLS защищенных соединений Docker):  
```
nano /etc/iptables/rules.v4
```
Добавляем правило:  
```bash
-A INPUT -p tcp -m tcp --dport 2376 -j ACCEPT
```
Применяем изменения и перезапускаем соответствующие службы (пример для Debian/Ubuntu):  
```
iptables-restore < /etc/iptables/rules.v4 && systemctl restart docker
```
Теперь Docker настроен для использования защищенного соединения, и вы можете настраивать средства мониторинга, такие как PRTG, для безопасного соединения с вашим Docker хостом.
