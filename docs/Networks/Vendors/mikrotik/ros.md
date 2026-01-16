#### BGP
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
