
---

# README: `my_gliner_text.py`

## Назначение

Функция `extract_entities_text` извлекает из текста **только сущности** (без атрибутов по регуляркам) и опционально возвращает **окно контекста** вокруг каждой сущности. Работает на локальной модели **GLiNER 2.5** (`gliner2.5-multi-v1`).

Поддерживает все метки GLiNER 2.5: `PERSON`, `ORGANIZATION`, `DATE`, `PII`, `INN`, `ACCOUNT`, `LOCATION`, `BANK`. Есть **индивидуальные пороги уверенности** по каждому типу.

## Сигнатура

```python
extract_entities_text(
    text,
    entity_types=("PERSON", "ORGANIZATION"),
    entity_labels=None,
    ignore_org_patterns=None,
    ignore_person_patterns=None,
    ignore_initials=True,
    window_left_margin=300,
    return_window=True,
    per_type_thresholds=None,
    chunk_size_words=None,
    chunk_overlap_words=None,
)
```

## Параметры

### Вход
* **`text`** (`str`, обязательный) — исходный текст.

### 1. Что искать
* **`entity_types`** (`tuple[str, ...]`, по умолчанию `("PERSON", "ORGANIZATION")`) — метки GLiNER 2.5 для поиска.
  * Доступные: `"PERSON"` (люди), `"ORGANIZATION"` (организации), `"DATE"` (даты), `"PII"` (общий PII), `"INN"` (ИНН), `"ACCOUNT"` (счета), `"LOCATION"` (локации), `"BANK"` (банки).
  * *Пример:* `("PERSON",)` — только люди.
  * *Пример:* `("PERSON", "DATE", "ACCOUNT")` — люди, даты, счета.
* **`entity_labels`** (`dict`, по умолчанию `None`) — полный словарь меток по типам: `{type: {label: [описания]}}`. Позволяет переопределить описания для любого типа. Если `None` — используется `DEFAULT_ENTITY_LABELS`.

### 2. Фильтры для организаций
* **`ignore_org_patterns`** (`list[str]`, по умолчанию `None`) — список регулярок для отсева организаций. Проверяется только текст сущности (после склейки и ОПФ).
  * *Пример:* `[r'банк', r'мвд', r'суд', r'област(и|ь)']`

### 3. Фильтры для ФИО
* **`ignore_person_patterns`** (`list[str]`, по умолчанию `None`) — список регулярок для отсева ФИО по контексту (50 символов перед сущностью + сама сущность).
  * *Пример:* `[r'судья', r'следовател', r'прокурор', r'в интересах']`
* **`ignore_initials`** (`bool`, по умолчанию `True`) — игнорировать ли ФИО с инициалами.

### 4. Окно поиска атрибутов
* **`window_left_margin`** (`int`, по умолчанию `300`) — насколько символов смотреть **налево** от сущности при построении окна.
  * `window_start = max(block_start, span.start - window_left_margin)`, где `block_start` — конец предыдущей сущности (или 0 для первой).
  * *Пример:* `0` — окно от конца предыдущей сущности до начала следующей.
  * *Пример:* `500` — больше контекста слева.
* **`return_window`** (`bool`, по умолчанию `True`) — если `True`, возвращает сущности с полем `window` (текст + координаты). Если `False` — только `{entity, type, start, stop}`.

### 5. Индивидуальные пороги уверенности
* **`per_type_thresholds`** (`dict`, по умолчанию `None`) — словарь `{тип: порог}` для фильтрации по `confidence`.
  * Ключи — метки GLiNER 2.5: `"PERSON"`, `"ORGANIZATION"`, `"DATE"`, `"PII"`, `"INN"`, `"ACCOUNT"`, `"LOCATION"`, `"BANK"`.
  * Значения — `float` 0.0–1.0.
  * Для типов, которых нет в словаре, порог не применяется.
  * *Пример:* `{"PERSON": 0.7, "ORGANIZATION": 0.3, "DATE": 0.5}`
  * Если `None` — фильтрация по `confidence` не применяется (внутренний порог модели — 0.1).

### 6. Чанкинг
* **`chunk_size_words`** (`int`, по умолчанию `None`) — размер куска в словах.
* **`chunk_overlap_words`** (`int`, по умолчанию `None`) — перекрытие между кусками в словах.

## Что возвращает

Список словарей, по одному на сущность.

**При `return_window=False`:**
* **`entity`** (`str`) — текст сущности.
* **`type`** (`str`) — метка GLiNER 2.5 (`"PERSON"`, `"ORGANIZATION"`, `"DATE"`, `"PII"`, `"INN"`, `"ACCOUNT"`, `"LOCATION"`, `"BANK"`).
* **`start`** (`int`) — индекс первого символа.
* **`stop`** (`int`) — индекс сразу после последнего символа.

**При `return_window=True`** добавляется:
* **`window`** (`dict`) — окно контекста:
  * `text` (`str`) — текст окна.
  * `start` (`int`) — индекс начала окна.
  * `stop` (`int`) — индекс конца окна.

> **Окно:** `window_start = max(block_start, span.start - window_left_margin)`, `window_end = block_end`, где `block_start` — конец предыдущей сущности (или 0), `block_end` — начало следующей сущности (или `len(text)`).

## Пример JSON-вывода

**`return_window=True`:**
```json
[
  {
    "entity": "Ивановой Марии Сергеевны",
    "type": "PERSON",
    "start": 431,
    "stop": 455,
    "window": {
      "text": "…фрагмент текста от window_start до window_end…",
      "start": 131,
      "stop": 1467
    }
  },
  {
    "entity": "ООО «АЛЬФАСТРОЙ»",
    "type": "ORGANIZATION",
    "start": 94,
    "stop": 109,
    "window": {
      "text": "…фрагмент текста…",
      "start": 0,
      "stop": 380
    }
  }
]
```

**`return_window=False`:**
```json
[
  {
    "entity": "Ивановой Марии Сергеевны",
    "type": "PERSON",
    "start": 431,
    "stop": 455
  },
  {
    "entity": "ООО «АЛЬФАСТРОЙ»",
    "type": "ORGANIZATION",
    "start": 94,
    "stop": 109
  }
]
```

## Примеры использования

**1. Только люди и организации, без окон:**
```python
from my_gliner_text import extract_entities_text

entities = extract_entities_text(
    text,
    entity_types=("PERSON", "ORGANIZATION"),
    ignore_org_patterns=[r'банк', r'мвд', r'суд'],
    ignore_person_patterns=[r'судья', r'следовател'],
    return_window=False,
)
```

**2. Люди + организации с окнами (для последующей привязки атрибутов):**
```python
entities = extract_entities_text(
    text,
    entity_types=("PERSON", "ORGANIZATION"),
    return_window=True,
    window_left_margin=300,
)
```

**3. Все типы с индивидуальными порогами:**
```python
entities = extract_entities_text(
    text,
    entity_types=("PERSON", "ORGANIZATION", "DATE", "PII", "INN", "ACCOUNT"),
    per_type_thresholds={
        "PERSON": 0.7,
        "ORGANIZATION": 0.4,
        "DATE": 0.6,
        "PII": 0.5,
        "INN": 0.8,
        "ACCOUNT": 0.8,
    },
    return_window=False,
)
```

**4. Длинный текст — с чанкингом:**
```python
entities = extract_entities_text(
    text,
    chunk_size_words=300,
    chunk_overlap_words=50,
)
```