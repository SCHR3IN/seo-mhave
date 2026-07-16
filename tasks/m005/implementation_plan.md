# Implementation Plan — Task M005: Исправить soft 404 страницы московского магазина

Этот документ описывает план устранения «мягкой ошибки 404» (soft 404) для страницы московского магазина `/contacts/stores/moskva/404/` и смежных разделов `/contacts/stores/`.

---

## User Review Required

> [!IMPORTANT]
> Нам необходимо согласовать стратегию обработки устаревших путей `/contacts/stores/`. 
> Сейчас в файле `/contacts/stores/index.php` прописан безусловный редирект (301) на главную страницу `/`. Поисковые системы расценивают такие массовые редиректы на главную как **Soft 404**.

---

## Open Questions

> [!WARNING]
> Пожалуйста, ответьте на следующие вопросы для точной настройки маршрутизации:
>
> 1. **Какое поведение для `/contacts/stores/moskva/404/` и всего раздела `/contacts/stores/` является предпочтительным?**
>    - **Вариант А**: Возвращать честный HTTP-статус **404 Not Found** с отображением стандартной страницы ошибки Битрикса.
>    - **Вариант Б**: Настроить **301 редирект на релевантный раздел** — `/contacts/` (главная страница контактов), что является легитимным с точки зрения SEO решением при переносе или закрытии магазинов.
>
> 2. **Обновление навигационного меню**:
>    - В файлах меню (`.bottom5.menu.php` и `info/.left.menu.php`) пункт «Магазины» ссылается на `/contacts/stores/`. Согласны ли вы заменить ссылку на `/contacts/`?
>
> 3. **Компонент каталога**:
>    - В параметрах каталога (`/catalog/index.php`) параметр `STORE_PATH` равен `/contacts/stores/#store_id#/`. Если мы закрываем детальные страницы магазинов, согласны ли вы перенаправить этот параметр на `/contacts/`?

---

## Proposed Changes

Мы планируем внести изменения в следующие файлы:

### [Component Name: Routing & Pages]

#### [MODIFY] [index.php](file:///home/egor/Документы/Antigravity_Project/mhave.ru/contacts/stores/index.php)
Изменение логики обработки запросов. В зависимости от выбора варианта (А или Б):
- Либо включение стандартного обработчика 404 Битрикса:
  ```php
  define("ERROR_404", "Y");
  CHTTP::SetStatus("404 Not Found");
  ```
- Либо изменение редиректа на `/contacts/` вместо `/`:
  ```php
  header("Location: /contacts/", true, 301);
  ```

#### [MODIFY] [.bottom5.menu.php](file:///home/egor/Документы/Antigravity_Project/mhave.ru/.bottom5.menu.php)
Замена ссылки в меню с `/contacts/stores/` на `/contacts/`.

#### [MODIFY] [.left.menu.php](file:///home/egor/Документы/Antigravity_Project/mhave.ru/info/.left.menu.php)
Замена ссылки в меню с `/contacts/stores/` на `/contacts/`.

#### [MODIFY] [index.php](file:///home/egor/Документы/Antigravity_Project/mhave.ru/catalog/index.php)
Корректировка параметра `"STORE_PATH" => "/contacts/stores/#store_id#/"` на `"STORE_PATH" => "/contacts/"`.

---

## Verification Plan

### Automated Tests
- Запуск тестов проверки заголовков с помощью `curl`:
  ```bash
  curl -I https://mhave.ru/contacts/stores/moskva/404/
  ```
- Проверка отсутствия старых URL в генерируемом `sitemap.xml`.

### Manual Verification
- Визуальная проверка ссылок в футере (нижнее меню) и левом меню помощи.
