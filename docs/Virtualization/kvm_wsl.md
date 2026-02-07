# Работа с виртуализацией KVM в WSL2

Эта статья описывает базовую работу с гипервизором KVM/QEMU в среде Windows Subsystem for Linux 2 (WSL2). Материал ориентирован на системных администраторов среднего уровня и фокусируется на практических командах, утилитах, логике выбора подходов и особенностях работы в WSL2.

## Предварительные требования

- Windows 10/11 с включённой функцией WSL2.
- Включена аппаратная виртуализация в BIOS/UEFI (Intel VT-x/AMD-V с EPT/RVI).
- Достаточно оперативной памяти (рекомендуется ≥16 ГБ на хосте).

## Этап 1: Установка и начальная настройка KVM

### Проверка поддержки виртуализации

```bash
grep -E --color=auto 'vmx|svm' /proc/cpuinfo
```

Вывод должен содержать флаги `vmx` (Intel) или `svm` (AMD). Если ничего не выводится — виртуализация недоступна в WSL2.

Проверьте модуль KVM:

```bash
lsmod | grep kvm
```

Должны быть загружены `kvm_intel` или `kvm_amd` и `kvm`.

### Установка пакетов

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y qemu-kvm qemu-utils libvirt-daemon-system \
                    libvirt-clients bridge-utils virt-manager
```

- `qemu-kvm` и `qemu-utils` — основной гипервизор и утилиты.
- `libvirt-daemon-system` + `libvirt-clients` — сервис управления виртуальными машинами и CLI-утилита `virsh`.
- `virt-manager` — опциональный графический менеджер (работает через X11-forwarding или RDP).
- `bridge-utils` — для работы с bridge-интерфейсами (если потребуется).

### Настройка прав доступа

```bash
sudo adduser $USER kvm
sudo adduser $USER libvirt
```

После этого **обязательно перезапустите сессию WSL** (закройте и откройте терминал), иначе права не применятся.
## Файловая структура и организация рабочего пространства

Правильная организация файлов упрощает работу, резервное копирование и перенос образов между системами.

### Рекомендуемая структура

```text
~/vm/                      # Основная директория для всех виртуальных машин (в домашнем каталоге)
├── images/                # Готовые и рабочие образы дисков
│   ├── pfsense.qcow2
│   ├── ubuntu-server.qcow2
│   └── windows10.qcow2
├── iso/                   # Установочные образы (.iso, .img)
│   ├── pfSense-CE-memstick-serial-2.7.2-RELEASE-amd64.img
│   ├── ubuntu-24.04-live-server-amd64.iso
│   └── windows11.iso
├── xml/                   # XML-определения для libvirt (исходники)
│   ├── pfsense.xml
│   └── ubuntu-server.xml
└── snapshots/             # Снимки состояния (если используете qemu-img snapshot)
    └── pfsense-snapshot1.qcow2
```

**Почему именно так:**

| Директория       | Что хранить                                      | Почему здесь                                   | Альтернативы / замечания                              |
|------------------|--------------------------------------------------|------------------------------------------------|-------------------------------------------------------|
| `~/vm/images/`   | Файлы `.qcow2`, `.img`, `.vmdk` (рабочие диски)  | Удобный доступ без sudo, легко бэкапить       | `/var/lib/libvirt/images/` — дефолт libvirt (требует root) |
| `~/vm/iso/`      | Установочные образы (не меняются)                | Отделяем неизменяемые файлы от рабочих        | Можно держать в отдельном месте, если много образов   |
| `~/vm/xml/`      | Исходные XML-файлы определений ВМ                | Версионирование в Git, повторное использование | Libvirt хранит импортированные в своей БД             |
| `~/vm/snapshots/`| Снимки состояния (backing files)                 | Логическое разделение                         | Необязательно, если используете libvirt snapshots     |

### Где запускать команды

| Контекст                     | Рекомендуемая директория для запуска | Почему                                           |
|------------------------------|--------------------------------------|--------------------------------------------------|
| Прямой запуск QEMU           | Любой, но удобно из `~/vm/images/`   | Путь к диску можно указывать относительно (`./pfsense.qcow2`) |
| `qemu-img` (создание/конверсия) | Из `~/vm/images/`                    | Создаваемый файл сразу окажется в нужном месте   |
| `virsh define`               | Из `~/vm/xml/`                       | Удобно указывать `./pfsense.xml`                  |
| `virsh console/start`        | Любая                                | `virsh` работает глобально                       |

**Практический совет:**  
Создайте корневую директорию один раз:

```bash
mkdir -p ~/vm/{images,iso,xml,snapshots}
```

После этого переходите в нужную поддиректорию перед выполнением команд.

### Особенности в WSL2

- **Производительность:** Храните образы в Linux-файлсистеме (`/home/user/vm/`), а не на смонтированном Windows-диске (`/mnt/c/Users/...`). Доступ к `/mnt/c` сильно медленнее.
- **Права доступа:** В домашней директории файлы принадлежат вашему пользователю — не нужны `sudo` для `qemu-img` или прямого QEMU.
- **Бэкап и перенос:** Файлы в `~/vm/` легко копировать на Windows-диск (`cp -r ~/vm /mnt/c/backup/`) или загружать в облако.

## Этап 2: Способы запуска виртуальных машин

В KVM есть два основных подхода:

1. **Прямой запуск через `qemu-system-x86_64`** — максимальная гибкость, полный контроль параметров.
2. **Управление через libvirt (`virsh`)** — удобство, декларативная конфигурация, интеграция с сетями libvirt.

### Подход 1: Прямой запуск QEMU (рекомендуется для разовых задач и отладки)

Пример команды для запуска ВМ с двумя сетевыми интерфейсами в режиме user-NAT:

```bash
qemu-system-x86_64 \
  -enable-kvm \
  -cpu host \
  -m 2048 \
  -drive file=~/vm/images/pfsense.qcow2,if=virtio,format=qcow2 \
  -netdev user,id=wan -device virtio-net-pci,netdev=wan \
  -netdev user,id=lan -device virtio-net-pci,netdev=lan \
  -nographic \
  -serial mon:stdio
