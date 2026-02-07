##### IPsec (GRE over IPsec)
В обычной ситуации достаточно создать интерфейс типа GRE Tunnel - всё необходимое будет создаваться автоматически  
Если же это не подходит, например мы хотим включить режим response-only (passive), то при создании интерфейса GRE Tunnel не задаём пароль ipsec и предварительно создаём вручную динамические сущности для тунеля:  

```
/ip ipsec peer
add name=new-peer address=X.X.X.X/32 local-address=Y.Y.Y.Y passive=yes
```
```
/ip ipsec identity
add peer=new-peer auth-method=pre-shared-key secret="ВАШ_PSK"
```
```
/ip ipsec policy
add src-address=Y.Y.Y.Y/32 dst-address=X.X.X.X/32 protocol=gre \
    action=encrypt tunnel=no peer=new-peer proposal=default
```

##### BGP
1. Создаём префикс-листы
    ```
    /routing filter rule
    add chain=bgp-in disabled=no rule=\
        "if ((dst in <принимаемый_префикс>/15) || (dst in <принимаемый_префикс>/15)) { accept }"
    ```
2. Настраиваем нашу ASN
    ```
    /routing bgp template
    set default as=<номер_локальной_asn> disabled=no router-id=<ip_адрес_роутера> routing-table=main
    ```
3. Создаём соединение с соседом
    ```
    /routing bgp connection
    add as=<номер_локальной_asn> disabled=no input.filter=bgp-in local.address=\
        <локальный_тунельный_ip> .role=ebgp name=connection-name output.network=<адрес-лист_анонсируемых_подсетей> \
        remote.address=<тунельный_ip_соесда>/32 .as=<asn_соседа> \
        templates=default
    ```
