# diagnosis rag

## 1. СОЗДАТЬ новую базу и сохранить на диск

python diagnosis_rag.py \
    --build \
    --input-file "./mkb10.xlsx" \
    --column "Название диагноза" \
    --index-file "./mkb_index.faiss" \
    --top-k 15 \
    --sentences-file "./sentences.pkl"

## 2. ЗАГРУЗИТЬ готовую базу и выполнить поиск

python diagnosis_rag.py \
    --load \
    --index-file "./mkb_index.faiss" \
    --sentences-file "./sentences.pkl" \
    --query "сахарный диабет" \
    --top-k 15 \
    "results.json"

## 3. СОЗДАТЬ базу и СРАЗУ выполнить поиск

python diagnosis_rag.py \
    --build \
    --input-file "mkb10.xlsx" \
    --query "членистоногими" \
    --top-k 15 \
    "results.json"
