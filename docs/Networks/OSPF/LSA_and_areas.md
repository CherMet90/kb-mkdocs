##### Типы LSA

| LSA       | Описание                                              |
|-----------|-------------------------------------------------------|
| Type 1    | для обмена инфой между роутерами внутри зоны          |
| Type 2    | распространяет DR                                     |
| Type 3    | анонс маршрутов из другой зоны, cоздаёт ABR           |
| Type 4    | анонс маршрута до ASBR, создаёт ABR                   |     
| Type 5    | анонс external-маршрута, создаёт ASBR                 |
| Type 7    | анонс external-маршрута в NSSA-сетях, создаёт ASBR    |
<br>

##### Stubby зоны
###### Stub
В stub зоне запрещены LSA 4 и 5. При анонсе в stub зону ABR анонсит вместо них себя, как default route  
![Stub Area](../../images/ospf_stub.png)
###### Not-So-Stubby (NSSA)
В отличии от stub зоны разрешен redistribute маршрутов. ABR анонсит default route вместо LSA 4 И 5 опционально(!)  
![NSSA Area](../../images/ospf_nssa.png)
###### Totally
Реализуется командой `no-summary` на ABR. ABR начинает LSA 3 также заменять на default route.