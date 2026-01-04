### Установка драйвера на сетевую карту потребительского класса (Intel I225-V/I226-V) в Windows Server
1. Скачиваем модифицированые драйвера: https://www.quarkbook.com/wp-content/uploads/2022/11/PRO2500_Winx64_WS2022_RELEASE_29.2.zip  
2. Через F8 загружаемся в режиме без проверки подписи драйверов
3. Устанавливаем драйвер:
```
cd .\PRO2500_Winx64_WS2022_RELEASE_29.2\
pnputil.exe -i -a .\e2f.inf
```