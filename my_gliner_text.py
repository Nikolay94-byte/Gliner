import re
from gliner2 import AutoExtractor

# ============================================================================
# КОНСТАНТЫ
# ============================================================================
MODEL_PATH = r"F:\Python projects\Gliner\models\gliner2.5-multi-v1"

# Регулярка для подстраховки ФИО (Фамилия Имя Отчество с падежными окончаниями отчества)
FIO_FALLBACK_REGEX = r'\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:вич|вича|вичу|вичем|виче|вна|вны|вне|вну|вной|ична|ичны|ичне|ичну|ичной|инична|иничны|иничне|иничну|иничной|кызы|улы|оглы)\b'

ORG_FORMS = {
    "ООО", "АО", "ПАО", "НАО", "ЗАО", "ОАО", "ИП", "ГУП", "МУП",
    "ПК", "КФХ", "ХП", "АНО", "НП", "ТСЖ", "СНТ", "ОДО",
    "ФГУП", "ФГБУ", "ГБУ", "МБУ", "ЧОУ", "ЧУ", "ФОНД", "СОЮЗ",
    "ГК", "ФКП", "ФГАУ", "ФГКУ",
    "ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ",
    "ПУБЛИЧНОЕ АКЦИОНЕРНОЕ ОБЩЕСТВО",
    "НЕПУБЛИЧНОЕ АКЦИОНЕРНОЕ ОБЩЕСТВО",
    "АКЦИОНЕРНОЕ ОБЩЕСТВО",
    "ЗАКРЫТОЕ АКЦИОНЕРНОЕ ОБЩЕСТВО",
    "ОТКРЫТОЕ АКЦИОНЕРНОЕ ОБЩЕСТВО",
    "ИНДИВИДУАЛЬНЫЙ ПРЕДПРИНИМАТЕЛЬ",
    "ГОСУДАРСТВЕННОЕ УНИТАРНОЕ ПРЕДПРИЯТИЕ",
    "МУНИЦИПАЛЬНОЕ УНИТАРНОЕ ПРЕДПРИЯТИЕ",
    "ФЕДЕРАЛЬНОЕ ГОСУДАРСТВЕННОЕ УНИТАРНОЕ ПРЕДПРИЯТИЕ",
    "ПРОИЗВОДСТВЕННЫЙ КООПЕРАТИВ",
    "КРЕСТЬЯНСКОЕ (ФЕРМЕРСКОЕ) ХОЗЯЙСТВО",
    "ХОЗЯЙСТВЕННОЕ ПАРТНЕРСТВО",
    "АВТОНОМНАЯ НЕКОММЕРЧЕСКАЯ ОРГАНИЗАЦИЯ",
    "НЕКОММЕРЧЕСКОЕ ПАРТНЕРСТВО",
    "ТОВАРИЩЕСТВО СОБСТВЕННИКОВ НЕДВИЖИМОСТИ",
    "САДОВОДЧЕСКОЕ НЕКОММЕРЧЕСКОЕ ТОВАРИЩЕСТВО",
    "ОБЩЕСТВО С ДОПОЛНИТЕЛЬНОЙ ОТВЕТСТВЕННОСТЬЮ",
    "ФЕДЕРАЛЬНОЕ ГОСУДАРСТВЕННОЕ БЮДЖЕТНОЕ УЧРЕЖДЕНИЕ",
    "ФЕДЕРАЛЬНОЕ ГОСУДАРСТВЕННОЕ АВТОНОМНОЕ УЧРЕЖДЕНИЕ",
    "ГОСУДАРСТВЕННОЕ БЮДЖЕТНОЕ УЧРЕЖДЕНИЕ",
    "МУНИЦИПАЛЬНОЕ БЮДЖЕТНОЕ УЧРЕЖДЕНИЕ",
    "ЧАСТНОЕ ОБРАЗОВАТЕЛЬНОЕ УЧРЕЖДЕНИЕ",
    "ЧАСТНОЕ УЧРЕЖДЕНИЕ",
    "БЛАГОТВОРИТЕЛЬНЫЙ ФОНД",
    "ОБЩЕСТВЕННАЯ ОРГАНИЗАЦИЯ",
    "РЕЛИГИОЗНАЯ ОРГАНИЗАЦИЯ",
    "ГОСУДАРСТВЕННАЯ КОРПОРАЦИЯ",
    "ГОСУДАРСТВЕННАЯ КОМПАНИЯ",
    "ПУБЛИЧНО-ПРАВОВАЯ КОМПАНИЯ",
}

