import re
from gliner2 import AutoExtractor

# ============================================================================
# КОНСТАНТЫ
# ============================================================================
MODEL_PATH = r"F:\Python projects\Gliner\models\gliner2.5-multi-v1"

DEFAULT_INN_REGEX = r'\b(\d{10,12})\b'
DEFAULT_BIRTH_DATE_REGEX = r'\b(\d{2}\.\d{2}\.\d{4})\b'
DEFAULT_ACCOUNT_REGEX = r'\b(\d{19,20})\b'

DEFAULT_BIRTH_DATE_MARKERS = [r'года\s+рождения', r'г\.р\.', r'родил']

# Метки для GLiNER 2.5 (zero-shot описания)
DEFAULT_PERSON_LABELS = {
    "PERSON": "A full name of a person (ФИО человека, Иванов Иван Иванович, Петрова Мария Сергеевна)"
}
DEFAULT_ORG_LABELS = {
    "ORGANIZATION": "A commercial company name INCLUDING its legal form (ООО «АЛЬФАСТРОЙ», АО «Фрязинский Завод», ПАО Сбербанк)"
}

# Регулярка для подстраховки ФИО
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

TOP_RUSSIAN_BANKS = [
    r"Сбербанк", r"ВТБ", r"ГПБ", r"Газпромбанк", r"АЛЬФА\W{0,3}БАНК",
    r"НКО\W{0,3}НКЦ", r"ТБанк", r"Т\W{0,3}Банк", r"Тинькофф",
    r"Россельхозбанк", r"МОСКОВСКИЙ\W{0,3}КРЕДИТНЫЙ\W{0,3}БАНК", r"МКБ",
    r"Банк\W{0,3}ДОМ\.РФ", r"Совкомбанк", r"Райффайзенбанк", r"БМ\W{0,3}Банк",
    r"НКО\W{0,3}АО\W{0,3}НРД", r"НОВИКОМБАНК", r"АБ\W{0,3}РОССИЯ",
    r"Банк\W{0,3}Санкт\W{0,3}Петербург", r"Уралсиб", r"ОТП\W{0,3}Банк",
    r"МТС\W{0,3}Банк", r"ЮниКредит\W{0,3}Банк", r"Ozon\W{0,3}Банк", r"Озон\W{0,3}Банк",
    r"Национальный\W{0,3}Резервный\W{0,3}Банк", r"НРБанк", r"Дж\.\W{0,3}П\.\W{0,3}Морган\W{0,3}Банк",
    r"Банк\W{0,3}ТКБ", r"ТКБ", r"Почта\W{0,3}Банк", r"Точка",
    r"Азиатско\W{0,3}Тихоокеанский\W{0,3}банк", r"АТБ", r"Экспобанк",
    r"Абсолют\W{0,3}Банк", r"Кредит\W{0,3}Европа\W{0,3}Россия", r"Зенит",
    r"Аверс", r"Металлинвестбанк", r"Локо\W{0,3}Банк", r"Росэксимбанк",
    r"УБРИР", r"ВБ\W{0,3}Банк", r"Кубань\W{0,3}Кредит", r"Авто\W{0,3}Финанс\W{0,3}Банк",
    r"ББР\W{0,3}Банк", r"Русский\W{0,3}Стандарт", r"Синара", r"Примсоцбанк",
    r"Газэнергобанк", r"Меткомбанк", r"Левобережный", r"Центр\W{0,3}Инвест",
    r"Инго", r"МСП\W{0,3}Банк", r"БКС\W{0,3}Банк", r"ДенизМосква",
    r"Чайна\W{0,3}Констракшн\W{0,3}Банк", r"Ренессанс\W{0,3}Кредит", r"Интеза", r"Траст",
    r"СДМ\W{0,3}Банк", r"СНГБ", r"СМБСР\W{0,3}Банк", r"Фора\W{0,3}Банк",
    r"Инвестторгбанк", r"Коммерческий\W{0,3}Индо\W{0,3}Банк", r"Прио\W{0,3}Внешторгбанк",
    r"АРЕСБАНК", r"Эс\W{0,3}Би\W{0,3}Ай\W{0,3}Банк", r"Ури\W{0,3}Банк",
    r"Мидзухо\W{0,3}Банк", r"Цифра\W{0,3}банк", r"банк\W{0,3}Раунд",
    r"МБА\W{0,3}МОСКВА", r"ТАТСОЦБАНК", r"Белгородсоцбанк", r"Банк\W{0,3}Акцепт",
    r"НС\W{0,3}Банк", r"КОШЕЛЕВ\W{0,3}БАНК", r"Урал\W{0,3}ФД",
    r"Унифондбанк", r"БАЛТИНВЕСТБАНК", r"Свой\W{0,3}Банк", r"Энергобанк",
    r"Первый\W{0,3}Инвестиционный\W{0,3}Банк", r"АК\W{0,3}БАРС", r"АКИБАНК",
    r"Акцепт", r"Александровский", r"Алеф\W{0,3}Банк", r"Алмазэргиэнбанк",
    r"Альба\W{0,3}Альянс", r"Америкэн\W{0,3}Экспресс\W{0,3}Банк", r"Апабанк",
    r"Ассоциация", r"Атон", r"Байкалинвестбанк", r"Байкальский\W{0,3}Банк",
    r"Балтийский\W{0,3}Банк", r"Балтийский\W{0,3}Банк\W{0,3}Развития",
    r"Балтика", r"Балткредобанк", r"Балтсоцкомбанк", r"Банк\W{0,3}Агора",
    r"Банк\W{0,3}Берейт", r"Банк\W{0,3}Венец", r"Банк\W{0,3}Далена",
    r"Банк\W{0,3}Жилищного\W{0,3}Финансирования", r"Банк\W{0,3}Казани",
    r"Банк\W{0,3}Клиентский", r"Банк\W{0,3}Кредит\W{0,3}Свисс",
    r"Банк\W{0,3}Кузнецкий", r"Банк\W{0,3}Левобережный", r"Банк\W{0,3}Металлург",
    r"Банк\W{0,3}Москва", r"Банк\W{0,3}Нейва", r"Банк\W{0,3}Новый\W{0,3}Символ",
    r"Банк\W{0,3}Образование", r"Банк\W{0,3}Открытие", r"Банк\W{0,3}Первомайский",
    r"Банк\W{0,3}Приморье", r"Банк\W{0,3}ПСКБ", r"Банк\W{0,3}Российский\W{0,3}Кредит",
    r"Банк\W{0,3}Саратов", r"Банк\W{0,3}Снежинский", r"Банк\W{0,3}Солидарность",
    r"Банк\W{0,3}Союз", r"Банк\W{0,3}Столица", r"Банк\W{0,3}Таврический",
    r"Банк\W{0,3}Тамбовкредитпромбанк", r"Банк\W{0,3}Тендер", r"Банк\W{0,3}Тетраполис",
    r"Банк\W{0,3}Уссури", r"Банк\W{0,3}Финсервис", r"Банк\W{0,3}Фридом",
    r"Банк\W{0,3}Хоум\W{0,3}Кредит", r"Банк\W{0,3}ЦентроКредит", r"Банк\W{0,3}Челиндбанк",
    r"Банк\W{0,3}Элита", r"Банк\W{0,3}Энергомашбанк",
    r"Банк\W{0,3}Югра", r"Бинбанк", r"Братский\W{0,3}Банк", r"Быстробанк",
    r"Вайлдберриз\W{0,3}Банк", r"ВБ\W{0,3}Банк", r"Великие\W{0,3}Луки\W{0,3}Банк",
    r"Волга\W{0,3}Кредит\W{0,3}Банк", r"Волгопромбанк", r"Воронежский\W{0,3}Банк",
    r"Восточный\W{0,3}Банк", r"ВУЗ\W{0,3}Банк", r"Газтрансбанк",
    r"Гарант\W{0,3}Инвест", r"Глобал\W{0,3}Банк", r"Голдман\W{0,3}Сакс\W{0,3}Банк",
    r"Городской\W{0,3}Банк", r"Гринфилдбанк", r"Гута\W{0,3}Банк", r"Дальневосточный\W{0,3}Банк",
    r"Девон\W{0,3}Кредит", r"Джей\W{0,3}Энд\W{0,3}Ти\W{0,3}Банк", r"Дзержинский\W{0,3}Банк",
    r"Диамант\W{0,3}Банк", r"Дил\W{0,3}Банк", r"Дом\W{0,3}Банк",
    r"Дон\W{0,3}Кредит\W{0,3}Банк", r"Донской\W{0,3}Банк", r"Драйв\W{0,3}Клик\W{0,3}Банк",
    r"ЕвроАзиатский\W{0,3}Банк", r"Евроситибанк", r"Енисей",
    r"Заречье", r"Заубер\W{0,3}Банк", r"Земский\W{0,3}Банк", r"Зираат\W{0,3}Банк",
    r"Идея\W{0,3}Банк", r"Изберком", r"Икано\W{0,3}Банк", r"Инбанк",
    r"Инвестиционный\W{0,3}Банк", r"ИнвестКапиталБанк", r"Индустриальный\W{0,3}Банк",
    r"Иннопром\W{0,3}Банк", r"Интерпрогрессбанк", r"Интехбанк",
    r"ИРИС\W{0,3}Банк", r"Итуруп\W{0,3}Банк", r"Йошкар\W{0,3}Ола\W{0,3}Банк",
    r"Казанский\W{0,3}Банк", r"Камчатка\W{0,3}Банк", r"Капитал\W{0,3}Банк",
    r"Кетовский\W{0,3}Банк", r"Киви\W{0,3}Банк", r"КИТ\W{0,3}Финанс",
    r"Классик\W{0,3}Банк", r"Клинский\W{0,3}Банк", r"Ковровский\W{0,3}Банк",
    r"Колыма\W{0,3}Банк", r"Коммерцбанк",
]

