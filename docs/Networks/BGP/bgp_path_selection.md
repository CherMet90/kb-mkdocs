##### Порядок сравнения атрибутов для выбора пути:
* **highest** *weight* # Cisco only. Задаётся локально для роутера.
* **highest** *local preference* # Действует внутри AS. Default value 100
* local originated route: locally advertised -> locally aggregated -> received by BGP peers
* **shortest** *AIGP metric*
* **shortest** *AS_Path*
* **best** *origin code*: network statement(i) -> EGP(e)*(deprecated)* -> redistributed(?)
* **lowest** *MED* # атрибут сохраняется в пределах соседней AS, не далее
* *eBGP* > confederation members > *iBGP*
* **closest** *IGP-neighbor*
* **oldest** eBGP route
* **lowest** neighbor *BGP RID*
* **lowest** neighbor *IP*

###### Кейсы, которые я вижу:
*weight* - Если один роутер подключается к двум разным вышестоящим AS, для выбора предпочитаемого хопа для исходящего трафика.  
*local preference* - 2 маршика с двумя пирами, третий, iBGP-сосед, сможет выбрать хоп для исходящего трафика.  
*AS_Path* - Для манипуляции предпочитаемым путём для входящего трафика при стыке одного роутера с двумя вышестоящими AS. Добавляем лишнюю запись в AS_Path для неосновного пира, откуда меньше хотим получать трафик