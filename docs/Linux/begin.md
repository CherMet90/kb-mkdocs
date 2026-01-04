##### sudo WinSCP 
1. В файле `/etc/sudoers` разрешаем пользователю запуск sftp с рут-правами без запроса пароля:
```
<username> ALL=NOPASSWD: /usr/lib/openssh/sftp-server
```
2. Добавляем параметры запуска для соединения в самой программе WinSCP:
```
sudo /usr/lib/openssh/sftp-server
```
<br>

##### После первого запуска
```
sudo apt update
sudo apt upgrade
```
<br>

##### Настройка авторизации SSH
1. Создаём пользака и помещаем его в группу `sudo`:
```
sudo adduser <username>
sudo usermod -aG sudo <username>
```
* Перелогиниваемся, тестируем
2. Выключаем доступ для `root` в файле `/etc/ssh/sshd_config`:
```
PermitRootLogin no
```
* Тестируем
3. Копируем папку с ключами `~/.ssh` со старого сервера на новый
4. Правим права скопированных файлов:
```
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```
5. В `sshd_config` включаем авторизацию по ключам:
```
PubkeyAuthentication yes
```
6. Тестируем, выключаем авторизацию по паролю:
```
PasswordAuthentication no
```
<br>

##### Настройка iptables
1. Добавляем правила:
```
sudo iptables -A INPUT -i lo -j ACCEPT
sudo iptables -A INPUT -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A INPUT -p tcp -m tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -p tcp -m tcp --dport <нестандарный_порт_ssh> -j ACCEPT
sudo iptables -A INPUT -p tcp -m tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p icmp --icmp-type 8 -j ACCEPT
sudo iptables -P INPUT DROP
```
2. Тестируем, устанавливаем `netfilter-persistent`:
```
sudo apt update
sudo apt install iptables-persistent
sudo netfilter-persistent save
sudo systemctl enable netfilter-persistent
sudo systemctl start netfilter-persistent
```
3. Меняем порт ssh в `/etc/ssh/sshd_config`
4. `systemctl restart ssh.d` Тестируем ssh-подключение с новым портом
5. Находим номер и удаляем правило для 22 порта:
```
sudo iptables -L --line-numbers
sudo iptables -D INPUT 5
```
6. Тестируем, сохраняем
```
sudo netfilter-persistent save
```