# ============================================================================
# МЕТКИ ДЛЯ ВСЕХ ТИПОВ СУЩНОСТЕЙ (GLiNER 2.5)
# ============================================================================
DEFAULT_ENTITY_LABELS = {
    "PERSON": {
        "PERSON": [
            "A full name of a person (ФИО человека, Иванов Иван Иванович, Петрова Мария Сергеевна)",
            "NOT a date, NOT a number, NOT an organization"
        ]
    },
    "ORGANIZATION": {
        "ORGANIZATION": [
            "A commercial company name INCLUDING its legal form (ООО «АЛЬФАСТРОЙ», АО «Фрязинский Завод», ПАО Сбербанк)",
            "The entire name of the organization as written in the text",
            "NOT a government agency, NOT a court, NOT a police department, NOT a bank"
        ]
    },
    "DATE": {
        "DATE": [
            "A calendar date in any format (12.12.1994, 12.12.1994 г.р., 14.02.1995 года рождения)",
            "NOT a period, NOT a term, NOT a number"
        ]
    },
    "PII": {
        "PII": [
            "Personally identifiable information: bank account number (20 digits), INN (10-12 digits), SNILS, passport",
            "NOT a phone number, NOT an address"
        ]
    },
    "INN": {
        "INN": [
            "Russian taxpayer identification number (ИНН), exactly 10 or 12 digits",
            "NOT a bank account, NOT a phone number"
        ]
    },
    "ACCOUNT": {
        "ACCOUNT": [
            "Russian bank account number (расчетный счет), exactly 19 or 20 digits",
            "NOT an INN, NOT a phone number, NOT a card number"
        ]
    },
    "LOCATION": {
        "LOCATION": [
            "A geographic location: city, region, district, address (г. Москва, Ростовская область, с. Кшенский)",
            "NOT an organization, NOT a person"
        ]
    },
    "BANK": {
        "BANK": [
            "A bank or credit institution name (ПАО Сбербанк, Банк ВТБ, АО «Альфа-Банк»)",
            "NOT a generic organization, NOT a court"
        ]
    },
}

_model = None


def get_model():
    """Ленивая загрузка GLiNER 2.5 (один раз на процесс)."""
    global _model
    if _model is None:
        print(f"[GLiNER 2.5] Загрузка модели из {MODEL_PATH}...")
        _model = AutoExtractor.from_pretrained(MODEL_PATH, local_files_only=True)
    return _model


def split_text_into_chunks(text, chunk_size, overlap):
    """Разбивает текст на перекрывающиеся куски с реальными абсолютными offset-ами."""
    word_spans = [(m.start(), m.end()) for m in re.finditer(r'\S+', text)]
    chunks = []
    start = 0
    while start < len(word_spans):
        end = min(start + chunk_size, len(word_spans))
        char_start = word_spans[start][0]
        char_end = word_spans[end - 1][1]
        chunks.append({
            "text": text[char_start:char_end],
            "char_start": char_start,
            "char_end": char_end,
        })
        if end == len(word_spans):
            break
        start += (chunk_size - overlap)
    return chunks


def _parse_gliner25_result(result):
    """Приводит ответ GLiNER 2.5 к списку {start, end, text, label, confidence}."""
    entities = []
    if isinstance(result, dict) and 'entities' in result:
        for label, items in result['entities'].items():
            for item in items:
                entities.append({
                    "start": item["start"],
                    "end": item["end"],
                    "text": item["text"],
                    "label": label,
                    "confidence": item.get("confidence", 1.0),
                })
    else:
        for ent in result:
            entities.append({
                "start": ent["start"],
                "end": ent.get("end", ent.get("stop")),
                "text": ent["text"],
                "label": ent.get("label", ent.get("type")),
                "confidence": ent.get("confidence", 1.0),
            })
    return entities


