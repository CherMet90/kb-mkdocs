Cisco-протокол для распространении информации о сконфигурированных вланах  
* *Server* - можно конфигурировать вланы, информация распространяется по vtp
* *Client* - нельзя конфигурировать, информация о конфигурации получается только по vtp
* *Transparent* - можно конфигурировать, информация по vtp самим свичом игнорируется, но передается другим членам vtp
<br>

###### VTP advertisements содержат:  
  * VLAN ID 
  * VTP Domain Name 
  * VTP Password 
  * VTP configuration revision number 
  * VLAN configuration 
<br>

###### VTP Pruning:  
Мутная хня. Не даёт флудить бродкастом, если на свиче нет активных клиентов влана. Инфа об активных клиентах распространяется с помощью сообщений *VTP Join*.  
<br>

###### VTP v3 improvements:  
  * поддерживает вланы из диапазона 1000+
  * поддерживает private вланы
  * добавлено разделения серверных ролей на *primary* и *secondary*. *Secondary* - бэкапит информацию с primary
<br>

###### Базовая конфигурация:  
```
config t
feature vtp
vtp domain *domain-name*
vtp version {1 | 2}
vtp mode {client | server| transparent| off}
vtp file *file-name*
vtp password *password-value*
exit
```
<br>

###### Траблшутинг:  
1. `show vlan brief`  # чекнуть что на всех свичах домена одинаковые вланы
2. `show vtp status`  # чекнуть корректность роли устройства и имени vtp-домена
3. `show vtp pass`    # проверить корректность пароля