```

**Логика выбора параметров:**

| Параметр               | Почему выбираем именно так                          | Альтернативы / когда менять                     |
|-----------------------|----------------------------------------------------|------------------------------------------------|
| `-enable-kvm`         | Аппаратная виртуализация — максимальная производительность | Без него — эмуляция, очень медленно            |
| `-cpu host`           | Проброс реальных возможностей CPU хоста            | `host-passthrough` — ещё больше фич, но хуже переносимость |
| `-m 2048`             | Баланс между потребностями гостя и хостом          | Увеличивать при необходимости                  |
| `if=virtio`           | Paravirtualized драйверы — лучшая производительность диска/сети | `ide` — если гость не поддерживает virtio      |
| `-netdev user`        | Простой NAT, не требует прав root                  | `tap` + bridge — для интеграции с хост-сетью    |
| `-nographic -serial mon:stdio` | Консоль в текущем терминале — удобно в WSL         | `-vnc :0` — если нужен графический доступ      |

#### Подключение установочного образа (.iso или .img) для установки ОС

Часто требуется установить ОС с нуля на пустой диск `qcow2`. Для этого подключается установочный образ (ISO или raw-образ `.img`) в качестве CD/DVD или USB-накопителя.

**Варианты подключения и логика выбора**

| Тип образа             | Как подключить                                                                 | Когда использовать                                                                 | Примечания                                                                 |
|-----------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| Стандартный ISO       | `-cdrom install.iso` <br>или<br>`-drive file=install.iso,media=cdrom,if=ide` | Большинство Linux-дистрибутивов, Windows, любые образы, предназначенные для CD/DVD | Самый простой и надёжный способ. Гость видит как обычный CD-ROM.           |
| Raw-образ `.img` (memstick, hybrid) | `-drive file=image.img,if=ide,format=raw,media=cdrom`<br> + `-boot d`         | pfSense, FreeBSD, OPNsense — образы, которые могут работать как CD            | Работает как CD-ROM, но требует указания `media=cdrom` и загрузки с него   |
| Raw-образ `.img` как USB | `-drive file=image.img,if=none,id=stick,format=raw`<br>`-device usb-storage,drive=stick` | Когда гость ожидает именно USB-накопитель (некоторые версии pfSense/FreeBSD) | Более сложный вариант, иногда требуется эмуляция USB-контроллера (`-device qemu-xhci`) |

**Пример: Установка pfSense из memstick-образа (.img) как CD-ROM** (самый стабильный вариант из практики)

```bash
qemu-system-x86_64 \
  -enable-kvm \
  -cpu host \
  -m 1024 \
  -drive file=~/vm/images/pfsense.qcow2,if=virtio,format=qcow2 \
  -drive file=pfSense-CE-memstick-serial-*.img,if=ide,format=raw,media=cdrom \
  -boot d \
  -netdev user,id=wan -device virtio-net-pci,netdev=wan \
  -netdev user,id=lan -device virtio-net-pci,netdev=lan \
  -nographic \
  -serial mon:stdio
