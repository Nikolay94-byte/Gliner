
---

# README: `my_gliner_ner.py`

## Назначение

Функция `extract_entities_with_attributes` извлекает из текста **сущности** (люди `PER`, организации `ORG`) и **привязанные к ним атрибуты** (ИНН, дата рождения, банковские счета) с абсолютными координатами в исходном тексте.

Работает на локальной модели **GLiNER 2.5** (`gliner2.5-multi-v1`). Атрибуты (ИНН, даты, счета) ищутся **регулярными выражениями** внутри окна вокруг сущности, а не самой моделью — это даёт предсказуемость и контроль.

## Сигнатура

```python
extract_entities_with_attributes(
    text,
    entity_types=("PER", "ORG"),
    person_labels=None,
    org_labels=None,
    ignore_org_patterns=None,
    ignore_person_patterns=None,
    ignore_initials=True,
    inn_pattern=DEFAULT_INN_REGEX,
    birth_date_pattern=DEFAULT_BIRTH_DATE_REGEX,
    account_pattern=DEFAULT_ACCOUNT_REGEX,
    birth_date_markers=None,
    attributes_to_find=("inn", "birth_date", "account"),
    account_owner_patterns=None,
    account_ignore_patterns=None,
    chunk_size_words=None,
    chunk_overlap_words=None,
)
```

## Параметры

### Вход
* **`text`** (`str`, обязательный) — исходный текст, в котором нужно найти сущности и атрибуты.

### 1. Что искать (сущности)
* **`entity_types`** (`tuple[str, ...]`, по умолчанию `("PER", "ORG")`) — типы сущностей.
  * `"PER"` — люди (ФИО). Внутри маппится в метку модели `"PERSON"`.
  * `"ORG"` — организации. Внутри маппится в метку модели `"ORGANIZATION"`.
  * *Пример:* `("PER",)` — искать только людей.
* **`person_labels`** (`dict`, по умолчанию `None`) — словарь с описаниями для модели, как искать людей. Если `None`, используется `DEFAULT_PERSON_LABELS`.
  * *Пример:* `{"PERSON": "ФИО должника, гражданин РФ"}`
* **`org_labels`** (`dict`, по умолчанию `None`) — описания для модели, как искать организации. Если `None`, используется `DEFAULT_ORG_LABELS`.
  * *Пример:* `{"ORGANIZATION": "Коммерческая организация, ООО, АО"}`

### 2. Фильтры для организаций
* **`ignore_org_patterns`** (`list[str]`, по умолчанию `None`) — список регулярок для отсева организаций. Проверяется **только текст самой сущности** (после склейки и приклеивания ОПФ), контекст не проверяется — иначе слова «банк», «фонд» из предыдущего предложения отсеивали бы нормальные компании.
  * *Пример:* `[r'банк', r'мвд', r'суд', r'прокуратур']`
  * Если `None` — фильтрация не применяется.

### 3. Фильтры для ФИО
* **`ignore_person_patterns`** (`list[str]`, по умолчанию `None`) — список регулярок для отсева ФИО по контексту. Проверяются 50 символов **перед** сущностью **и** сама сущность.
  * *Пример:* `[r'судья', r'следовател', r'прокурор', r'в интересах']`
* **`ignore_initials`** (`bool`, по умолчанию `True`) — игнорировать ли ФИО с инициалами. `True` — «И.С. Иванов» отсеивается. `False` — разрешено.

### 4. Регулярки для атрибутов
* **`inn_pattern`** (`str`, по умолчанию `r'\b(\d{10,12})\b'`) — регулярка для поиска ИНН.
* **`birth_date_pattern`** (`str`, по умолчанию `r'\b(\d{2}\.\d{2}\.\d{4})\b'`) — регулярка для поиска даты рождения.
* **`account_pattern`** (`str`, по умолчанию `r'\b(\d{19,20})\b'`) — регулярка для поиска банковских счетов.
* **`birth_date_markers`** (`list[str]`, по умолчанию `None`) — маркеры, помогающие отличить дату рождения от других дат (срок следствия, дата постановления).
  * Если `None` — используется `[r'года\s+рождения', r'г\.р\.', r'родил']`.

### 5. Какие атрибуты искать
* **`attributes_to_find`** (`tuple[str, ...]`, по умолчанию `("inn", "birth_date", "account")`) — какие атрибуты искать.
  * `()` — искать только сущности, без атрибутов.
  * `("account",)` — только счета.
  * `("inn", "account")` — ИНН и счета.

