# Walkthrough: ID M007 — Добавить единственный H1 на главную страницу

Задача по добавлению единственного H1 на главную страницу успешно завершена.

## Изменения

### Шаблон блока `CUSTOM_TEXT`
Модифицирован файл `/home/bitrix/ext_www/mhave.ru/include/mainpage/components/custom_text/text.php` на боевом сервере (предварительно создан резервный файл `.bak`). В него добавлен видимый заголовок `<h1>` с коммерческой формулировкой:
```html
<div class="index-block__title-wrapper index-block__title-wrapper--mb-35">
	<h1 class="index-block__title switcher-title" style="text-transform: none; font-weight: 700; color: #1d2029;">Профессиональная косметика, космецевтика и пищевые добавки Mhave</h1>
</div>
```

## Тестирование и валидация

### 1. Проверка HTML-кода
Сделан проверочный запрос на главную страницу. Результаты парсинга подтверждают наличие ровно одного тега `<h1>` на странице:
```bash
$ curl -s https://mhave.ru/ | grep -E -o -i "<h1[^>]*>" | wc -l
1
```

Содержимое тега корректно:
```html
<h1 class="index-block__title switcher-title" style="text-transform: none; font-weight: 700; color: #1d2029;">Профессиональная косметика, космецевтика и пищевые добавки Mhave</h1>
```

### 2. Визуальная проверка
Была проведена автоматическая визуальная проверка отображения на Desktop и Mobile viewports. 

#### Сравнение отображения (Desktop vs Mobile)

````carousel
![Desktop View (1280x800)](/home/egor/.gemini/antigravity/brain/532e51bc-4106-4909-be23-9f637758c85e/mhave_1280_800_1784240108250.png)
<!-- slide -->
![Mobile View (375x667)](/home/egor/.gemini/antigravity/brain/532e51bc-4106-4909-be23-9f637758c85e/mhave_375_667_1784240120009.png)
````

**Результат проверки:**
- На Desktop заголовок отображается в одну строку, шрифт центрирован и выдержан в общей цветовой схеме сайта.
- На Mobile заголовок автоматически адаптируется, переносясь на следующую строку без выхода за пределы экрана и наложений.
