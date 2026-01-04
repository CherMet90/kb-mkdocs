# Обновление прошивки на коммутаторах Huawei

## Шаги обновления

### 1. Загрузка файлов прошивки и патча через TFTP
Используйте TFTP для передачи файлов с сервера на коммутатор. Это обеспечивает целостность файлов по сравнению с веб-загрузкой.

Выполните команды в пользовательском режиме CLI:

```bash
tftp <ip_сервера> get <имя_файла_прошивки>  # Например: tftp 192.168.1.100 get s1720-gw_v200r022c00spc500.cc
tftp <ip_сервера> get <имя_файла_патча>    # Например: tftp 192.168.1.100 get s1720-gw_v200r022sph1b0.pat
```

**Проверка:** После загрузки используйте `dir` для подтверждения наличия файлов в хранилище коммутатора.

### 2. Установка прошивки
Задайте загруженный файл как системное ПО для следующей загрузки. Это не влияет на текущую сессию до перезагрузки.

В режиме просмотра конфигурации:

```bash
startup system-software s1720-gw_v200r022c00spc500.cc
```

Ожидаемый вывод:
```
Info: Succeeded in setting the software for booting system.
```

### 3. Установка патча
Задайте патч для применения после перезагрузки. Патч исправляет специфические проблемы в прошивке.

```bash
startup patch s1720-gw_v200r022sph1b0.pat
```

Ожидаемый вывод:
```
Info: Succeeded in setting main board resource file for system.
```

### 4. Перезагрузка устройства
Перезагрузите коммутатор для применения изменений. Система проверит конфигурацию и обновит firmware.

```bash
reboot
```

Ожидаемый вывод и взаимодействие:
```
Info: The system is now comparing the configuration, please wait.
Info: If want to reboot with saving diagnostic information, input 'N' and then execute 'reboot save diagnostic-information'.
System will reboot! Continue?[Y/N]:y
Comparing the firmware versions........................................
Warning: It will take a few minutes to upgrade firmware. Please do not switchover, reset, remove, or power off the board when upgrade is being performed. Please keep system stable...........................................................................................................
Info: Online upgrade firmware on slot 0 successfully.
Info: System is rebooting, please wait...
```

**Время выполнения:** Перезагрузка и обновление может занять несколько минут. Мониторьте консоль для прогресса.

## Пост-обновление действия
- Проверьте версию: `display version`.
- Тестируйте ключевые функции (порты, VLAN, routing).
- Если возникли проблемы, откатитесь к предыдущей прошивке: используйте `startup system-software <старая_прошивка>` и перезагрузите.
