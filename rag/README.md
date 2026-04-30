# diagnosis rag

## 1. СОЗДАТЬ новую базу и сохранить на диск

```bash
python diagnosis_rag.py \
    --build \
    --input-file "./mkb10.xlsx" \
    --column "Название диагноза" \
    --index-file "./mkb_index.faiss"
```

## 2. ЗАГРУЗИТЬ готовую базу и выполнить поиск

```bash
python diagnosis_rag.py \
    --load \
    --input-file "./mkb10.xlsx" \
    --column "Название диагноза" \
    --index-file "./mkb_index.faiss" \
    --query "сахарный диабет" \
    --top-k 15 \
    "results.json"
```

## 3. СОЗДАТЬ базу и СРАЗУ выполнить поиск

```bash
python diagnosis_rag.py \
    --build \
    --input-file "./mkb10.xlsx" \
    --column "Название диагноза" \
    --query "членистоногими" \
    --top-k 15 \
    "results.json"
```

## 4. Пакетная обработка: проставить топ-5 диагнозов для каждого запроса

```bash
python diagnosis_rag.py \
    --load \
    --input-file "./mkb10.xlsx" \
    --column "Название диагноза" \
    --index-file "./mkb_index.faiss" \
    --batch-file "patient_diagnoses.xlsx" \
    --query-column "Диагноз пациента" \
    --top-n 5 \
    "patient_diagnoses_with_mkb.xlsx"
```

## 5. Пакетная обработка с сохранением в тот же файл

```bash
python diagnosis_rag.py \
    --load \
    --input-file "./mkb10.xlsx" \
    --column "Название диагноза" \
    --index-file "./mkb_index.faiss" \
    --batch-file "diagnoses.xlsx" \
    --query-column "Query" \
    --output-column "МКБ-10 топ-3" \
    --top-n 3 \
    --format sentences \
    "diagnoses.xlsx"
```

## 6. Только скоры (для анализа)

```bash
python diagnosis_rag.py \
    --load \
    --input-file "./mkb10.xlsx" \
    --column "Название диагноза" \
    --index-file "./mkb_index.faiss" \
    --batch-file "queries.xlsx" \
    --query-column "Diagnosis" \
    --top-n 5 \
    --format scores \
    "queries_with_scores.xlsx"
```

## 7. Одиночный запрос

```bash
python diagnosis_rag.py \
    --load \
    --input-file "./mkb10.xlsx" \
    --column "Название диагноза" \
    --index-file "./mkb_index.faiss" \
    --query "сахарный диабет" \
    "result.json"
```
