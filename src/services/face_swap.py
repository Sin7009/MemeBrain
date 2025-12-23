from PIL import Image
from typing import Optional
from .config import config
import logging
import os

# Импорты для face swap (могут отсутствовать, если библиотеки не установлены)
try:
    import cv2
    import insightface
    from insightface.app import FaceAnalysis
    import numpy as np
    FACE_SWAP_AVAILABLE = True
except ImportError:
    FACE_SWAP_AVAILABLE = False
    logging.warning("Face swap libraries not available. Install insightface, onnxruntime, opencv-python to enable.")

class FaceSwapper:
    """
    Класс для замены лица на изображении. 
    Использует InsightFace для детекции и замены лиц.
    """
    def __init__(self):
        self.enabled = config.FACE_SWAP_ENABLED and FACE_SWAP_AVAILABLE
        self.app = None
        self.swapper = None
        
        if config.FACE_SWAP_ENABLED and not FACE_SWAP_AVAILABLE:
            logging.error("FaceSwapper: Включена в конфиге, но библиотеки не установлены!")
            logging.error("Установите: pip install insightface onnxruntime opencv-python")
        elif self.enabled:
            try:
                logging.info("FaceSwapper: Инициализация моделей InsightFace...")
                # Инициализация FaceAnalysis для детекции лиц
                self.app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
                self.app.prepare(ctx_id=-1, det_size=(640, 640))
                
                # Загрузка модели swapper
                # Модель должна быть скачана заранее или будет загружена автоматически
                self.swapper = insightface.model_zoo.get_model('inswapper_128.onnx', 
                                                               providers=['CPUExecutionProvider'])
                logging.info("FaceSwapper: Успешно инициализирована!")
            except Exception as e:
                logging.error(f"FaceSwapper: Ошибка инициализации: {e}")
                self.enabled = False
        else:
            logging.info("FaceSwapper: Отключена в конфигурации.")

    def swap_face(self, template_image_path: str, user_avatar_path: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        Меняет лицо на шаблоне, используя аватар пользователя.
        
        Args:
            template_image_path: Путь к шаблону мема
            user_avatar_path: Путь к аватару пользователя
            output_path: Путь для сохранения результата (опционально)
            
        Returns:
            Путь к результату или None в случае ошибки
        """
        if not self.enabled:
            # Если отключено, просто возвращаем оригинальный путь
            return template_image_path
        
        if not os.path.exists(template_image_path):
            logging.error(f"Template image not found: {template_image_path}")
            return template_image_path
            
        if not os.path.exists(user_avatar_path):
            logging.error(f"User avatar not found: {user_avatar_path}")
            return template_image_path
        
        try:
            logging.info("FaceSwapper: Выполняется замена лица...")
            
            # Загрузка изображений
            img_target = cv2.imread(template_image_path)
            img_source = cv2.imread(user_avatar_path)
            
            if img_target is None or img_source is None:
                logging.error("Failed to load images")
                return template_image_path
            
            # Детекция лиц на исходном изображении (аватар)
            faces_source = self.app.get(img_source)
            if not faces_source:
                logging.warning("No face detected in user avatar")
                return template_image_path
            
            # Детекция лиц на целевом изображении (шаблон)
            faces_target = self.app.get(img_target)
            if not faces_target:
                logging.warning("No face detected in template")
                return template_image_path
            
            # Берем первое найденное лицо из аватара
            source_face = faces_source[0]
            
            # Применяем swap для каждого лица на шаблоне
            result = img_target.copy()
            for target_face in faces_target:
                result = self.swapper.get(result, target_face, source_face, paste_back=True)
            
            # Сохранение результата
            if output_path is None:
                output_path = template_image_path.replace('.jpg', '_swapped.jpg')
            
            cv2.imwrite(output_path, result)
            logging.info(f"FaceSwapper: Успешно! Результат: {output_path}")
            return output_path
            
        except Exception as e:
            logging.error(f"FaceSwapper: Ошибка при замене лица: {e}")
            return template_image_path