### 6. Фильтрация счетов по банку
* **`account_owner_patterns`** (`list[str]`, по умолчанию `None`) — регулярки для **owner-банков** (их счета берём). Включает режим «только счета указанных банков».
  * Направление (счёт→банк или банк→счёт) определяется автоматически по первому банку в окне.
  * *Пример:* `[r'ВТБ', r'Банк\s+ВТБ', r'ПАО\s+«?ВТБ»?']`
  * Если `None` (и `account_ignore_patterns` тоже `None`) — берутся все счета.
* **`account_ignore_patterns`** (`list[str]`, по умолчанию `None`) — регулярки для банков, счета которых нужно **игнорировать**.
  * Итоговый ignore = `TOP_RUSSIAN_BANKS` минус owner + `account_ignore_patterns`.
  * *Пример:* `[r'Сбербанк', r'Тинькофф']`

### 7. Чанкинг
* **`chunk_size_words`** (`int`, по умолчанию `None`) — размер куска в словах. Если `None` — текст подаётся в модель целиком.
  * *Пример:* `300` — разбить на куски по 300 слов.
* **`chunk_overlap_words`** (`int`, по умолчанию `None`) — перекрытие между кусками в словах. Используется только если задан `chunk_size_words`.
  * *Пример:* `50`.

## Что возвращает

Список словарей, по одному на сущность:

* **`entity`** (`str`) — текст сущности.
* **`type`** (`str`) — `"PER"` или `"ORG"`.
* **`start`** (`int`) — индекс первого символа сущности в исходном тексте.
* **`stop`** (`int`) — индекс сразу после последнего символа (exclusive).
* **`attributes`** (`dict`) — найденные атрибуты:
  * **`inn`** (`dict | None`) — ИНН (только для `ORG`). Формат: `{"value": str, "start": int, "stop": int}`.
  * **`birth_date`** (`dict | None`) — дата рождения (только для `PER`). Формат: `{"value": str, "start": int, "stop": int}`.
  * **`account`** (`list[dict]`) — список счетов (для `PER` и `ORG`). Формат каждого: `{"value": str, "start": int, "stop": int}`.

> **Инвариант координат:** `text[start:stop]` всегда равно `value` (для атрибутов) или `entity` (для сущности).

## Пример JSON-вывода

```json
[
  {
    "entity": "Ивановой Марии Сергеевны",
    "type": "PER",
    "start": 431,
    "stop": 455,
    "attributes": {
      "inn": null,
      "birth_date": {
        "value": "12.12.1994",
        "start": 456,
        "stop": 466
      },
      "account": [
        {
          "value": "40800010990000123456",
          "start": 375,
          "stop": 395
        }
      ]
    }
  },
  {
    "entity": "ООО «АЛЬФАСТРОЙ»",
    "type": "ORG",
    "start": 94,
    "stop": 109,
    "attributes": {
      "inn": {
        "value": "7711134567",
        "start": 115,
        "stop": 125
      },
      "birth_date": null,
      "account": [
        {
          "value": "40701110701000000106",
          "start": 166,
          "stop": 186
        },
        {
          "value": "40701110225630002518",
          "start": 217,
          "stop": 237
        }
      ]
    }
  }
]
```

## Примеры использования

**1. Базовый поиск (люди + организации + все атрибуты):**
```python
from my_gliner_ner import extract_entities_with_attributes

entities = extract_entities_with_attributes(
    text,
    ignore_org_patterns=[r'банк', r'мвд', r'суд'],
    ignore_person_patterns=[r'судья', r'следовател']
)
```

**2. Только физлица и только дата рождения + счёт:**
```python
entities = extract_entities_with_attributes(
    text,
    entity_types=("PER",),
    attributes_to_find=("birth_date", "account")
)
```

**3. Только счета ВТБ:**
```python
entities = extract_entities_with_attributes(
    text,
    account_owner_patterns=[r'ВТБ', r'Банк\s+ВТБ', r'ПАО\s+«?ВТБ»?']
)
```

**4. Длинный текст — с чанкингом:**
```python
entities = extract_entities_with_attributes(
    text,
    chunk_size_words=300,
    chunk_overlap_words=50
)
```

