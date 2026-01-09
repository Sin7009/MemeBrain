# Модели для Face Swap

Эта директория содержит модели для функции замены лиц.

## Необходимые модели

### inswapper_128.onnx

Модель для замены лиц от InsightFace.

**Скачать:**
- GitHub Release: https://github.com/deepinsight/insightface/releases/download/v0.7/inswapper_128.onnx
- Размер: ~554 MB

**Установка:**
1. Скачайте файл `inswapper_128.onnx`
2. Поместите его в эту директорию: `models/inswapper_128.onnx`
3. Установите необходимые зависимости (см. ниже)

## Зависимости

Для использования face swap необходимо установить дополнительные библиотеки:

```bash
pip install insightface==0.7.3
pip install onnxruntime>=1.15.0
pip install opencv-python>=4.8.0
```

## Включение функции

После установки моделей и зависимостей, включите face swap в `.env`:

```env
FACE_SWAP_ENABLED=True
```

## Примечание

Модели InsightFace требуют значительных вычислительных ресурсов:
- **CPU**: Работает, но медленно (5-10 секунд на замену)
- **GPU**: Рекомендуется для продакшена (< 1 секунды)

Для использования GPU установите `onnxruntime-gpu` вместо `onnxruntime`.

## Лицензия

Модели InsightFace распространяются под лицензией MIT.
См. https://github.com/deepinsight/insightface для деталей.
