import os
import re
from my_gliner_ner import (
    extract_entities_with_attributes,
    get_model,
    DEFAULT_PERSON_LABELS,
    DEFAULT_ORG_LABELS,
    ORG_FORMS,
)

TEXTS_DIR = r"F:\Python projects\Gliner\data\debtors_vtb_account_numbers"

# ============================================================================
# ДАННЫЕ ИЗ EXCEL (ЛИСТ 2: "ВСЕ СЧЕТА")
# ============================================================================
DATASET_ALL = {
    "004174_564.txt": [
        ("Ивановой Марии Сергеевны", "12.12.1994", ["40800010990000123456"], None),
    ],
    "004174_564 усложненный на тестирование окна поиска перед сущностью.txt": [
        ("Ивановой Марии Сергеевны", "12.12.1994", ["40800010990000123456"], None),
        ("Ивановой Ольги Сергеевны", "12.12.1995", ["40800010990000123457"], None),
        ("Ивановой Натальи Сергеевны", "12.12.1996", ["40800010990000123458"], None),
    ],
    "доп_1_2026-06-11_11-30-50_1.txt": [
        ("Ощепковой Зины Алексеевны", "05.11.2004", [
            "40800010100108209565", "40000810800108341325", "40000810211009025774",
            "42301800011000282646", "40817810000003388773", "42307800011142757981",
            "42307800011000111608", "40817810001005111300", "40817000852221116767",
            "40914111226000000044", "40817111220000017108", "40817111605000903063",
            "40911110900000040781"
        ], None),
    ],
    "доп_2-225_копия_2026-06-08-15-36-55.txt": [
        ("Иванову Ивану Ивановичу", "14.02.1995", [], None),
    ],
    "пример с разрывом сущности.txt": [
        ("Иванову Ивану Ивановичу", "14.02.1995", ["12345678911234567891"], None),
    ],
    "доп_442117(1).txt": [
        ("Устанчук Дмитрия Сергеевича", "18.09.1986", [
            "40817800026001116091", "4081000002600111385", "40810008026001116066"
        ], None),
        ("Пупкина Ивана Охлабыстовича", "13.09.1996", [
            "40817800026001116094", "4080004022601112609"
        ], None),
    ],
    "доп_442117.txt": [
        ("Устанчук Дмитрия Сергеевича", "18.09.1986", [
            "40817840111004000091", "4081781002111000385", "40811118026000006066"
        ], None),
    ],
    "неск_должников_286133.txt": [
        ("ООО «АЛЬФАСТРОЙ»", None, [
            "40701110701000000106", "40701110225630002518", "40701110600010000055"
        ], "7711134567"),
        ("Петрова Николая Анатольевича", "29.04.1971", [
            "40811110206000042066", "40817111000450000155", "40817111000330155800",
            "40817111000206858510", "4081111000061965156", "40811110000130632709",
            "40817111000000069013"
        ], None),
        ("Сидоровой Елены Викторовны", "09.10.1971", [
            "40817811110005830032", "42301110008065806382", "42307811110006009081",
            "40817811100030257736", "40817811100054008660", "40817811100061966863",
            "40811110400061966852", "42301110700200035707", "42301110400200050436",
            "40817111000330160933", "40811110006330160934", "40817111100020565501"
        ], None),
        ("Петрова Артема Витальевича", "01.11.2002", [
            "40817811100065841739", "40811110008065835490", "40817111000602953594",
            "40817111000043592598", "40817111000002795050", "40817111000600769943",
            "40817111000230010342", "40817810111000015270", "40817111000890323623"
        ], None),
    ],
    "неск_постановлений_280501_1.txt": [
        ("Иванова Петра Сергеевича", "14.06.1998", [
            "40811110000012345678", "40817111000005098765", "40817810111000456789",
            "40811100008004010070", "40111000508004009242", "40811100001782033274",
            "4081111000012881438"
        ], None),
        ("Сидорова Юрия Владимировича", "12.06.1999", [
            "42301110008700611406", "40811110008125735756", "40811110008120037674",
            "40811110008128654161", "40811110008129195799", "40811110008129307442",
            "40811110000006740095", "42301811100071207675", "40817111000130007030",
            "40814111000130049460", "40817911100030006133", "40817711100030000062",
            "40811110006130002654", "40811110004013520559", "42303811100030001907",
            "40811110000180103710", "42305111000180175428", "40111000209254045086",
            "40817811100057049467", "42303810011100006194", "42306810111000300440",
            "42301110008000000088", "42304911100000000002", "42303810111000416326",
            "40817811100086005119", "40817810111000123055", "42305811100000186986"
        ], None),
    ],
    "неск_постановлений_280501_2.txt": [
        ("ООО «ГАММА»", None, [
            "40702810111000502425", "40702391110000000045", "40702810701110000909",
            "42102811110000000189", "42102811100060000244", "40702811100060002849"
        ], "7712345678"),
        ("АО «Фрязинский Экспериментальный Завод»", None, [
            "40702811100000021288", "42102111000610004922", "40702911100010000003",
            "40702111000400000094", "40702111000400000733"
        ], "5052115023"),
    ],
    "285816.txt": [
        ("Ивановой Аллы Владимировны", "20.12.1954", [
            "40817810338111377412", "40817810838181190670", "40817810938111377516",
            "42305810238110974164", "42305810338110982946", "40817810880000032391"
        ], None),
        ("Петровой Ольги Дмитриевны", "07.11.1975", [
            "40817098138111002357", "40817098238111002323", "40817810238180056450",
            "40817810338180075593", "40817810838180022114", "40817810938111351246",
            "40817840538260800393", "42307810938126952779", "40817810948276011359",
            "40817810209306000908"
        ], None),
        ("Сидоровой Марины Дмитриевны", "07.11.1975", [], None),
        ("Кузнецовой Ксении Германовны", "28.08.1987", [
            "40817810355030453913", "40817810355177963612", "40817810455176577750",
            "40817810655177963574", "40817810655869432193", "40817810755867130643",
            "40817810855866580084", "40817810255004605619", "40817810230066048934",
            "40817840530066004732", "40817978630066004559"
        ], None),
        ("Яковлевой Элины Михайловны", "25.06.1966", [
            "40817810055178311262", "40817810055190371413", "40817810155031110895",
            "40817810155170082091", "40817810755862822370", "42301810855203213321",
            "40817810803001215023"
        ], None),
    ],
}

