##### Отключение авто-обновления:  
```
config system central-management
    set allow-push-configuration disable        # запрещает изменять конфигурацию из облака (необходимость СПОРНА)
    set allow-push-firmware disable             # запрещает автоматически отправалять обновление прошивки на устройства
    set allow-remote-firmware-upgrade disable   # запрещает инициировать обновление прошивки удаленно
end

config system fortiguard
    set auto-firmware-upgrade disable   # не разрешает запрашивать обновление со стороны самого устройства
end
```  
<br>

##### Сохранение вручную  
###### Включить режим  
```
config system global
set cfg-save manual
end
```  
###### Команда сохранения  
```
exec cfg save
```

##### Управление таймаутом сессий
```
config system session-ttl
    set default 3600    # глобальное значение
    config port         # port-specific настройки
        edit 7700       # id елемента (не обязан быть равен порту)
            set protocol 6          # протокол, TCP=6, обязательный параметр
            set timeout 9000        # значение таймаута в секундах
            set start-port 7700     # задаем порты, на которые распространяется настройка
            set end-port 7700
        next
    end
```


##### RADIUS-авторизация
Предполагается, что сам radius-сервер уже добавлен  
Создаем admin-профиль:  
```
    edit "radius_user_access"
        set comments ''
        set secfabgrp read
        set ftviewgrp read
        set authgrp read
        set sysgrp read
        set netgrp read
        set loggrp read
        set fwgrp read
        set vpngrp read
        set utmgrp read
        set wifi read
        set admintimeout-override disable
        set system-diagnostics enable
        set system-execute-ssh enable
        set system-execute-telnet enable
    next
```
Создаем user-группу:  
```
    edit "RADIUS_ro"
        set group-type firewall
        set authtimeout 0
        set auth-concurrent-override disable
        set http-digest-realm ''
        set member "sw-nps"
        config match
            edit 1
                set server-name "sw-nps"
                set group-name "RADIUS_ro"
            next
        end
    next
```
Создаем админскую учетку:
```
    edit "radius ro"
        set remote-auth enable
        set trusthost1 0.0.0.0 0.0.0.0
        set trusthost2 0.0.0.0 0.0.0.0
        set trusthost3 0.0.0.0 0.0.0.0
        set trusthost4 0.0.0.0 0.0.0.0
        set trusthost5 0.0.0.0 0.0.0.0
        set trusthost6 0.0.0.0 0.0.0.0
        set trusthost7 0.0.0.0 0.0.0.0
        set trusthost8 0.0.0.0 0.0.0.0
        set trusthost9 0.0.0.0 0.0.0.0
        set trusthost10 0.0.0.0 0.0.0.0
        set ip6-trusthost1 ::/0
        set ip6-trusthost2 ::/0
        set ip6-trusthost3 ::/0
        set ip6-trusthost4 ::/0
        set ip6-trusthost5 ::/0
        set ip6-trusthost6 ::/0
        set ip6-trusthost7 ::/0
        set ip6-trusthost8 ::/0
        set ip6-trusthost9 ::/0
        set ip6-trusthost10 ::/0
        set accprofile "radius_user_access"
        set comments ''
        set vdom "root"
        set schedule ''
        set two-factor disable
        set email-to ''
        set sms-server fortiguard
        set sms-phone ''
        set guest-auth disable
        set wildcard enable
        set remote-group "RADIUS_ro"
        set accprofile-override disable
        set vdom-override disable
    next
```
<br>

##### Захват трафика CLI
```
# diagnose sniffer packet <interface> '<filter>'
diagnose sniffer packet any 'host 192.168.71.6'
```
<br>


##### Отключение приветственного окна
```
config system global
    set gui-auto-upgrade-setup-warning disable
    set gui-forticare-registration-setup-warning disable
end
```