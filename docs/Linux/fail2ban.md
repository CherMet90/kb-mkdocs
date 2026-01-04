Установлен/работает ли fail2ban:  
```
sudo systemctl status fail2ban
```
Получить список заблокированных IP-адресов:  
```
sudo fail2ban-client status sshd
```
Разблокировать IP-адрес:  
```
sudo fail2ban-client set sshd unbanip YOUR_IP_ADDRESS
```