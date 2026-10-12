# Предсказание калорийности блюд

Проект решает задачу мультимодальной регрессии: по фотографии блюда, списку ингредиентов и массе порции модель предсказывает общую калорийность.

## Структура

- `data/` — CSV-файлы и изображения блюда;
- `dataset.py` — объединение метаданных, преобразование ингредиентов, Dataset и DataLoader;
- `utils.py` — модель, обучение, метрики, checkpoint и инференс;
- `config.yaml` — все параметры запуска;
- `2.ipynb` — EDA, обучение, тестирование и визуальный анализ ошибок;
- `artifacts/` — создаётся после обучения и содержит checkpoint, историю и test-предсказания.

## Установка

```bash
pip install torch torchvision torchaudio
pip install pandas numpy pillow matplotlib pyyaml
pip install albumentations timm transformers
```

Для первого запуска `timm` и `transformers` скачивают предобученные веса, поэтому нужен доступ к сети. Если CUDA-сборка PyTorch не поддерживает конкретный GPU, pipeline автоматически использует CPU.

## Запуск

Запустите Jupyter Notebook из этой директории:

```bash
cd /home/froschin/work/masters_degree_Roshchin_M25-555/работа_с_изображениями_и_текстом/2
jupyter notebook 2.ipynb
```

Все параметры обучения находятся в `config.yaml`. Обучение воспроизводится одной функцией:

```python
from utils import train

history = train("config.yaml")
```

После обучения ноутбук загружает `artifacts/best_model.pt`, считает MAE/RMSE/R² на test и визуализирует пять блюд с максимальной абсолютной ошибкой.
