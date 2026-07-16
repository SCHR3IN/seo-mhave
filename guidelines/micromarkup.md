# Техническая спецификация микроразметки (JSON-LD)

Этот документ описывает требования и примеры внедрения микроразметки на сайте `mhave.ru` с использованием формата **JSON-LD**. Использование JSON-LD является наиболее современным стандартом и поддерживается всеми поисковыми системами и ИИ-агентами.

---

## 1. Разметка статьи блога (BlogPosting)

Должна выводиться на детальной странице каждой статьи (`/info/articles/ID/` или аналогичных).

### 1.1. Шаблон JSON-LD
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://mhave.ru/info/articles/primer-statyi/"
  },
  "headline": "Заголовок статьи (H1)",
  "description": "Краткое описание (анонс) статьи",
  "image": "https://mhave.ru/upload/iblock/article_preview.jpg",  
  "author": {
    "@type": "Person",
    "name": "Имя Фамилия Автора",
    "jobTitle": "Косметолог-дерматолог",
    "sameAs": "https://mhave.ru/about/team/doctor-ivanova/"
  },  
  "publisher": {
    "@type": "Organization",
    "name": "MHAVE",
    "logo": {
      "@type": "ImageObject",
      "url": "https://mhave.ru/local/templates/aspro_max/images/logo.png"
    }
  },
  "datePublished": "2026-07-10T12:00:00+03:00",
  "dateModified": "2026-07-14T19:30:00+03:00"
}
</script>
```

### 1.2. Особенности реализации на 1С-Битрикс
В шаблоне детальной страницы статьи (`component_epilog.php` или `template.php` компонента `news.detail`):
1. **dateModified**: Вместо даты создания выводим дату последнего изменения элемента:
   ```php
   $dateModified = MakeTimeStamp($arResult["TIMESTAMP_X"]);
   $dateModifiedISO = date("c", $dateModified); // Формат ISO 8601
   ```
2. **datePublished**: Дата начала активности:
   ```php
   $datePublished = MakeTimeStamp($arResult["ACTIVE_FROM"]);
   $datePublishedISO = date("c", $datePublished);
   ```
3. **author**: В инфоблоке статей должно быть создано свойство типа привязки к элементам (например, `UF_AUTHOR` к инфоблоку "Команда/Авторы"). Если свойство пустое, по умолчанию выводим:
   ```json
   "author": {
     "@type": "Organization",
     "name": "Редакция MHAVE"
   }
   ```

---

## 2. Разметка вопросов и ответов (FAQPage)

Используется для вывода часто задаваемых вопросов в статьях или на страницах услуг.

### 2.1. Шаблон JSON-LD
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Как правильно подобрать кушон под тип кожи?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Для сухой кожи подходят кушоны с влажным финишем и гиалуроновой кислотой (например, Troiareuke Seoul C21). Для жирной кожи выбирайте матирующие кушоны с себорегулирующими компонентами."
      }
    },
    {
      "@type": "Question",
      "name": "Можно ли использовать ретинол летом?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Да, использовать ретинол летом можно, но только в вечернем уходе и при обязательном нанесении солнцезащитного крема с фактором SPF 50+ каждое утро."
      }
    }
  ]
}
</script>
```

### 2.2. Реализация в контенте
Для добавления FAQ контент-менеджерами можно использовать множественное свойство типа «Справочник» или разметку внутри текста. Но предпочтительнее сделать кастомный блок в конструкторе Аспро, выводящий поля `Вопрос` и `Ответ` и автоматически заворачивающий их в JSON-LD.

---

## 3. Разметка навигационной цепочки (BreadcrumbList)

Помогает поисковым системам правильно понимать и отображать хлебные крошки в сниппете (выдаче).

### 3.1. Шаблон JSON-LD
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Главная",
      "item": "https://mhave.ru/"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "Косметика",
      "item": "https://mhave.ru/catalog/kosmetika/"
    },
    {
      "@type": "ListItem",
      "position": 3,
      "name": "Средства для лица",
      "item": "https://mhave.ru/catalog/kosmetika/sredstva-dlya-litsa/"
    }
  ]
}
</script>
```

### 3.2. Внедрение в 1С-Битрикс
В шаблоне компонента хлебных крошек `menu` или `breadcrumb` (обычно в `/local/templates/aspro_max/components/bitrix/breadcrumb/`):
```php
if(empty($arResult))
    return "";

$strReturn = '<script type="application/ld+json">';
$strReturn .= '{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [';

$items = [];
$itemSize = count($arResult);
for($index = 0; $index < $itemSize; $index++)
{
    $title = htmlspecialcharsbx($arResult[$index]["TITLE"]);
    $link = $arResult[$index]["LINK"];
    // Проверка на абсолютный URL
    if (strpos($link, 'http') !== 0) {
        $link = 'https://mhave.ru' . $link;
    }
    
    $pos = $index + 1;
    $items[] = '{"@type": "ListItem", "position": ' . $pos . ', "name": "' . $title . '", "item": "' . $link . '"}';
}

$strReturn .= implode(',', $items);
$strReturn .= ']}</script>';

return $strReturn;
```
