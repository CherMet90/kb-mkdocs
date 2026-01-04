*Зачем?*  
Для сегментирования широковещательного (L2) домена  

*Методы назначения влана:*
  * port-based
  * MAC-based
  * protocol-based (по L3-заголовкам, чтобы различить ipv4, ipv6, arp и т.д.)
  * based on IP subnets (router-on-a-stick)  

*ISL - проприетарный cisco способ тэгирования трафика*  

*Best practice:*  
  * Юзать **voice vlan** для IP-тлф
  * Боремся с **vlan-hopping**:
    * используем **статический режим** порта (sw mode acc, tru; sw noneg)
    * использовать **vlan 1** на транковых портах между свичами (спорно)
    * **"Dead End"** влан для неиспользуемых портов
  * **port security**
  * **dhcp snooping** (включить глобально, назначить trusted/untrusted порты)
  * использовать **изоляцию** портов (private vlans, protected ports)