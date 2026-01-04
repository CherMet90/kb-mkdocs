##### Unzip tar.gz
```
# To uncompress the gz file
gunzip file.tar.gz

# Now you will have a .tar file
# To extract the tar file
tar -xvf file.tar
```
<br>

##### Add a new Virtual Disk to VM established by VMware Workstaion Player
1. Shutdown the VM
2. Add the New Virtual Disk:  
    - Open VMware Workstation Player.
    - Go to "Player" > "Manage" > "Virtual Machine Settings".
    - Click "Add..." to add a new hard disk.
    - Follow the wizard steps:  
        * Type: Select "Hard Disk".
        * Disk Type: Choose a disk type, typically "SCSI" for simplicity.
        * Disk Size: Set the size to 20GB.
        * Options: Choose whether you want to allocate the disk space now or allow it to grow as needed.
3. Start the VM
4. Partition and Format the New Disk:
* Identify the new disk first:  
     ```lsblk```
 You should see the new disk, likely as `/dev/sdb`.
* Partition the new disk:  
     ```sudo fdisk /dev/sdb```
 Follow the prompts to create a new partition. When done, it might create something like `/dev/sdb1`.
* Format the partition:  
     ```sudo mkfs.ext4 /dev/sdb1```
5. Create a Mount Point and Mount the New Disk:
   ```
   sudo mkdir /mnt/newdisk
   sudo mount /dev/sdb1 /mnt/newdisk
   ```
6. Update /etc/fstab to Auto-Mount the New Disk:  
Open /etc/fstab in a text editor:  
   ```sudo nano /etc/fstab```
Add an entry to ensure the new disk mounts at startup:  
   ```/dev/sdb1  /mnt/newdisk  ext4  defaults  0  2```
7. Reboot to Verify:  
   ```sudo reboot```
<br>

##### Переместить данные на другой раздел и создать символьную ссылку на старом (на примере `.vscode-server`)
1. Stop the VSCode server or any processes using `.vscode-server`:  
     ```pkill -f vscode```
2. Move the `.vscode-server` directory:  
     ```sudo mv /home/username/.vscode-server /mnt/newdisk/.vscode-server```
3. Create a symbolic link to the new location:  
     ```sudo ln -s /mnt/newdisk/.vscode-server /home/username/.vscode-server```
4. Ensure the link works and the `.vscode-server` directory is accessible:  
   ```ls -l /home/username/.vscode-server```

##### Настройка автоматических security updates (Ubuntu)
- устанавливаем пакет
     ```
     sudo apt-get install unattended-upgrades
     ```
- включаем автообновления 
     ```
     sudo dpkg-reconfigure --priority=low unattended-upgrades
     ```
- в настройках `/etc/apt/apt.conf.d/50unattended-upgrades` в `Unattended-Upgrade::Allowed-Origins {}` настраиваем каналы, которые хотим автоматически обновлять, например комментим `"${distro_id}:${distro_codename}";`, чтобы избежать автоматического обновления всех пакетов, оставляем - `-security` канал
- проверяем настройки периодичности обновлений в `/etc/apt/apt.conf.d/20auto-upgrades`:
     ```
     APT::Periodic::Update-Package-Lists "1";
     APT::Periodic::Unattended-Upgrade "1";
     ```
- можем настроить временной период для обновлений:
     ```
     # Проверяем часовой пояс системного времени
     timedatectl

     # Открываем редактор настроек
     sudo systemctl edit apt-daily-upgrade.timer
     
     # Не расскоментируем существующие примеры, а вставляем блок выше секции с примерами (в файле есть комментарий, который гласит, что ниже него по файлу настройки игнорируются)
     [Timer]
     OnCalendar=*-*-* 17:00:00     # Начало периода обновлений по системному времени
     RandomizedDelaySec=40m        # Длительность промежутка, в течении которого обновление может быть запущено (конкретное время будет рандомизировано при каждом запуске)
     ```
- сохраняем, закрываем (`Ctrl+O → Enter → Ctrl+X`)
- применяем настройки
     ```
     sudo systemctl daemon-reload
     sudo systemctl restart apt-daily-upgrade.timer
     ```
- проверяем, что они применились - наша секция должна появится в конце вывода
     ```
     systemctl cat apt-daily-upgrade.timer
     ```