# ============================================================================
# ВТОРОЙ РЕЖИМ: сущности + (опционально) окно поиска атрибутов
# ============================================================================
def extract_entities_text(
        text,

        # ====================================================================
        # 1. ЧТО ИСКАТЬ
        # ====================================================================
        entity_types=("PERSON", "ORGANIZATION"),
        # Метки GLiNER 2.5 для поиска.
        # "PERSON" — люди (ФИО), "ORGANIZATION" — организации, "DATE" — даты,
        # "PII" — общий PII, "INN" — ИНН, "ACCOUNT" — счета,
        # "LOCATION" — локации, "BANK" — банки.
        # Пример: ("PERSON",) — искать только людей.
        # Пример: ("PERSON", "DATE", "ACCOUNT") — люди, даты, счета.

        entity_labels=None,
        # Полный словарь меток по типам: {type: {label: [описания]}}.
        # Если None, используется DEFAULT_ENTITY_LABELS.
        # Позволяет переопределить описания для любого типа.

        # ====================================================================
        # 2. ФИЛЬТРЫ ДЛЯ ОРГАНИЗАЦИЙ
        # ====================================================================
        ignore_org_patterns=None,
        # СПИСОК РЕГУЛЯРОК для отсева организаций.
        # Проверяется ТОЛЬКО текст самой сущности (после склейки ORG и ОПФ).
        # Если None или пустой список — фильтрация не применяется.

        # ====================================================================
        # 3. ФИЛЬТРЫ ДЛЯ ФИО
        # ====================================================================
        ignore_person_patterns=None,
        # СПИСОК РЕГУЛЯРОК для отсева ФИО по КОНТЕКСТУ (50 символов перед именем).
        # Если None или пустой список — фильтрация не применяется.

        ignore_initials=True,
        # Флаг: игнорировать ли ФИО с инициалами.
        # True — "И.С. Иванов" будет отсеян (по умолчанию).
        # False — инициалы разрешены.

        # ====================================================================
        # 4. ОКНО ПОИСКА АТРИБУТОВ
        # ====================================================================
        window_left_margin=300,
        # Насколько символов смотреть НАЛЕВО от сущности при построении окна.
        # Окно: [max(block_start, span.start - window_left_margin), block_end).

        return_window=True,
        # Если True — возвращать сущности с окном (window).
        # Если False — только {entity, type, start, stop} без окна.

        # ====================================================================
        # 5. ИНДИВИДУАЛЬНЫЕ ПОРОГИ УВЕРЕННОСТИ ПО ТИПАМ
        # ====================================================================
        per_type_thresholds=None,
        # СЛОВАРЬ индивидуальных порогов уверенности по типам сущностей.
        # Ключи — метки GLiNER 2.5 ("PERSON", "ORGANIZATION", "DATE", "PII",
        # "INN", "ACCOUNT", "LOCATION", "BANK"). Значения — float 0.0–1.0.
        # Для типов, которых нет в словаре, порог не применяется (0.0).
        #
        # Пример:
        #   per_type_thresholds={"PERSON": 0.7, "ORGANIZATION": 0.3, "DATE": 0.5}
        #
        # Если None — фильтрация по confidence не применяется.
        # По умолчанию 0,1

        # ====================================================================
        # 6. ЧАНКИНГ (РАЗБИВКА ДЛИННОГО ТЕКСТА)
        # ====================================================================
        chunk_size_words=None,
        # Размер куска в словах.
        # Если None (по умолчанию) — текст не делится на чанки.

        chunk_overlap_words=None
        # Перекрытие между кусками в словах.
        # Используется, только если задан chunk_size_words.
):
    """Возвращает сущности + (опционально) окно поиска атрибутов.

    Формат при return_window=True:
    [
      {
        "entity": str, "type": str, "start": int, "stop": int,
        "window": {"text": str, "start": int, "stop": int}
      }, ...
    ]

    Формат при return_window=False:
    [
      {"entity": str, "type": str, "start": int, "stop": int}, ...
    ]

    Тип в результате — метка GLiNER 2.5 ("PERSON", "ORGANIZATION", "DATE", ...).

    per_type_thresholds — словарь {тип: порог} для фильтрации по confidence.
    Типы, которых нет в словаре, не фильтруются.
    """
    if entity_labels is None:
        entity_labels = DEFAULT_ENTITY_LABELS

    # Собираем метки для запрошенных типов
    final_labels = {}
    for entity_type in entity_types:
        if entity_type in entity_labels:
            labels = entity_labels[entity_type]
        elif entity_type in DEFAULT_ENTITY_LABELS:
            labels = DEFAULT_ENTITY_LABELS[entity_type]
        else:
            continue

        for label, desc in labels.items():
            final_labels[label] = [desc] if isinstance(desc, str) else desc

    compiled_ignore_orgs = [re.compile(pattern, re.IGNORECASE) for pattern in (ignore_org_patterns or [])]
    compiled_ignore_persons = [re.compile(pattern, re.IGNORECASE) for pattern in (ignore_person_patterns or [])]

    model = get_model()

    # ========================================================================
    # ЧАНКИНГ И ПОИСК СУЩНОСТЕЙ (GLiNER 2.5)
    # ========================================================================
    if chunk_size_words is not None:
        overlap = chunk_overlap_words or 0
        chunks = split_text_into_chunks(text, chunk_size_words, overlap)
        all_raw_entities = []

        for chunk in chunks:
            chunk_text = chunk["text"]
            offset = chunk["char_start"]

            result = model.extract_entities(
                chunk_text, final_labels, threshold=0.1,
                include_spans=True, include_confidence=True,
            )
            chunk_entities = _parse_gliner25_result(result)

            for entity in chunk_entities:
                entity["start"] += offset
                entity["end"] += offset
                all_raw_entities.append(entity)

        unique_entities = []
        seen_keys = set()
        for entity in all_raw_entities:
            key = (entity["text"], entity["start"] // 10)
            if key not in seen_keys:
                seen_keys.add(key)
                unique_entities.append(entity)
        raw_entities = unique_entities
    else:
        result = model.extract_entities(
            text, final_labels, threshold=0.1,
            include_spans=True, include_confidence=True,
        )
        raw_entities = _parse_gliner25_result(result)

    # ========================================================================
    # ФИЛЬТРАЦИЯ ПО ИНДИВИДУАЛЬНЫМ ПОРОГАМ (per_type_thresholds)
    # ========================================================================
    if per_type_thresholds:
        filtered_by_confidence = []
        for entity in raw_entities:
            type_threshold = per_type_thresholds.get(entity['label'], 0.0)
            if entity.get('confidence', 1.0) >= type_threshold:
                filtered_by_confidence.append(entity)
        raw_entities = filtered_by_confidence

    # ========================================================================
    # ПОДСТРАХОВКА (FALLBACK) ДЛЯ ФИО
    # ========================================================================
    if "PERSON" in entity_types:
        existing_per_stems = set()
        for entity in raw_entities:
            if entity['label'] == 'PERSON':
                words = entity['text'].split()
                if words and len(words[0]) >= 5:
                    existing_per_stems.add(words[0][:5].lower())

        for match in re.finditer(FIO_FALLBACK_REGEX, text):
            fallback_text = match.group()
            words = fallback_text.split()
            if not words or len(words[0]) < 5:
                continue

            fallback_stem = words[0][:5].lower()
            if fallback_stem in existing_per_stems:
                continue

            raw_entities.append({
                "start": match.start(),
                "end": match.end(),
                "text": fallback_text,
                "label": "PERSON",
                "confidence": 1.0,
            })

    # ========================================================================
    # ШАГ 1. СКЛЕЙКА СОСЕДНИХ ORG + ПРИКЛЕИВАНИЕ ОПФ
    # ========================================================================
    raw_sorted = sorted(raw_entities, key=lambda entity: entity["start"])

    merged_entities = []
    for entity in raw_sorted:
        merged_entities.append({
            'start': entity["start"],
            'stop': entity["end"],
            'text': entity["text"],
            'type': entity["label"],
            'cluster_key': re.sub(r'[«»"\s]', '', entity["text"].lower()),
        })

    merged_entities.sort(key=lambda entity: entity['start'])

    index = 1
    while index < len(merged_entities):
        current = merged_entities[index]
        previous = merged_entities[index - 1]

        if current['type'] == 'ORGANIZATION' and previous['type'] == 'ORGANIZATION':
            between = text[previous['stop']:current['start']]
            if re.fullmatch(r'[\s«»"\-–—]*', between):
                if previous['text'].upper() in ORG_FORMS:
                    current['text'] = f"{previous['text']} {current['text']}"
                    current['start'] = previous['start']
                    current['cluster_key'] = re.sub(r'[«»"\s]', '', current['text'].lower())
                    merged_entities.pop(index - 1)
                    index -= 1
                    continue
                else:
                    previous['text'] = f"{previous['text']} {current['text']}"
                    previous['stop'] = current['stop']
                    previous['cluster_key'] = re.sub(r'[«»"\s]', '', previous['text'].lower())
                    merged_entities.pop(index)
                    continue
        index += 1

    sorted_forms = sorted(ORG_FORMS, key=len, reverse=True)
    opf_pattern = r'\b(' + '|'.join(re.escape(form) for form in sorted_forms) + r')\b'

    for entity in merged_entities:
        if entity['type'] != 'ORGANIZATION':
            continue

        words = entity['text'].split()
        already_has_opf = False
        if words:
            first_word = words[0].upper()
            if first_word in ORG_FORMS:
                already_has_opf = True
            elif len(words) > 1:
                two_words = f"{words[0]} {words[1]}".upper()
                if two_words in ORG_FORMS:
                    already_has_opf = True

        if already_has_opf:
            continue

        left_start = max(0, entity['start'] - 100)
        left_text = text[left_start:entity['start']]

        matches = list(re.finditer(opf_pattern, left_text, re.IGNORECASE))
        if matches:
            match = matches[-1]
            opf = match.group(1).upper()
            entity['text'] = f"{opf} {entity['text']}"
            entity['start'] = left_start + match.start()
            entity['cluster_key'] = re.sub(r'[«»"\s]', '', entity['text'].lower())

    # ========================================================================
    # ШАГ 2. ФИЛЬТРАЦИЯ
    # ========================================================================
    filtered_entities = []
    for entity in merged_entities:
        entity_text = entity["text"]
        entity_type = entity["type"]

        if entity_type == "ORGANIZATION":
            if any(pattern.search(entity_text) for pattern in compiled_ignore_orgs):
                continue

        if entity_type == "PERSON":
            context_start = max(0, entity["start"] - 50)
            context_text = text[context_start:entity["stop"]]  # ← включаем саму сущность
            if any(pattern.search(context_text) for pattern in compiled_ignore_persons):
                continue
            if ignore_initials and re.search(r'[А-ЯЁA-Z]\.[А-ЯЁA-Z]?\.?', entity_text):
                continue

        if entity_type == "ORGANIZATION" and entity_text.upper() in ORG_FORMS:
            continue

        filtered_entities.append(entity)

    filtered_entities.sort(key=lambda entity: entity['start'])

    # ========================================================================
    # ШАГ 3. КЛАСТЕРИЗАЦИЯ
    # ========================================================================
    clusters = {}
    for span in filtered_entities:
        if span['type'] == 'PERSON':
            words = span['text'].split()
            key_parts = [word[:3].lower() for word in words[:3]]
            key = "".join(key_parts)
        else:
            key = span['cluster_key']

        if key not in clusters:
            clusters[key] = {
                'start': span['start'],
                'stop': span['stop'],
                'text': span['text'],
                'type': span['type'],
            }
        else:
            clusters[key]['stop'] = max(clusters[key]['stop'], span['stop'])

    merged_spans = list(clusters.values())
    merged_spans.sort(key=lambda span: span['start'])

    # ========================================================================
    # ШАГ 4. ФОРМИРОВАНИЕ РЕЗУЛЬТАТА
    # ========================================================================
    results = []

    for span_index, span in enumerate(merged_spans):
        item = {
            'entity': span['text'],
            'type': span['type'],
            'start': span['start'],
            'stop': span['stop'],
        }

        if return_window:
            block_end = len(text) if span_index + 1 == len(merged_spans) else merged_spans[span_index + 1]['start']
            block_start = 0 if span_index == 0 else merged_spans[span_index - 1]['stop']

            window_start = max(block_start, span['start'] - window_left_margin)
            window_end = block_end

            item['window'] = {
                'text': text[window_start:window_end],
                'start': window_start,
                'stop': window_end,
            }

        results.append(item)

    return results