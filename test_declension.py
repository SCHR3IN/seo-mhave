import pandas as pd
import re

def decline_accusative(name):
    n = name.strip()
    # Special dictionary for site categories
    rules = {
        'Косметика': 'косметику',
        'Пищевые добавки': 'пищевые добавки',
        'Аксессуары': 'аксессуары',
        'Средства для лица': 'средства для лица',
        'Средства для тела': 'средства для тела',
        'Уход за лицом': 'средства для ухода за лицом',
        'Уход за телом': 'средства для ухода за телом',
        'Сыворотки для лица': 'сыворотки для лица',
        'Кремы для лица': 'кремы для лица',
        'Очищение кожи': 'средства для очищения кожи',
    }
    if n in rules:
        return rules[n]
    
    # Generic simple rule for words ending in -ка / -а
    if n.endswith('ка'):
        return n[:-1] + 'ку'
    elif n.endswith('а') and not n.endswith('ста'):
        return n[:-1] + 'у'
    elif n.endswith('ия'):
        return n[:-2] + 'ию'
    return n.lower()

test_names = ['Косметика', 'Пищевые добавки', 'Аксессуары', 'Средства для лица', 'Сыворотки для лица', 'Новинки']
for t in test_names:
    print(f"'{t}' -> 'Купить {decline_accusative(t)} по выгодной цене в интернет-магазине MHAVE'")
