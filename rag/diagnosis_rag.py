#!/usr/bin/env python3
"""
Скрипт для семантического поиска диагнозов по МКБ-10.
Поддерживает создание новой векторной базы и загрузку готовой из файла.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss
from tqdm import tqdm


def load_data(input_path, diagnosis_column_name):
    """Загружает данные из Excel-файла"""
    df = pd.read_excel(input_path, dtype=str)

    if diagnosis_column_name not in df.columns:
        raise ValueError(
            f"Колонка '{diagnosis_column_name}' не найдена в файле. "
            f"Доступные колонки: {list(df.columns)}"
        )

    sentences = df[diagnosis_column_name].tolist()
    return sentences


def build_index(model, sentences):
    """Создаёт векторную базу FAISS"""
    print("Векторизация диагнозов...")
    embeddings = model.encode(
        sentences, show_progress_bar=True, normalize_embeddings=True
    )
    embeddings = np.array(embeddings).astype("float32")

    print(f"Размерность одного вектора: {embeddings.shape[1]}")

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    print(f"Количество векторов в базе: {index.ntotal}")

    return index


def save_index(index, index_path):
    """Сохраняет FAISS индекс на диск"""
    index_path = Path(index_path)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(index_path))
    print(f"FAISS индекс сохранён в: {index_path}")


def load_index(index_path):
    """Загружает FAISS индекс с диска"""
    index_path = Path(index_path)
    if not index_path.exists():
        raise FileNotFoundError(f"Файл индекса не найден: {index_path}")
    index = faiss.read_index(str(index_path))
    print(f"FAISS индекс загружен из: {index_path}")
    print(f"Количество векторов в базе: {index.ntotal}")
    return index


def search_similar(model, index, sentences, query, top_k=10):
    """Ищет похожие диагнозы"""
    query_vector = model.encode([query], normalize_embeddings=True).astype("float32")
    scores, indices = index.search(query_vector, top_k)
    results = []
    for idx, score in zip(indices[0], scores[0]):
        results.append(
            {
                "index": int(idx),
                "sentence": sentences[idx],
                "score": float(score),
            }
        )
    return results


def format_top_results(results, top_n, format_type="detailed"):
    """Форматирует топ-N результатов в строку"""
    top_results = results[:top_n]

    if format_type == "detailed":
        return "\n".join(
            f"{i}. [{r['index']}] {r['sentence'][:100]} (score: {r['score']:.4f})"
            for i, r in enumerate(top_results, 1)
        )

    if format_type == "scores":
        return ", ".join(f"{r['score']:.4f}" for r in top_results)

    if format_type == "sentences":
        return "\n".join(
            f"{i}. {r['sentence'][:100]}" for i, r in enumerate(top_results, 1)
        )

    return ""


def batch_process_queries(
    model,
    index,
    db_sentences,
    input_df,
    query_column,
    output_column=None,
    top_k=10,
    top_n=5,
    format_type="detailed",
):
    """Пакетная обработка запросов из DataFrame"""
    if query_column not in input_df.columns:
        raise ValueError(f"Колонка '{query_column}' не найдена в файле")

    if output_column is None:
        output_column = f"Топ-{top_n} похожих диагнозов"

    df = input_df.copy()

    # Берём только непустые строки (не NaN и не пустая строка)
    mask = df[query_column].notna() & (df[query_column].str.strip() != "")
    queries = df.loc[mask, query_column].tolist()
    query_indices = df.loc[mask].index

    results_list = []

    print(
        f"\nОбработка {len(queries)} непустых запросов (пропущено {(~mask).sum()} пустых)..."
    )
    for query in tqdm(queries, desc="Поиск"):
        try:
            res = search_similar(
                model, index, db_sentences, str(query).strip(), top_k=top_k
            )
            results_list.append(format_top_results(res, top_n, format_type))
        except Exception as e:
            print(f"Ошибка при обработке '{query}': {e}", file=sys.stderr)
            results_list.append(f"ОШИБКА: {e}")

    # Записываем результаты только в строки с непустыми запросами
    df.loc[query_indices, output_column] = results_list

    # Для пустых строк оставляем NaN (или можно записать пустую строку)
    # df.loc[~mask, output_column] = ""  # раскомментируй, если хочешь пустые строки вместо NaN

    return df, output_column


def main():
    parser = argparse.ArgumentParser(
        description="Семантический поиск диагнозов по МКБ-10 с использованием векторной базы данных.",
        epilog="Примеры использования:\n"
        "  Создание базы:        %(prog)s --build -i mkb10.xlsx\n"
        "  Одиночный поиск:      %(prog)s --load -i mkb10.xlsx -q 'сахарный диабет' result.json\n"
        "  Пакетная обработка:   %(prog)s --load -i mkb10.xlsx --batch-file queries.xlsx -Q 'Диагноз' output.xlsx\n"
        "  Только скоры:         %(prog)s --load -i mkb10.xlsx --batch-file q.xlsx --format scores output.xlsx",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # === Режим работы ===
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--build",
        action="store_true",
        help="Создать новую векторную базу из Excel-файла с эталонными диагнозами "
        "(требуется --input-file)",
    )
    mode_group.add_argument(
        "--load",
        action="store_true",
        help="Загрузить готовую векторную базу с диска для поиска "
        "(требуется --input-file и --index-file)",
    )

    # === Аргументы для --build ===
    parser.add_argument(
        "--input-file",
        "-i",
        type=str,
        help="Путь к Excel-файлу с эталонными диагнозами. "
        "В режиме --build: источник данных для создания векторной базы. "
        "В режиме --load: источник текстов диагнозов для вывода результатов поиска",
    )

    parser.add_argument(
        "--column",
        "-c",
        type=str,
        default="Название диагноза",
        help="Название колонки в Excel-файле, содержащей тексты диагнозов "
        "(по умолчанию: 'Название диагноза')",
    )

    # === FAISS индекс ===
    parser.add_argument(
        "--index-file",
        type=str,
        default="vector_db/mkb_index.faiss",
        help="Путь к файлу FAISS индекса. "
        "В режиме --build: путь для сохранения созданного индекса. "
        "В режиме --load: путь к готовому индексу для загрузки "
        "(по умолчанию: 'vector_db/mkb_index.faiss')",
    )

    # === Пакетная обработка ===
    parser.add_argument(
        "--batch-file",
        type=str,
        help="Путь к Excel-файлу с запросами для пакетной обработки. "
        "Файл должен содержать колонку с текстами запросов (см. --query-column). "
        "Результаты будут добавлены в новую колонку",
    )

    parser.add_argument(
        "--query-column",
        "-Q",
        type=str,
        default="Диагноз",
        help="Название колонки в batch-файле, содержащей тексты запросов "
        "(по умолчанию: 'Диагноз')",
    )

    parser.add_argument(
        "--output-column",
        type=str,
        help="Название колонки для сохранения результатов поиска. "
        "Если не указана, создаётся автоматически в формате 'Топ-N похожих диагнозов'",
    )

    parser.add_argument(
        "--top-n",
        "-N",
        type=int,
        default=5,
        help="Количество лучших результатов для сохранения в Excel при пакетной обработке "
        "(по умолчанию: 5)",
    )

    parser.add_argument(
        "--format",
        type=str,
        choices=["detailed", "scores", "sentences"],
        default="detailed",
        help="Формат сохранения результатов в Excel: "
        "'detailed' — полная информация с индексом и скором, "
        "'scores' — только числовые скоры через запятую, "
        "'sentences' — только названия диагнозов "
        "(по умолчанию: 'detailed')",
    )

    # === Одиночный запрос ===
    parser.add_argument(
        "--query",
        "-q",
        type=str,
        help="Текст запроса для одиночного поиска. "
        "Результат выводится в консоль и сохраняется в JSON-файл",
    )

    parser.add_argument(
        "output_file_path",
        type=str,
        nargs="?",
        help="Путь для сохранения результатов. "
        "Для --query: JSON-файл с результатами поиска. "
        "Для --batch-file: Excel-файл с добавленной колонкой результатов. "
        "Если не указан при --batch-file, используется исходный batch-файл",
    )

    # === Общие аргументы ===
    parser.add_argument(
        "--top-k",
        "-k",
        type=int,
        default=10,
        help="Общее количество ближайших кандидатов, извлекаемых из базы. "
        "Из них top-N лучших сохраняются в результаты "
        "(по умолчанию: 10)",
    )

    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default="deepvk/USER-bge-m3",
        help="Название модели SentenceTransformer для создания эмбеддингов "
        "(по умолчанию: 'deepvk/USER-bge-m3')",
    )

    args = parser.parse_args()

    # ============================================
    # ЗАГРУЗКА МОДЕЛИ
    # ============================================
    print(f"Загрузка модели '{args.model}'...")
    model = SentenceTransformer(args.model, trust_remote_code=True)

    # ============================================
    # СОЗДАНИЕ ИЛИ ЗАГРУЗКА БАЗЫ
    # ============================================
    if args.build:
        if not args.input_file:
            print(
                "Ошибка: для --build необходимо указать --input-file", file=sys.stderr
            )
            sys.exit(1)
        input_path = Path(args.input_file)
        if not input_path.exists():
            print(f"Ошибка: файл '{input_path}' не найден", file=sys.stderr)
            sys.exit(1)

        sentences = load_data(input_path, args.column)
        print(f"Загружено диагнозов: {len(sentences)}")
        index = build_index(model, sentences)
        save_index(index, args.index_file)

    elif args.load:
        if not args.input_file:
            print(
                "Ошибка: для --load необходимо указать --input-file (Excel-файл с диагнозами)",
                file=sys.stderr,
            )
            sys.exit(1)
        input_path = Path(args.input_file)
        if not input_path.exists():
            print(f"Ошибка: файл '{input_path}' не найден", file=sys.stderr)
            sys.exit(1)

        sentences = load_data(input_path, args.column)
        index = load_index(args.index_file)

    # ============================================
    # ПАКЕТНАЯ ОБРАБОТКА (BATCH)
    # ============================================
    if args.batch_file:
        batch_path = Path(args.batch_file)
        if not batch_path.exists():
            print(f"Ошибка: файл '{batch_path}' не найден", file=sys.stderr)
            sys.exit(1)

        print(f"\nЗагрузка файла с запросами: {batch_path}")
        batch_df = pd.read_excel(batch_path, dtype=str)

        output_path = (
            Path(args.output_file_path) if args.output_file_path else batch_path
        )
        result_df, out_col = batch_process_queries(
            model,
            index,
            sentences,
            batch_df,
            query_column=args.query_column,
            output_column=args.output_column,
            top_k=args.top_k,
            top_n=args.top_n,
            format_type=args.format,
        )
        result_df.to_excel(output_path, index=False)
        print(f"\nРезультаты сохранены в: {output_path}")
        print(f"Колонка с результатами: '{out_col}'")

    # ============================================
    # ОДИНОЧНЫЙ ЗАПРОС
    # ============================================
    elif args.query:
        if not args.output_file_path:
            print(
                "Ошибка: с --query необходимо указать output_file_path", file=sys.stderr
            )
            sys.exit(1)

        print(f"\nЗапрос: '{args.query}'")
        results = search_similar(model, index, sentences, args.query, top_k=args.top_k)

        print(f"\nРезультаты (топ-{args.top_k}):")
        print("-" * 70)
        for i, res in enumerate(results, 1):
            text = (
                res["sentence"][:80] + "..."
                if len(res["sentence"]) > 80
                else res["sentence"]
            )
            print(f"{i:2}. [{res['index']}] {text}")
            print(f"    score: {res['score']:.6f}\n")

        output_path = Path(args.output_file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "query": args.query,
                    "model": args.model,
                    "top_k": args.top_k,
                    "results": results,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        print(f"Результаты сохранены в: {output_path}")

    else:
        print("\nБаза готова. Используйте --batch-file или --query для поиска.")


if __name__ == "__main__":
    main()
