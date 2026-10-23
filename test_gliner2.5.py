import os
import json
from gliner2.joint_ie import JointIE, JointIEConfig

# Твоя локальная модель
MODEL_PATH = r"F:\Python projects\Gliner\models\gliner2.5-multi-v1"

TEXTS_DIR = r"F:\Python projects\Gliner\data\debtors_vtb_account_numbers"

TEXT_FILES = [
    "004174_564.txt",
    "004174_564 усложненный на тестирование окна поиска перед сущностью.txt",
    "доп_1_2026-06-11_11-30-50_1.txt",
    "пример с разрывом сущности.txt",
    "неск_должников_286133.txt",
    "неск_постановлений_280501_2.txt",
    "285816.txt",
]

_model = None


def get_model():
    global _model
    if _model is None:
        print(f"[GLiNER 2.5 JointIE] Загрузка модели из {MODEL_PATH}...")
        _model = JointIE.from_pretrained(MODEL_PATH, local_files_only=True)
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

        # ====================================================================
        # Схема: две связи
        # 1. person -> birth_date (дата рождения человека)
        # 2. organization -> inn (ИНН организации)
        # ====================================================================
        schema = (
            model.create_schema()
            .entities([
                "person",       # ФИО
                "date",         # даты (включая даты рождения)
                "organization", # организации
                "inn",          # ИНН (10-12 цифр)
            ])
            .relation("has_birth_date", "person", "date")
            .relation("has_inn", "organization", "inn")
        )

        # ВАЖНО: include_spans и include_confidence — поля JointIEConfig,
        # а не аргументы extract() [citation:2]
        config = JointIEConfig(
            optimizer="beam",
            beam_size=16,
            include_spans=True,
            include_confidence=True,
        )

        try:
            result = model.extract(text, schema, config=config)
        except Exception as e:
            print(f"  ❌ Ошибка при извлечении: {e}")
            continue

        # feasible=False означает, что жёсткие ограничения не выполнены
        # (это НЕ то же самое, что «в тексте нет фактов») [citation:1]
        print(f"  feasible: {result.feasible}")

        # Печатаем сущности
        print(f"\n  СУЩНОСТИ ({len(result.entities)}):")
        for ent in result.entities:
            conf = getattr(ent, "confidence", None)
            conf_str = f" (conf={conf:.4f})" if conf is not None else ""
            print(f"    [{ent.type}] '{ent.text}' @ {ent.start}-{ent.end}{conf_str}")

        # Печатаем связи
        print(f"\n  СВЯЗИ ({len(result.relations)}):")
        for rel in result.relations:
            head = result.entity(rel.head)
            tail = result.entity(rel.tail)
            conf = getattr(rel, "confidence", None)
            conf_str = f" (conf={conf:.4f})" if conf is not None else ""
            print(f"    {head.text} --{rel.type}--> {tail.text}{conf_str}")

        # Полный JSON для отладки
        print(f"\n  ПОЛНЫЙ JSON:")
        try:
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"    (to_dict() недоступен: {e})")


if __name__ == "__main__":
    main()