_model = None


def get_model():
    global _model
    if _model is None:
        print(f"[GLiNER 2.5] Загрузка модели...")
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


def _finditer_abs(regex, text, slice_start, slice_end):
    """Ищет regex в text[slice_start:slice_end], возвращает список dict с абсолютными координатами."""
    result = []
    for match in regex.finditer(text, slice_start, slice_end):
        if match.groups():
            value_start = match.start(1)
            value_stop = match.end(1)
            value = match.group(1)
        else:
            value_start = match.start()
            value_stop = match.end()
            value = match.group(0)
        result.append({"value": value, "start": value_start, "stop": value_stop})
    return result


def _select_accounts_by_bank(
        text,
        account_matches,
        window_start,
        window_end,
        compiled_owners,
        compiled_bank_markers,
):
    """Оставляет только счета, привязанные к owner-банкам (логика не менялась)."""
    if not compiled_owners:
        return account_matches
    if not account_matches:
        return []

    owner_occurrences = []
    for owner_regex in compiled_owners:
        for match in owner_regex.finditer(text, window_start, window_end):
            owner_occurrences.append({"start": match.start(), "stop": match.end()})
    owner_occurrences.sort(key=lambda occ: occ["start"])

    bank_occurrences = []
    for bank_regex in compiled_bank_markers:
        for match in bank_regex.finditer(text, window_start, window_end):
            bank_occurrences.append({"start": match.start(), "stop": match.end()})
    bank_occurrences.extend(owner_occurrences)
    bank_occurrences.sort(key=lambda occ: occ["start"])

    if not bank_occurrences:
        return []
    if not owner_occurrences:
        return []

    first_bank = bank_occurrences[0]
    accounts_before_first_bank = any(
        acc["start"] < first_bank["start"] for acc in account_matches
    )
    direction = "account_to_bank" if accounts_before_first_bank else "bank_to_account"

    selected = []
    seen_keys = set()
    for owner in owner_occurrences:
        if direction == "bank_to_account":
            segment_start = owner["stop"]
            next_banks = [b for b in bank_occurrences if b["start"] >= owner["stop"]]
            segment_end = next_banks[0]["start"] if next_banks else window_end
        else:
            segment_end = owner["start"]
            prev_banks = [b for b in bank_occurrences if b["stop"] <= owner["start"]]
            segment_start = prev_banks[-1]["stop"] if prev_banks else window_start

        for acc in account_matches:
            if acc["start"] < segment_start or acc["stop"] > segment_end:
                continue
            key = (acc["value"], acc["start"])
            if key in seen_keys:
                continue
            seen_keys.add(key)
            selected.append(acc)

    selected.sort(key=lambda acc: acc["start"])
    return selected


