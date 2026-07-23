# Задача M016: Проверить Product/Breadcrumb/Offer-разметку на контрольных сценариях

## 🎯 Цель задачи
Провести аудит существующей структурированной разметки (schema.org) на всех типах страниц и добавить недостающую JSON-LD разметку для корректного отображения в результатах поиска Google (rich snippets).

---

## 🛠️ Реализация и технические изменения

### 1. Аудит текущей разметки
Проведён полный аудит 4 типов страниц:

| Тип страницы | Product | BreadcrumbList | Offer | Organization | WebSite |
|---|---|---|---|---|---|
| Карточка товара | ✅ Microdata | ✅ Microdata | ✅ AggregateOffer | ❌ | ❌ |
| Категория | ✅ (в листинге) | ✅ Microdata | ✅ (в листинге) | ❌ | ❌ |
| Главная | ❌ | ❌ | ❌ | ✅ JSON-LD | ❌ |

**Проблемы:**
- Нет JSON-LD (Google предпочитает JSON-LD над Microdata)
- `itemprop="name"` дублируется 15 раз на одной странице
- Нет `WebSite` + `SearchAction` на главной

### 2. Добавленная JSON-LD разметка

#### Product (карточки товаров)
```json
{
  "@type": "Product",
  "name": "...",
  "description": "...",
  "image": "...",
  "sku": "...",
  "brand": { "@type": "Brand", "name": "..." },
  "offers": {
    "@type": "Offer",
    "price": "...",
    "priceCurrency": "RUB",
    "availability": "https://schema.org/InStock"
  }
}
```

#### BreadcrumbList (каталог, бренды)
```json
{
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "Главная", "item": "https://mhave.ru/" },
    { "@type": "ListItem", "position": 2, "name": "Каталог", "item": "..." }
  ]
}
```

#### WebSite + SearchAction (главная)
```json
{
  "@type": "WebSite",
  "name": "MHAVE",
  "url": "https://mhave.ru/",
  "potentialAction": {
    "@type": "SearchAction",
    "target": { "@type": "EntryPoint", "urlTemplate": "https://mhave.ru/catalog/?q={search_term_string}" },
    "query-input": "required name=search_term_string"
  }
}
```

### 3. Технические детали реализации

**Файл:** `local/php_interface/lib/MhaveSeoTemplates.php`

Добавлены 3 метода:
- `generateJsonLd()` — маршрутизатор: определяет тип страницы и вызывает нужный builder
- `buildProductJsonLd()` — собирает Product из CIBlockElement + CPrice + CFile
- `buildBreadcrumbJsonLd()` — строит цепочку из URL-сегментов через CIBlockSection

Особенности:
- Статическая карта имён для не-инфоблоковых URL (`catalog` → `Каталог`, `kosmetika` → `Косметика`)
- Поиск по 2 инфоблокам (14 — косметика, 9 — БАД)
- Fallback на элементы (последний сегмент URL — товар)
- JSON-LD инжектируется перед `</head>` через output buffer

---

## ✅ Результаты верификации

| Тест | Результат |
|---|---|
| Product JSON-LD на карточке товара | ✅ name, description, image, sku, offer |
| BreadcrumbList JSON-LD на карточке товара | ✅ 5+ ListItem с корректными именами |
| BreadcrumbList JSON-LD на категории | ✅ |
| WebSite + SearchAction на главной | ✅ |
| Organization на главной (уже было) | ✅ без изменений |
| Чистые страницы без лишних блоков | ✅ |

---

## 📁 Затронутые файлы
- `local/php_interface/lib/MhaveSeoTemplates.php` — добавлены методы JSON-LD генерации

## 📅 Дата выполнения
23.07.2026
