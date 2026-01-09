from PIL import Image
from typing import Optional
from .config import config
import logging
import os

# Попытка импорта insightface и opencv
try:
    import cv2
    import numpy as np
    import insightface
    from insightface.app import FaceAnalysis
    FACE_SWAP_AVAILABLE = True
except ImportError:
    FACE_SWAP_AVAILABLE = False
    logging.info("FaceSwap: insightface/opencv не установлены. Функция замены лиц недоступна.")

class FaceSwapper:
    """
    Класс для замены лица на изображении с использованием InsightFace.
    Требует установки: insightface, onnxruntime, opencv-python
    """
    def __init__(self):
        self.enabled = config.FACE_SWAP_ENABLED and FACE_SWAP_AVAILABLE
        self.app = None
        self.swapper = None
        
        if config.FACE_SWAP_ENABLED and not FACE_SWAP_AVAILABLE:
            logging.warning(
                "FaceSwapper: Включен в конфигурации, но необходимые библиотеки не установлены!\n"
                "Установите: pip install insightface onnxruntime opencv-python"
            )
            return
        
        if self.enabled:
            try:
                logging.info("FaceSwapper: Инициализация моделей...")
                # Инициализация FaceAnalysis для детекции лиц
                self.app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
                self.app.prepare(ctx_id=-1, det_size=(640, 640))  # -1 для CPU
                
                # Загрузка модели замены лиц
                # Модель должна быть загружена отдельно
                # Скачать можно с: https://github.com/deepinsight/insightface/releases
                model_path = os.path.join('models', 'inswapper_128.onnx')
                if os.path.exists(model_path):
                    self.swapper = insightface.model_zoo.get_model(model_path, providers=['CPUExecutionProvider'])
                    logging.info("FaceSwapper: Инициализация успешна!")
                else:
                    logging.warning(
                        f"FaceSwapper: Модель не найдена по пути {model_path}\n"
                        "Скачайте inswapper_128.onnx и поместите в директорию models/"
                    )
                    self.enabled = False
            except Exception as e:
                logging.error(f"FaceSwapper: Ошибка инициализации: {e}")
                self.enabled = False
        else:
            logging.info("FaceSwapper: Отключена в конфигурации.")

    def swap_face(self, template_image_path: str, user_avatar_path: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        Меняет лицо на шаблоне, используя аватар пользователя.
        
        Args:
            template_image_path: Путь к изображению-шаблону (где заменить лицо)
            user_avatar_path: Путь к аватару пользователя (откуда взять лицо)
            output_path: Путь для сохранения результата (опционально)
        
        Returns:
            Путь к результирующему изображению или None при ошибке
        """
        if not self.enabled:
            # Если отключено, просто возвращаем оригинальный путь
            logging.debug("FaceSwapper: Отключена, возвращаем оригинал")
            return template_image_path
        
        if not self.swapper:
            logging.warning("FaceSwapper: Модель не загружена")
            return template_image_path
        
        try:
            # Загрузка изображений
            img_target = cv2.imread(template_image_path)
            img_source = cv2.imread(user_avatar_path)
            
            if img_target is None:
                logging.error(f"FaceSwapper: Не удалось загрузить шаблон {template_image_path}")
                return template_image_path
                
            if img_source is None:
                logging.error(f"FaceSwapper: Не удалось загрузить аватар {user_avatar_path}")
                return template_image_path
            
            # Детекция лиц на обоих изображениях
            faces_source = self.app.get(img_source)
            faces_target = self.app.get(img_target)
            
            if len(faces_source) == 0:
                logging.warning("FaceSwapper: Лицо не найдено на аватаре пользователя")
                return template_image_path
                
            if len(faces_target) == 0:
                logging.warning("FaceSwapper: Лицо не найдено на шаблоне")
                return template_image_path
            
            # Берем первое лицо из каждого изображения
            source_face = faces_source[0]
            
            # Заменяем лицо на каждом найденном лице в шаблоне
            result = img_target.copy()
            for target_face in faces_target:
                result = self.swapper.get(result, target_face, source_face, paste_back=True)
            
            # Определяем путь для сохранения
            if output_path is None:
                # Создаем уникальное имя на основе входных файлов
                base_name = os.path.splitext(os.path.basename(template_image_path))[0]
                output_path = f"{base_name}_swapped.jpg"
            
            # Сохраняем результат
            cv2.imwrite(output_path, result)
            logging.info(f"FaceSwapper: Успешно сохранено в {output_path}")
            return output_path
            
        except Exception as e:
            logging.error(f"FaceSwapper: Ошибка при замене лица: {e}")
            return template_image_path
    
    def is_available(self) -> bool:
        """Проверяет, доступна ли функция замены лиц."""
        return self.enabled and self.swapper is not None

