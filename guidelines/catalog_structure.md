# Реструктуризация каталога «Косметика для лица»

Этот документ содержит план перехода от старой структуры разделов каталога косметики для лица к новой оптимизированной структуре на основе файла `task_13_hierarchy.csv`. Данная реструктуризация направлена на устранение дублирования, сокращение вложенности и оптимизацию H1 для поисковых систем.

---

## 1. Карта перенаправлений (301 Redirects)

Для сохранения SEO-трафика при изменении URL разделов каталога необходимо настроить 301-редиректы. Редиректы настраиваются либо в файле `.htaccess`, либо через стандартный модуль редиректов в 1С-Битрикс.

| Старый URL (Источник) | Новый URL (Назначение) | H1 (Новое название раздела) |
| :--- | :--- | :--- |
| `/catalog/kosmetika/sredstva-dlya-litsa/glubokoe-ochishchenie/` | `/catalog/kosmetika/sredstva-dlya-litsa/ochishchenie/` | **Очищение кожи лица** |
| `/catalog/kosmetika/sredstva-dlya-litsa/tonizirovanie/` | `/catalog/kosmetika/sredstva-dlya-litsa/toniki/` | **Тоники для лица** |
| `/catalog/kosmetika/sredstva-dlya-litsa/syvorotki-i-kontsentraty1/` | `/catalog/kosmetika/sredstva-dlya-litsa/syvorotki/` | **Сыворотки для лица** |
| `/catalog/kosmetika/sredstva-dlya-litsa/maski1/` | `/catalog/kosmetika/sredstva-dlya-litsa/maski/` | **Маски для лица** |
| `/catalog/kosmetika/sredstva-dlya-litsa/uvlazhnenie-i-pitanie/spetsialnyy-ukhod/` | `/catalog/kosmetika/sredstva-dlya-litsa/spetsialnyy-ukhod/` | **Специальный уход** |

---

## 2. Новое дерево подразделов

Корневой раздел: `/catalog/kosmetika/sredstva-dlya-litsa/` (H1: **Косметика для лица**)

### 2.1. Группа «ОЧИЩЕНИЕ»
* `/ochishchenie/` — **Очищение кожи лица** (общий раздел)
* `/ochishchenie/geli-dlya-umyvaniya/` — **Гели для умывания**
* `/ochishchenie/molochko/` — **Молочко для умывания**
* `/ochishchenie/penki/` — **Пенки для умывания** *(резерв)*
* `/ochishchenie/mitsellyarnye-sredstva/` — **Мицеллярные средства** *(резерв)*

### 2.2. Группа «ТОНИКИ»
* `/toniki/` — **Тоники для лица**

### 2.3. Группа «СЫВОРОТКИ И КОНЦЕНТРАТЫ»
* `/syvorotki/` — **Сыворотки для лица**
* `/koncentraty/` — **Концентраты для лица**

### 2.4. Группа «КРЕМЫ»
* `/kremy-dlya-litsa/` — **Кремы для лица**
  * `dnevnye-kremy/` — **Дневные кремы**
  * `nochnye-kremy/` — **Ночные кремы**
  * `anti-eydzh/` — **Кремы Анти-Эйдж**
  * `universalnye-kremy/` — **Универсальные кремы**
  * `normalizuyushchie-kremy/` — **Нормализующие кремы**
  * `bb-kremy/` — **ВВ-кремы**
  * `ampulnye-kremy/` — **Ампульные кремы**
  * `solntsezashchitnye-kremy-spf/` — **Солнцезащитные кремы (SPF)**
  * `kremy-dlya-vek/` — **Кремы для век**

### 2.5. Группа «МАСКИ»
* `/maski/` — **Маски для лица**
  * `anti-eydzh/` — **Маски Анти-Эйдж**
  * `lifting/` — **Маски с эффектом лифтинга**
  * `vosstanavlivayushchie/` — **Восстанавливающие маски**
  * `nochnye/` — **Ночные маски**
  * `protiv-akne-i-postakne/` — **Маски против акне и постакне**
  * `uvlazhnyayushchie/` — **Увлажняющие маски**

### 2.6. Группа «СПЕЦИАЛЬНЫЙ УХОД И ДР.»
* `/spetsialnyy-ukhod/` — **Специальный уход** (точечное применение)
* `/patchi-idgie/` — **Патчи для лица**
* `/kushony/` — **Кушоны**
* `/anti-eydzh/` — **Антивозрастные средства для лица**
* `/nabory/` — **Наборы по уходу за лицом**

---

## 3. Рекомендации по переносу товаров в Битрикс
1. **Резервная копия**: Перед внесением изменений сделайте резервную копию базы данных инфоблока каталога.
2. **Создание разделов**: Создайте новые разделы в инфоблоке каталога (с указанием ЧПУ символьных кодов согласно структуре выше).
3. **Пакетный перенос**: Через административную панель Битрикс выполните групповой перенос товаров из старых разделов в новые.
4. **Удаление старых**: Убедитесь, что старые разделы больше не содержат товаров, и удалите их.
5. **Внедрение редиректов**: Пропишите правила редиректа.

Пример правил для `.htaccess`:
```apache
Redirect 301 /catalog/kosmetika/sredstva-dlya-litsa/glubokoe-ochishchenie/ /catalog/kosmetika/sredstva-dlya-litsa/ochishchenie/
Redirect 301 /catalog/kosmetika/sredstva-dlya-litsa/tonizirovanie/ /catalog/kosmetika/sredstva-dlya-litsa/toniki/
Redirect 301 /catalog/kosmetika/sredstva-dlya-litsa/syvorotki-i-kontsentraty1/ /catalog/kosmetika/sredstva-dlya-litsa/syvorotki/
Redirect 301 /catalog/kosmetika/sredstva-dlya-litsa/maski1/ /catalog/kosmetika/sredstva-dlya-litsa/maski/
Redirect 301 /catalog/kosmetika/sredstva-dlya-litsa/uvlazhnenie-i-pitanie/spetsialnyy-ukhod/ /catalog/kosmetika/sredstva-dlya-litsa/spetsialnyy-ukhod/
```
