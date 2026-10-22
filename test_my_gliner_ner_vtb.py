import os
import re
import json
from my_gliner_ner import (
    extract_entities_with_attributes,
    TOP_RUSSIAN_BANKS,
)

TEXTS_DIR = r"F:\Python projects\Gliner\data\debtors_vtb_account_numbers"

# ============================================================================
# ДАННЫЕ ИЗ EXCEL (ЛИСТ 1: "ТОЛЬКО ВТБ СЧЕТА")
# ============================================================================
DATASET_VTB = {
    "004174_564.txt": [
        ("Ивановой Марии Сергеевны", "12.12.1994", ["40800010990000123456"], None),
    ],
    "доп_1_2026-06-11_11-30-50_1.txt": [
        ("Ощепковой Зины Алексеевны", "05.11.2004", ["40817111220000017108"], None),
    ],
    "доп_2-225_копия_2026-06-08-15-36-55.txt": [
        ("Иванову Ивану Ивановичу", "14.02.1995", [], None),
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
        ("ООО «АЛЬФАСТРОЙ»", None, ["40701110225630002518"], "7711134567"),
        ("Петрова Николая Анатольевича", "29.04.1971", [], None),
        ("Сидоровой Елены Викторовны", "09.10.1971", ["40817811100054008660"], None),
        ("Петрова Артема Витальевича", "01.11.2002", ["40817111000002795050"], None),
    ],
    "неск_постановлений_280501_1.txt": [
        ("Иванова Петра Сергеевича", "14.06.1998", [
            "40811100008004010070", "40111000508004009242", "40811100001782033274"
        ], None),
        ("Сидорова Юрия Владимировича", "12.06.1999", [
            "40111000209254045086", "40817811100057049467"
        ], None),
    ],
    "неск_постановлений_280501_2.txt": [
        ("ООО «ГАММА»", None, [
            "40702810701110000909", "42102811110000000189", "42102811100060000244"
        ], "7712345678"),
        ("АО «Фрязинский Экспериментальный Завод»", None, [
            "40702811100000021288", "42102111000610004922", "40702911100010000003"
        ], "5052115023"),
    ],
    "285816.txt": [
        ("Ивановой Аллы Владимировны", "20.12.1954", ["40817810880000032391"], None),
        ("Петровой Ольги Дмитриевны", "07.11.1975", [
            "40817810948276011359", "40817810209306000908"
        ], None),
        ("Сидоровой Марины Дмитриевны", "07.11.1975", [], None),
        ("Кузнецовой Ксении Германовны", "28.08.1987", [
            "40817810230066048934", "40817840530066004732", "40817978630066004559"
        ], None),
        ("Яковлевой Элины Михайловны", "25.06.1966", [], None),
    ],
}

IGNORE_ORG_PATTERNS = [
    r'втб', r'сбербанк', r'альфа-?банк', r'тбанк|т-банк|тинькофф',
    r'озон\s*банк', r'единая\s+касса', r'банк', r'касса', r'фонд',
    r'мвд', r'омвд', r'отдел', r'отделение', r'суд', r'прокуратур',
]

IGNORE_PERSON_PATTERNS = [
    r'судья', r'судьи', r'следовател', r'дознавател', r'прокурор',
    r'постановил', r'в интересах',
]

ACCOUNT_OWNER_PATTERNS = [r'ВТБ', r'Банк\s+ВТБ', r'ПАО\s+«?ВТБ»?']