```

- `-boot d` — загрузка со второго диска (установочный образ).
- После установки перезапустите без параметров подключения образа и `-boot d`.

**Пример: Подключение того же .img как USB-накопителя**

```bash
qemu-system-x86_64 \
  -enable-kvm \
  -cpu host \
  -m 1024 \
  -drive file=~/vm/images/pfsense.qcow2,if=virtio,format=qcow2 \
  -drive file=pfSense-CE-memstick-serial-*.img,if=none,id=stick,format=raw \
  -device qemu-xhci,id=usb \
  -device usb-storage,drive=stick,bus=usb.0 \
  -boot menu=on \
  -netdev user,id=wan -device virtio-net-pci,netdev=wan \
  -netdev user,id=lan -device virtio-net-pci,netdev=lan \
  -nographic \
  -serial mon:stdio
```

- `-boot menu=on` позволяет выбрать загрузочное устройство в BIOS QEMU (нажмите F12).

**Логика принятия решений при выборе способа подключения образа**

1. Сначала попробуйте как CD-ROM (`media=cdrom`) — работает в 90 % случаев.
2. Если установщик не видит носитель — попробуйте USB-эмуляцию.
3. Если ничего не помогает — проверьте документацию дистрибутива (pfSense официально рекомендует memstick как USB, но в QEMU CD-ROM часто работает лучше).

### Подход 2: Управление через libvirt и virsh

Libvirt хранит образы по умолчанию в `/var/lib/libvirt/images/`, но можно указывать любой путь.

#### Создание XML-определения ВМ

Пример минимального `vm.xml` (адаптируйте под свои пути):

```xml
<domain type='kvm'>
  <name>example-vm</name>
  <memory unit='KiB'>2097152</memory>
  <vcpu placement='static'>2</vcpu>
  <os>
    <type arch='x86_64' machine='pc'>hvm</type>
    <boot dev='hd'/>
  </os>
  <cpu mode='host-passthrough' check='none'/>
  <devices>
    <emulator>/usr/bin/qemu-system-x86_64</emulator>
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2'/>
      <source file='/home/YOUR_USERNAME/vm/images/example.qcow2'/>
      <target dev='vda' bus='virtio'/>
    </disk>
    <interface type='network'>
      <source network='default'/>
      <model type='virtio'/>
    </interface>
    <serial type='pty'>
      <target type='isa-serial' port='0'/>
    </serial>
    <console type='pty'>
      <target type='serial' port='0'/>
    </console>
  </devices>
</domain>
```

#### Основные команды virsh

```bash
# Импорт ВМ
virsh define vm.xml

# Запуск
virsh start example-vm

# Список ВМ
virsh list --all

# Консоль
virsh console example-vm          # выход: Ctrl + ]

# Корректное выключение
virsh shutdown example-vm

# Принудительное выключение
virsh destroy example-vm

# Удаление определения (файл образа остаётся)
virsh undefine example-vm
```

## Особенности работы KVM в WSL2

| Особенность                          | Последствия / рекомендации                                      |
|--------------------------------------|-----------------------------------------------------------------|
| Нет прямого доступа к аппаратным устройствам (GPU, USB) | Используйте только эмулируемые устройства                      |
| Сеть по умолчанию — NAT через хост    | Для bridge/tap требуется дополнительная настройка на стороне Windows |
| Ограниченный доступ к /dev/kvm       | Требуется членство в группе kvm                                 |
| Нет nested virtualization по умолчанию | Для запуска KVM внутри гостевой ВМ нужно включать в Windows    |

## Рекомендуемый алгоритм действий

1. Проверить поддержку виртуализации → установить пакеты → настроить права.
2. Создать диск: `qemu-img create -f qcow2 disk.qcow2 20G`.
3. Для разовой установки/теста — использовать прямой запуск QEMU.
4. Для постоянного использования — создать XML и управлять через virsh.
5. При необходимости сетевой интеграции — сначала протестировать user-NAT, затем переходить к более сложным схемам.

## Рекомендуемый алгоритм действий при установке ОС в новую ВМ

1. Создать пустой диск: `qemu-img create -f qcow2 disk.qcow2 20G`.
2. Скачать установочный образ.
3. Запустить QEMU с подключением образа как CD-ROM + `-boot d`.
4. Пройти установку в консоли.
5. Перезапустить ВМ без установочного образа для проверки.
6. При необходимости — импортировать в libvirt для дальнейшего управления.
