##### Shadow session
Смотрим номер сессии (можно удаленно):  
```
qwinsta /server <имя_компа>
```
Создаем ярлык:
```
C:\Windows\System32\mstsc.exe -v <имя_компа> /shadow:<номер_сессии> /control /noConsentPrompt
```