IGNORE_ORG_PATTERNS = [
    r'втб', r'сбербанк', r'альфа-?банк', r'тбанк|т-банк|тинькофф',
    r'озон\s*банк', r'единая\s+касса', r'банк', r'касса', r'фонд',
    r'мвд', r'омвд', r'отдел', r'отделение', r'суд', r'прокуратур',
    r'райффайзенбанк'
]

IGNORE_PERSON_PATTERNS = [
    r'судья', r'судьи', r'следовател', r'дознавател', r'прокурор',
    r'постановил', r'в интересах'
]


def load_text(filename):
    path = os.path.join(TEXTS_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def normalize(text):
    text = re.sub(r'[«»"\'`]', '', text)
    return re.sub(r'\s+', ' ', text).strip().lower()


def match_fio(found_text, exp_text):
    return normalize(found_text) == normalize(exp_text)


def _attr_values(found, name):
    """Достаёт список значений атрибута из нового формата."""
    attrs = found.get("attributes", {})
    v = attrs.get(name)
    if v is None:
        return []
    if isinstance(v, list):
        return [x["value"] for x in v]
    return [v["value"]]


# ============================================================================
# ДИАГНОСТИКА ЭТАПОВ (адаптирована под GLiNER 2.5)
# ============================================================================
def stages_diagnostics(text, threshold=0.1):
    # Метки в формате GLiNER 2.5: {label: [описания]}
    final_labels = {}
    for label, desc in DEFAULT_PERSON_LABELS.items():
        final_labels[label] = [desc] if isinstance(desc, str) else desc
    for label, desc in DEFAULT_ORG_LABELS.items():
        final_labels[label] = [desc] if isinstance(desc, str) else desc

    model = get_model()
    result = model.extract_entities(
        text,
        final_labels,
        threshold=threshold,
        include_spans=True,
        include_confidence=True,
    )

    # Приводим ответ GLiNER 2.5 к формату диагностики
    raw = []
    if isinstance(result, dict) and 'entities' in result:
        for label, items in result['entities'].items():
            for item in items:
                raw.append({
                    "start": item["start"],
                    "end": item["end"],
                    "text": item["text"],
                    "label": label,
                    "score": item.get("confidence"),
                })
    else:
        for ent in result:
            raw.append({
                "start": ent["start"],
                "end": ent.get("end", ent.get("stop")),
                "text": ent["text"],
                "label": ent.get("label", ent.get("type")),
                "score": ent.get("confidence"),
            })

    print(f"\n  ── ЭТАП 1. СЫРЫЕ СУЩНОСТИ GLiNER 2.5 (threshold={threshold}), всего {len(raw)}:")
    for e in raw:
        score = e.get("score")
        score_str = f" score={score:.4f}" if isinstance(score, (int, float)) else ""
        print(f"      [{e['label']}] '{e['text']}' @ {e['start']}-{e['end']}{score_str}")

    raw_sorted = sorted(raw, key=lambda e: e["start"])
    merged = []
    for ent in raw_sorted:
        merged.append({
            'start': ent["start"],
            'stop': ent["end"],
            'text': ent["text"],
            'type': ent["label"],
        })
    merged.sort(key=lambda x: x['start'])
    i = 0
    while i < len(merged) - 1:
        a = merged[i]
        b = merged[i + 1]
        if a['type'] == 'ORGANIZATION' and b['type'] == 'ORGANIZATION':
            between = text[a['stop']:b['start']]
            if re.fullmatch(r'[\s«»"\-–—]*', between):
                a['text'] = f"{a['text']} {b['text']}"
                a['stop'] = b['stop']
                merged.pop(i + 1)
                continue
        i += 1

    print(f"\n  ── ЭТАП 2. ПОСЛЕ СКЛЕЙКИ СОСЕДНИХ ORG, всего {len(merged)}:")
    for e in merged:
        print(f"      [{e['type']}] '{e['text']}' @ {e['start']}-{e['stop']}")

    sorted_forms = sorted(ORG_FORMS, key=len, reverse=True)
    opf_pattern = r'\b(' + '|'.join(re.escape(f) for f in sorted_forms) + r')\b'
    for ent in merged:
        if ent['type'] != 'ORGANIZATION':
            continue
        if ent['text'].upper() in ORG_FORMS:
            continue
        left_start = max(0, ent['start'] - 100)
        left_text = text[left_start:ent['start']]
        matches = list(re.finditer(opf_pattern, left_text, re.IGNORECASE))
        if matches:
            match = matches[-1]
            opf = match.group(1).upper()
            ent['text'] = f"{opf} {ent['text']}"
            ent['start'] = left_start + match.start()

    print(f"\n  ── ЭТАП 3. ПОСЛЕ ПРИКЛЕИВАНИЯ ОПФ, всего {len(merged)}:")
    for e in merged:
        print(f"      [{e['type']}] '{e['text']}' @ {e['start']}-{e['stop']}")

    compiled_ignore_orgs = [re.compile(p, re.IGNORECASE) for p in IGNORE_ORG_PATTERNS]
    compiled_ignore_persons = [re.compile(p, re.IGNORECASE) for p in IGNORE_PERSON_PATTERNS]
    filtered = []
    for ent in merged:
        ent_text = ent["text"]
        ent_type = ent["type"]

        if ent_type == "ORGANIZATION":
            if any(p.search(ent_text) for p in compiled_ignore_orgs):
                print(f"      [отсеяна ORG] '{ent_text}' — совпал ignore_org_patterns")
                continue
        if ent_type == "PERSON":
            ctx_start = max(0, ent["start"] - 50)
            ctx_text = text[ctx_start:ent["start"]]
            if any(p.search(ctx_text) for p in compiled_ignore_persons):
                print(f"      [отсеяна PER] '{ent_text}' — контекст: '{ctx_text.strip()}'")
                continue
            if re.search(r'[А-ЯЁA-Z]\.[А-ЯЁA-Z]?\.?', ent_text):
                print(f"      [отсеяна PER] '{ent_text}' — инициалы")
                continue

        if ent_type == "ORGANIZATION" and ent_text.upper() in ORG_FORMS:
            print(f"      [отсеяна ORG] '{ent_text}' — голое ОПФ")
            continue

        filtered.append(ent)

    print(f"\n  ── ЭТАП 4. ПОСЛЕ ФИЛЬТРАЦИИ, всего {len(filtered)}:")
    for e in filtered:
        print(f"      [{e['type']}] '{e['text']}' @ {e['start']}-{e['stop']}")

    clusters = {}
    for span in filtered:
        if span['type'] == 'PERSON':
            words = span['text'].split()
            key_parts = [w[:3].lower() for w in words[:3]]
            key = "".join(key_parts)
        else:
            key = (re.sub(r'[«»"\s]', '', span['text'].lower()), span['type'])

        if key not in clusters:
            clusters[key] = {'start': span['start'], 'stop': span['stop'], 'text': span['text'], 'type': span['type']}
        else:
            clusters[key]['stop'] = max(clusters[key]['stop'], span['stop'])

    merged_spans = list(clusters.values())
    merged_spans.sort(key=lambda x: x['start'])

    print(f"\n  ── ЭТАП 5. ПОСЛЕ КЛАСТЕРИЗАЦИИ, всего {len(merged_spans)}:")
    for e in merged_spans:
        print(f"      [{e['type']}] '{e['text']}' @ {e['start']}-{e['stop']}")
    print()


def test_all():
    passed = 0
    failed = 0

    for filename, expected_items in DATASET_ALL.items():
        print(f"\n{'=' * 70}")
        print(f"Файл: {filename}")
        print(f"{'=' * 70}")

        text = load_text(filename)
        if text is None:
            print(f"  ❌ [SKIP] Файл не найден: {TEXTS_DIR}\\{filename}")
            failed += len(expected_items)
            continue

        # ВЫВОД ЭТАПОВ
        stages_diagnostics(text, threshold=0.1)

        # ВЫЗОВ ФУНКЦИИ
        entities = extract_entities_with_attributes(
            text,
            entity_types=("PER", "ORG"),
            ignore_org_patterns=IGNORE_ORG_PATTERNS,
            ignore_person_patterns=IGNORE_PERSON_PATTERNS,
            attributes_to_find=("inn", "birth_date", "account"),
            chunk_size_words=None,
            chunk_overlap_words=None,
            account_owner_patterns=None,
            account_ignore_patterns=None,
        )

        print(f"  ИТОГОВЫЙ СПИСОК СУЩНОСТЕЙ ({len(entities)} шт.):")
        for e in entities:
            is_expected = any(match_fio(e['entity'], exp_name) for exp_name, _, _, _ in expected_items)
            mark = "★ ДОЛЖНИК" if is_expected else "❌ ЛИШНЯЯ"

            print(f"\n    [{mark}] {e['entity']} ({e['type']}) @ {e['start']}-{e['stop']}")
            bd = e["attributes"].get("birth_date")
            inn = e["attributes"].get("inn")
            accs = e["attributes"].get("account") or []
            if bd:
                print(f"        Дата: {bd['value']} @ {bd['start']}-{bd['stop']}")
            if inn:
                print(f"        ИНН: {inn['value']} @ {inn['start']}-{inn['stop']}")
            if accs:
                print(f"        Счета ({len(accs)}):")
                for a in accs:
                    print(f"            {a['value']} @ {a['start']}-{a['stop']}")

        print(f"\n  ПРОВЕРКА ЭТАЛОНА (все счета):")
        for exp_name, exp_date, exp_accs, exp_inn in expected_items:
            found = next((e for e in entities if match_fio(e['entity'], exp_name)), None)

            if not found:
                print(f"  ❌ [FAIL] '{exp_name}' — НЕ найден")
                failed += 1
                continue

            ok = True
            details = []

            if exp_date:
                dates = _attr_values(found, "birth_date")
                if dates == [exp_date]:
                    details.append(f"дата={exp_date} ✓")
                else:
                    details.append(f"дата FAIL (искали ровно {exp_date}, нашли {dates})")
                    ok = False

            if exp_inn:
                inns = _attr_values(found, "inn")
                if inns == [exp_inn]:
                    details.append(f"ИНН={exp_inn} ✓")
                else:
                    details.append(f"ИНН FAIL (искали {exp_inn}, нашли {inns})")
                    ok = False

            accounts = set(_attr_values(found, "account"))
            expected_set = set(exp_accs)

            if accounts == expected_set:
                details.append(f"счета ✓ (все {len(exp_accs)})")
            else:
                missing = expected_set - accounts
                extra = accounts - expected_set
                details.append(f"счета FAIL (не хватает: {len(missing)}, лишние: {len(extra)})")
                ok = False

            if ok:
                print(f"  [OK] '{found['entity']}' — {', '.join(details)}")
                passed += 1
            else:
                print(f"  ❌ [FAIL] '{found['entity']}' — {', '.join(details)}")
                failed += 1

    print(f"\n{'=' * 70}")
    print(f"ИТОГО: passed={passed}, failed={failed}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    test_all()