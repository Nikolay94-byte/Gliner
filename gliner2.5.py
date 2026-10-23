import os
import json
from gliner2 import AutoExtractor

# Путь к твоей локальной модели gliner2.5-multi-v1
MODEL_PATH = r"F:\Python projects\Gliner\models\gliner2.5-multi-v1"

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

# Метки, которые пробуем.
# PERSON и DATE точно есть в обучении metrika-labs.
# PII - общий класс для чувствительных данных (может включать счета).
# ORG - проверяем, сработает ли как zero-shot.
LABELS = [
    "PERSON",          # ФИО
    "DATE",            # Даты (вкл. даты рождения)
    "PII",             # Общий класс PII (возможно, счета/ИНН)
    "ORG",             # Организации (проверяем zero-shot)
]

_model = None

def get_model():
    global _model
    if _model is None:
        print(f"[GLiNER 2.5] Загрузка модели из {MODEL_PATH}...")
        _model = AutoExtractor.from_pretrained(MODEL_PATH, local_files_only=True)
    return _model


def load_text(filename):
    path = os.path.join(TEXTS_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def main():
    model = get_model()

    for filename in TEXT_FILES:
        print(f"\n{'=' * 70}")
        print(f"Файл: {filename}")
        print(f"{'=' * 70}")

        text = load_text(filename)
        if text is None:
            print(f"  ❌ [SKIP] Файл не найден: {TEXTS_DIR}\\{filename}")
            continue

        # Запускаем извлечение
        # include_spans=True обязателен для получения start/end
        result = model.extract_entities(
            text,
            LABELS,
            threshold=0.1,
            include_spans=True,
            include_confidence=True,
        )

        # Преобразуем ответ в читаемый формат
        output = []
        if isinstance(result, dict) and 'entities' in result:
            for label, items in result['entities'].items():
                for item in items:
                    output.append({
                        "entity": item.get("text"),
                        "type": label,
                        "start": item.get("start"),
                        "stop": item.get("end"),
                        "confidence": round(item.get("confidence", 0), 4),
                    })
        else:
            # На случай, если формат ответа другой
            for ent in result:
                output.append({
                    "entity": ent.get("text"),
                    "type": ent.get("label", "UNKNOWN"),
                    "start": ent.get("start"),
                    "stop": ent.get("end"),
                    "confidence": round(ent.get("confidence", 0), 4),
                })

        # Сортируем по позиции в тексте
        output.sort(key=lambda x: x['start'] if x['start'] is not None else 0)

        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()