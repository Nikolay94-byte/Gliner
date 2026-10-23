import os
import json

from my_gliner_text import extract_entities_text

TEXTS_DIR = r"F:\Python projects\Gliner\data\debtors_vtb_account_numbers"

TEXT_FILES = [
    "004174_564.txt",
    "004174_564 усложненный на тестирование окна поиска перед сущностью.txt",
    "доп_1_2026-06-11_11-30-50_1.txt",
    "доп_2-225_копия_2026-06-08-15-36-55.txt",
    "пример с разрывом сущности.txt",
    "доп_442117(1).txt",
    "доп_442117.txt",
    "неск_должников_286133.txt",
    "неск_постановлений_280501_1.txt",
    "неск_постановлений_280501_2.txt",
    "285816.txt",
]

IGNORE_ORG_PATTERNS = [
    r'втб', r'сбербанк', r'альфа-?банк', r'тбанк|т-банк|тинькофф',
    r'озон\s*банк', r'единая\s+касса', r'банк', r'касса', r'фонд',
    r'мвд', r'омвд', r'отдел', r'отделение', r'суд', r'прокуратур',
    r'райффайзенбанк',r'област(и|ь)',r'РФ',r'Российской Федерации',r'налоговых органов',r'органов\W{,3}контроля'
]

IGNORE_PERSON_PATTERNS = [
    r'судья', r'судьи', r'следовател', r'дознавател', r'прокурор',
    r'постановил', r'в интересах',
]


def load_text(filename):
    path = os.path.join(TEXTS_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def pretty_print(entities):
    dumped = json.dumps(entities, ensure_ascii=False, indent=2)
    dumped = dumped.replace("\\n", "\n")
    print(dumped)


def main():
    for filename in TEXT_FILES:
        print(f"\n{'=' * 70}")
        print(f"Файл: {filename}")
        print(f"{'=' * 70}")

        text = load_text(filename)
        if text is None:
            print(f"  ❌ [SKIP] Файл не найден: {TEXTS_DIR}\\{filename}")
            continue

        entities = extract_entities_text(
            text,
            entity_types=("PERSON", "ORGANIZATION"),   # ← исправлено
            ignore_org_patterns=IGNORE_ORG_PATTERNS,
            ignore_person_patterns=IGNORE_PERSON_PATTERNS,
            ignore_initials=True,
            return_window=True,
        )

        pretty_print(entities)


if __name__ == "__main__":
    main()