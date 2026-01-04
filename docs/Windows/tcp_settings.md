##### Тюним настройки TCP Windows для каналов с высоким delay (тестировалось на передаче SMB)
```
# Настройка SMB
Set-SmbClientConfiguration -EnableBandwidthThrottling $false  # Отключает ограничение пропускной способности SMB, позволяя использовать всю доступную полосу

# Настройки TCP
# Обязательные
netsh int tcp set global pacingprofile=always  # Активирует равномерное распределение пакетов во времени, снижая перегрузки при высоком RTT
netsh int tcp set global autotuninglevel=experimental  # Устанавливает агрессивную оптимизацию TCP-окна для высоколатентных соединений

# Второстепенные - улучшение не подтверждено
netsh int tcp set global prr=disable  # Отключает алгоритм пропорционального снижения скорости, позволяя быстрее восстанавливаться после потерь
netsh int tcp set global timestamps=enable  # Улучшает измерение времени RTT и точность повторных передач
netsh int tcp set global nonsackrttresiliency=enabled  # Повышает устойчивость при расчёте RTT без выборочного подтверждения

# Спорные
netsh int tcp set global ecncapability=enable  # Включает явное уведомление о перегрузке без отбрасывания пакетов
netsh int tcp set global rss=enable  # Включает Receive Side Scaling - распределяет обработку сетевых пакетов между ядрами CPU
```