def load_text(filename):
    """Читает файл из TEXTS_DIR. Возвращает None, если файла нет."""
    path = os.path.join(TEXTS_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def normalize(text):
    """Нормализует текст для сравнения: схлопывает пробелы, нижний регистр."""
    return re.sub(r'\s+', ' ', text).strip().lower()


def match_fio(found_text, exp_text):
    """Сравнивает найденное ФИО с эталоном по первым 5 буквам каждого слова."""
    found_norm = normalize(found_text).replace('«', '').replace('»', '')
    exp_words = normalize(exp_text).replace('«', '').replace('»', '').split()
    return all(word[:5] in found_norm for word in exp_words)


def _attr_values(found, name):
    """Достаёт список значений атрибута из формата результата.

    birth_date/inn — dict | None → [value] или [];
    account — list[dict] → [value, ...].
    """
    attrs = found.get("attributes", {})
    value = attrs.get(name)
    if value is None:
        return []
    if isinstance(value, list):
        return [item["value"] for item in value]
    return [value["value"]]


def test_all_vtb():
    passed = 0
    failed = 0

    for filename, expected_items in DATASET_VTB.items():
        print(f"\n{'=' * 70}")
        print(f"Файл: {filename}")
        print(f"{'=' * 70}")

        text = load_text(filename)
        if text is None:
            print(f"  ❌ [SKIP] Файл не найден: {TEXTS_DIR}\\{filename}")
            failed += len(expected_items)
            continue

        entities = extract_entities_with_attributes(
            text,
            entity_types=("PER", "ORG"),
            ignore_org_patterns=IGNORE_ORG_PATTERNS,
            ignore_person_patterns=IGNORE_PERSON_PATTERNS,
            attributes_to_find=("inn", "birth_date", "account"),
            account_owner_patterns=ACCOUNT_OWNER_PATTERNS,
            account_ignore_patterns=None,
        )

        print(f"  ИТОГОВЫЙ СПИСОК СУЩНОСТЕЙ ({len(entities)} шт.):")
        for entity in entities:
            is_expected = any(
                match_fio(entity['entity'], expected_name)
                for expected_name, _, _, _ in expected_items
            )
            mark = "★ ДОЛЖНИК" if is_expected else "❌ ЛИШНЯЯ"

            print(f"\n    [{mark}] {entity['entity']} ({entity['type']}) @ {entity['start']}-{entity['stop']}")
            birth_date = entity["attributes"].get("birth_date")
            inn = entity["attributes"].get("inn")
            accounts = entity["attributes"].get("account") or []
            if birth_date:
                print(f"        Дата: {birth_date['value']} @ {birth_date['start']}-{birth_date['stop']}")
            if inn:
                print(f"        ИНН: {inn['value']} @ {inn['start']}-{inn['stop']}")
            if accounts:
                print(f"        Счета ВТБ ({len(accounts)}):")
                for account in accounts:
                    print(f"            {account['value']} @ {account['start']}-{account['stop']}")

        print(f"\n  ПРОВЕРКА ЭТАЛОНА (только счета ВТБ):")
        for expected_name, expected_date, expected_accounts, expected_inn in expected_items:
            found = next(
                (entity for entity in entities if match_fio(entity['entity'], expected_name)),
                None,
            )

            if not found:
                print(f"  ❌ [FAIL] '{expected_name}' — НЕ найден")
                failed += 1
                continue

            ok = True
            details = []

            if expected_date:
                dates = _attr_values(found, "birth_date")
                if dates == [expected_date]:
                    details.append(f"дата={expected_date} ✓")
                else:
                    details.append(f"дата FAIL (искали ровно {expected_date}, нашли {dates})")
                    ok = False

            if expected_inn:
                inns = _attr_values(found, "inn")
                if inns == [expected_inn]:
                    details.append(f"ИНН={expected_inn} ✓")
                else:
                    details.append(f"ИНН FAIL (искали {expected_inn}, нашли {inns})")
                    ok = False

            accounts = set(_attr_values(found, "account"))
            expected_set = set(expected_accounts)

            if accounts == expected_set:
                details.append(f"счета ВТБ ✓ (все {len(expected_accounts)})")
            else:
                missing = expected_set - accounts
                extra = accounts - expected_set
                details.append(
                    f"счета ВТБ FAIL (не хватает: {len(missing)}, лишние: {len(extra)})"
                )
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
    test_all_vtb()