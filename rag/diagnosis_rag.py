#!/usr/bin/env python3
"""
Скрипт для семантического поиска диагнозов по МКБ-10.
Поддерживает создание новой векторной базы и загрузку готовой из файла.
"""

import argparse
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss


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

    return index, sentences


def save_index(index, sentences, index_path, sentences_path):
    """Сохраняет FAISS индекс и список предложений на диск"""
    index_path = Path(index_path)
    sentences_path = Path(sentences_path)

    index_path.parent.mkdir(parents=True, exist_ok=True)
    sentences_path.parent.mkdir(parents=True, exist_ok=True)

    # Сохраняем FAISS индекс
    faiss.write_index(index, str(index_path))
    print(f"FAISS индекс сохранён в: {index_path}")

    # Сохраняем список предложений через pickle
    with open(sentences_path, "wb") as f:
        pickle.dump(sentences, f)
    print(f"Список предложений сохранён в: {sentences_path}")


def load_index(index_path, sentences_path):
    """Загружает FAISS индекс и список предложений с диска"""
    index_path = Path(index_path)
    sentences_path = Path(sentences_path)

    if not index_path.exists():
        raise FileNotFoundError(f"Файл индекса не найден: {index_path}")
    if not sentences_path.exists():
        raise FileNotFoundError(f"Файл предложений не найден: {sentences_path}")

    # Загружаем FAISS индекс
    index = faiss.read_index(str(index_path))
    print(f"FAISS индекс загружен из: {index_path}")
    print(f"Количество векторов в базе: {index.ntotal}")

    # Загружаем список предложений
    with open(sentences_path, "rb") as f:
        sentences = pickle.load(f)
    print(f"Список предложений загружен из: {sentences_path}")

    return index, sentences


def search_similar(model, index, sentences, query, top_k=10):
    """Ищет похожие диагнозы"""
    query_vector = model.encode([query], normalize_embeddings=True).astype("float32")
    scores, indices = index.search(query_vector, top_k)

    results = []
    for idx, score in zip(indices[0], scores[0]):
        results.append(
            {
                "sentence": sentences[idx],
                "index": int(idx),
                "score": float(score),
            }
        )

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Семантический поиск диагнозов по текстовому запросу"
    )

    # === Режим работы ===
    mode_group = parser.add_mutually_exclusive_group(required=True)

    mode_group.add_argument(
        "--build",
        action="store_true",
        help="Режим создания новой векторной базы из Excel-файла",
    )

    mode_group.add_argument(
        "--load",
        action="store_true",
        help="Режим загрузки готовой векторной базы с диска",
    )

    # === Аргументы для режима --build ===
    parser.add_argument(
        "--input-file",
        "-i",
        type=str,
        help="Путь к Excel-файлу с диагнозами (только для --build)",
    )

    parser.add_argument(
        "--column",
        "-c",
        type=str,
        default="Название диагноза",
        help="Название колонки с диагнозами в Excel (по умолчанию: 'Название диагноза')",
    )

    # === Аргументы для режима --load ===
    parser.add_argument(
        "--index-file",
        type=str,
        default="vector_db/mkb_index.faiss",
        help="Путь к файлу FAISS индекса (для --build: куда сохранить, для --load: откуда загрузить)",
    )

    parser.add_argument(
        "--sentences-file",
        type=str,
        default="vector_db/sentences.pkl",
        help="Путь к файлу с предложениями (для --build: куда сохранить, для --load: откуда загрузить)",
    )

    # === Общие аргументы ===
    parser.add_argument(
        "--query",
        "-q",
        type=str,
        help="Поисковый запрос (если не указан, только создаётся/загружается БД)",
    )

    parser.add_argument(
        "output_file_path",
        type=str,
        nargs="?",
        help="Путь для сохранения результатов поиска в JSON (обязателен только с --query)",
    )

    parser.add_argument(
        "--top-k",
        "-k",
        type=int,
        default=10,
        help="Количество возвращаемых результатов (по умолчанию: 10)",
    )

    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default="deepvk/USER-bge-m3",
        help="Название модели SentenceTransformer (по умолчанию: 'deepvk/USER-bge-m3')",
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
        # Режим создания новой базы
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

        index, sentences = build_index(model, sentences)

        # Сохраняем базу
        save_index(index, sentences, args.index_file, args.sentences_file)

    elif args.load:
        # Режим загрузки готовой базы
        index, sentences = load_index(args.index_file, args.sentences_file)

    else:
        print("Ошибка: укажите --build или --load", file=sys.stderr)
        sys.exit(1)

    # ============================================
    # ПОИСК (если задан запрос)
    # ============================================
    if args.query:
        if not args.output_file_path:
            print(
                "Ошибка: с --query необходимо указать output_file_path", file=sys.stderr
            )
            sys.exit(1)

        print(f"\nЗапрос: '{args.query}'")
        results = search_similar(model, index, sentences, args.query, top_k=args.top_k)

        # Вывод в консоль
        print(f"\nРезультаты (топ-{args.top_k}):")
        print("-" * 70)
        for i, res in enumerate(results, 1):
            text = (
                res["sentence"][:80] + "..."
                if len(res["sentence"]) > 80
                else res["sentence"]
            )
            print(f"{i:2}. [{res['index']}] {text}")
            print(f"    score: {res['score']:.6f}")
            print()

        # Сохранение результатов
        output_path = Path(args.output_file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        output_data = {
            "query": args.query,
            "model": args.model,
            "top_k": args.top_k,
            "results": results,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"Результаты сохранены в: {output_path}")
    else:
        print("\nБаза данных готова. Используйте --load с --query для поиска.")


if __name__ == "__main__":
    main()
