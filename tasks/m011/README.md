# Задача M011: Закрыть мусорные фильтры и настроить canonical/noindex

## 🎯 Цель задачи
Исключить индексацию мусорных filter-URL (smart filter, GET-параметры сортировки, пагинации), предотвратить создание дублей в индексе Google. Сохранить доступность полезных фильтров.

---

## 🛠️ Реализация и технические изменения

### 1. Аудит текущего состояния

**Что уже работало (Aspro Lite):**

| Сценарий | HTTP | canonical | meta robots | X-Robots-Tag |
|---|---|---|---|---|
| `/filter/brand-is-X/apply/` | 200 | → родительская ✅ | `noindex, follow` ✅ | `noindex, follow` ✅ |
| `/filter/price-base-from-X/apply/` | 200 | → родительская ✅ | `noindex, follow` ✅ | `noindex, follow` ✅ |
| `/filter/apply/` (пустой) | 404 ✅ | → родительская | `noindex, follow` ✅ | `noindex, follow` ✅ |

**Что НЕ работало (нужно было исправить):**

| Сценарий | Проблема |
|---|---|
| `?set_filter=y&BRAND_REF=X` | ❌ Нет noindex — Google мог индексировать |
| `?sort=price&order=asc` | ❌ Нет noindex |
| `?PAGEN_1=2` (пагинация) | ❌ Нет noindex (только robots.txt) |
| `robots.txt` | ❌ Нет правила для `/filter/` |
| Sitemap | ✅ 0 filter-URL (чисто) |

### 2. Исправление robots.txt

Добавлено правило:
```
Disallow: */filter/
```

Это предотвращает обход ботами всех SEF-фильтров.

### 3. Noindex для GET-параметров фильтров

**Файл:** `local/php_interface/lib/MhaveSeoTemplates.php`

В метод `applyEndBufferContent()` добавлена проверка:

```php
$noindexParams = ['set_filter', 'sort', 'order', 'display', 'PAGEN_', 'SHOWALL_'];
```

Если `QUERY_STRING` содержит любой из этих параметров — инжектируется:
```html
<meta name="robots" content="noindex, follow">
```

Также добавлен backup-noindex для SEF `/filter/` URL на случай, если Aspro не отработает.

**Защита:** Если `<meta name="robots">` уже есть (например, от Aspro), дублирование не происходит.

### 4. Clean-param для Яндекса (GET-дубли)

По рекомендации Яндекс.Вебмастера «Найдены страницы-дубли с GET-параметрами» добавлены директивы `Clean-param`:

```
Clean-param: utm_source&utm_medium&utm_campaign&utm_content&utm_term /
Clean-param: yclid /
Clean-param: ysclid /
Clean-param: ybaip /
Clean-param: etext /
Clean-param: display /catalog/
Clean-param: sort&order /catalog/
Clean-param: is_aspro_mobile /
Clean-param: set_filter&BRAND_REF /catalog/
Clean-param: PAGEN_1&PAGEN_2 /
Clean-param: SHOWALL_1&SHOWALL_2 /
```

Это сообщает Яндексу, что указанные GET-параметры не влияют на контент страницы и не должны создавать отдельные URL.

### 5. Переобход страниц

11 ключевых страниц отправлены на переобход через API Яндекс.Вебмастера для обновления данных о titles/descriptions.

---

## ✅ Результаты верификации

| Тест | До | После |
|---|---|---|
| `/filter/brand-is-X/apply/` | `noindex` (Aspro) | `noindex` ✅ |
| `?set_filter=y&BRAND_REF=X` | ❌ индексируется | `noindex, follow` ✅ |
| `?sort=price&order=asc` | ❌ индексируется | `noindex, follow` ✅ |
| `?PAGEN_1=2` | ❌ индексируется | `noindex, follow` ✅ |
| Чистая категория `/catalog/kosmetika/` | нет noindex | нет noindex ✅ (не затронута) |
| robots.txt | нет filter-правила | `Disallow: */filter/` ✅ |
| Sitemap | 0 filter-URL | 0 filter-URL ✅ |

---

## 📁 Затронутые файлы
- `robots.txt` — добавлено `Disallow: */filter/`
- `local/php_interface/lib/MhaveSeoTemplates.php` — noindex для GET-фильтров

## 📅 Дата выполнения
23.07.2026