def _predict_entities_gliner25(text, final_labels, threshold=0.1):
    """Обёртка над GLiNER 2.5: возвращает список {start, end, text, label}.

    Приводит формат GLiNER 2.5 к тому, что ожидает остальной код:
    'end' вместо 'stop', 'label' вместо 'type'.
    """
    model = get_model()
    result = model.extract_entities(
        text,
        final_labels,
        threshold=threshold,
        include_spans=True,
        include_confidence=True,
    )

    entities = []
    if isinstance(result, dict) and 'entities' in result:
        for label, items in result['entities'].items():
            for item in items:
                entities.append({
                    "start": item["start"],
                    "end": item["end"],
                    "text": item["text"],
                    "label": label,
                })
    else:
        for ent in result:
            entities.append({
                "start": ent["start"],
                "end": ent.get("end", ent.get("stop")),
                "text": ent["text"],
                "label": ent.get("label", ent.get("type")),
            })
    return entities


def extract_entities_with_attributes(
        text,

        # ====================================================================
        # 1. ЧТО ИСКАТЬ
        # ====================================================================
        entity_types=("PER", "ORG"),

        person_labels=None,
        org_labels=None,

        # ====================================================================
        # 2. ФИЛЬТРЫ ДЛЯ ОРГАНИЗАЦИЙ
        # ====================================================================
        ignore_org_patterns=None,

        # ====================================================================
        # 3. ФИЛЬТРЫ ДЛЯ ФИО
        # ====================================================================
        ignore_person_patterns=None,
        ignore_initials=True,

        # ====================================================================
        # 4. РЕГУЛЯРКИ ДЛЯ АТРИБУТОВ
        # ====================================================================
        inn_pattern=DEFAULT_INN_REGEX,
        birth_date_pattern=DEFAULT_BIRTH_DATE_REGEX,
        account_pattern=DEFAULT_ACCOUNT_REGEX,
        birth_date_markers=None,

        # ====================================================================
        # 5. КАКИЕ АТРИБУТЫ ИСКАТЬ
        # ====================================================================
        attributes_to_find=("inn", "birth_date", "account"),

        # ====================================================================
        # 6. ФИЛЬТРАЦИЯ СЧЕТОВ ПО БАНКУ/ВЛАДЕЛЬЦУ
        # ====================================================================
        account_owner_patterns=None,
        account_ignore_patterns=None,

        # ====================================================================
        # 7. ЧАНКИНГ
        # ====================================================================
        chunk_size_words=None,
        chunk_overlap_words=None
):
    if person_labels is None:
        person_labels = DEFAULT_PERSON_LABELS
    if org_labels is None:
        org_labels = DEFAULT_ORG_LABELS
    if birth_date_markers is None:
        birth_date_markers = DEFAULT_BIRTH_DATE_MARKERS

    # Собираем метки в формате GLiNER 2.5: dict {label: [описания]}
    final_labels = {}
    if "PER" in entity_types:
        for label, desc in person_labels.items():
            final_labels[label] = [desc] if isinstance(desc, str) else desc
    if "ORG" in entity_types:
        for label, desc in org_labels.items():
            final_labels[label] = [desc] if isinstance(desc, str) else desc

    compiled_ignore_orgs = [re.compile(pattern, re.IGNORECASE) for pattern in (ignore_org_patterns or [])]
    compiled_ignore_persons = [re.compile(pattern, re.IGNORECASE) for pattern in (ignore_person_patterns or [])]
    compiled_birth_date_markers = [re.compile(pattern, re.IGNORECASE) for pattern in birth_date_markers]

    compiled_account_owners = [
        re.compile(owner_pattern, re.IGNORECASE)
        for owner_pattern in (account_owner_patterns or [])
    ]

    ignore_bank_patterns = []
    for bank_pattern in TOP_RUSSIAN_BANKS:
        is_owner = any(
            re.search(owner_pattern, bank_pattern, re.IGNORECASE)
            or re.search(bank_pattern, owner_pattern, re.IGNORECASE)
            for owner_pattern in (account_owner_patterns or [])
        )
        if not is_owner:
            ignore_bank_patterns.append(bank_pattern)

    if account_ignore_patterns:
        ignore_bank_patterns.extend(account_ignore_patterns)

    compiled_account_ignores = [
        re.compile(bank_pattern, re.IGNORECASE)
        for bank_pattern in ignore_bank_patterns
    ]

    active_attributes = {}
    if attributes_to_find:
        if "inn" in attributes_to_find:
            active_attributes["inn"] = {
                "regex": re.compile(inn_pattern),
                "applies_to": {"ORG"},
            }
        if "birth_date" in attributes_to_find:
            active_attributes["birth_date"] = {
                "regex": re.compile(birth_date_pattern),
                "applies_to": {"PER"},
            }
        if "account" in attributes_to_find:
            active_attributes["account"] = {
                "regex": re.compile(account_pattern),
                "applies_to": {"PER", "ORG"},
            }

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

            chunk_entities = _predict_entities_gliner25(chunk_text, final_labels, threshold=0.1)

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
        raw_entities = _predict_entities_gliner25(text, final_labels, threshold=0.1)

    # ========================================================================
    # ПОДСТРАХОВКА (FALLBACK) ДЛЯ ФИО
    # ========================================================================
    if "PER" in entity_types:
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
            context_text = text[context_start:entity["start"]]
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

    if not active_attributes:
        return [{
            'entity': span['text'],
            'type': 'PER' if span['type'] == 'PERSON' else 'ORG',
            'start': span['start'],
            'stop': span['stop'],
            'attributes': {},
        } for span in merged_spans]

    # ========================================================================
    # ШАГ 4. ПОИСК АТРИБУТОВ (без изменений)
    # ========================================================================
    results = []
    used_accounts = set()

    for span_index, span in enumerate(merged_spans):
        entity_text = span['text']
        entity_type = 'PER' if span['type'] == 'PERSON' else 'ORG'

        block_end = len(text) if span_index + 1 == len(merged_spans) else merged_spans[span_index + 1]['start']
        block_start = 0 if span_index == 0 else merged_spans[span_index - 1]['stop']

        search_start = max(block_start, span['start'] - 300)
        search_end = block_end

        found_attributes = {}

        for attribute_name, attribute_info in active_attributes.items():
            if entity_type not in attribute_info["applies_to"]:
                found_attributes[attribute_name] = None if attribute_name != "account" else []
                continue

            regex = attribute_info["regex"]

            if attribute_name == "birth_date":
                chosen = None

                inside = _finditer_abs(regex, text, span['start'], span['stop'])
                explicit_inside = []
                for item in inside:
                    before_context = text[max(0, item["start"] - 30):item["start"]]
                    if any(pattern.search(before_context) for pattern in compiled_birth_date_markers):
                        explicit_inside.append(item)
                if explicit_inside:
                    chosen = explicit_inside[0]
                elif inside:
                    chosen = inside[0]
                else:
                    after = _finditer_abs(regex, text, span['stop'], search_end)
                    explicit_after = []
                    for item in after:
                        before_context = text[max(0, item["start"] - 30):item["start"]]
                        if any(pattern.search(before_context) for pattern in compiled_birth_date_markers):
                            explicit_after.append(item)
                    if explicit_after:
                        chosen = explicit_after[0]
                    elif after:
                        chosen = after[0]
                    else:
                        before = _finditer_abs(regex, text, search_start, span['start'])
                        if before:
                            chosen = before[-1]

                found_attributes[attribute_name] = chosen

            elif attribute_name == "inn":
                matches = _finditer_abs(regex, text, search_start, search_end)
                found_attributes[attribute_name] = matches[0] if matches else None

            elif attribute_name == "account":
                matches = _finditer_abs(regex, text, search_start, search_end)

                if compiled_account_owners or compiled_account_ignores:
                    matches = _select_accounts_by_bank(
                        text=text,
                        account_matches=matches,
                        window_start=search_start,
                        window_end=search_end,
                        compiled_owners=compiled_account_owners,
                        compiled_bank_markers=compiled_account_ignores,
                    )

                unique_accounts = []
                for item in matches:
                    key = (item["value"], item["start"])
                    if key in used_accounts:
                        continue
                    used_accounts.add(key)
                    unique_accounts.append(item)
                found_attributes[attribute_name] = unique_accounts

        results.append({
            'entity': entity_text,
            'type': entity_type,
            'start': span['start'],
            'stop': span['stop'],
            'attributes': found_attributes,
        })

    return results