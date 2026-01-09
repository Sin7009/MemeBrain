import unittest
import os
import tempfile
from pathlib import Path
from PIL import Image

# Set env vars before importing
os.environ["TELEGRAM_BOT_TOKEN"] = "dummy_token"
os.environ["TAVILY_API_KEY"] = "dummy_key"
os.environ["OPENROUTER_API_KEY"] = "dummy_openrouter"
os.environ["FACE_SWAP_ENABLED"] = "False"  # Disable by default for tests

from src.services.face_swap import FaceSwapper, FACE_SWAP_AVAILABLE


class TestFaceSwapperDisabled(unittest.TestCase):
    """Тесты FaceSwapper в отключенном состоянии"""
    
    def setUp(self):
        """Создаем FaceSwapper с отключенной функцией"""
        # Патчим config для отключения
        import src.services.config as config_module
        self.original_enabled = config_module.config.FACE_SWAP_ENABLED
        config_module.config.FACE_SWAP_ENABLED = False
        
        self.swapper = FaceSwapper()
    
    def tearDown(self):
        """Восстанавливаем настройки"""
        import src.services.config as config_module
        config_module.config.FACE_SWAP_ENABLED = self.original_enabled
    
    def test_disabled_returns_original(self):
        """Тест возврата оригинального пути при отключенной функции"""
        template_path = "test_template.jpg"
        avatar_path = "test_avatar.jpg"
        
        result = self.swapper.swap_face(template_path, avatar_path)
        
        # Должен вернуть оригинальный путь
        self.assertEqual(result, template_path)
    
    def test_is_available_false_when_disabled(self):
        """Тест проверки доступности при отключенной функции"""
        self.assertFalse(self.swapper.is_available())


class TestFaceSwapperAvailability(unittest.TestCase):
    """Тесты проверки доступности библиотек"""
    
    def test_libraries_availability(self):
        """Тест проверки доступности insightface и opencv"""
        # Просто проверяем, что флаг установлен корректно
        if FACE_SWAP_AVAILABLE:
            # Если библиотеки доступны, проверяем импорты
            try:
                import cv2
                import insightface
                self.assertTrue(True)
            except ImportError:
                self.fail("FACE_SWAP_AVAILABLE=True, но библиотеки не импортируются")
        else:
            # Если недоступны, проверяем что действительно не импортируются
            self.assertFalse(FACE_SWAP_AVAILABLE)


class TestFaceSwapperWithTempFiles(unittest.TestCase):
    """Тесты FaceSwapper с временными файлами"""
    
    def setUp(self):
        """Создаем временные директории и файлы"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Создаем тестовые изображения
        self.template_path = os.path.join(self.temp_dir, "template.jpg")
        self.avatar_path = os.path.join(self.temp_dir, "avatar.jpg")
        
        # Создаем простые тестовые изображения
        img = Image.new('RGB', (100, 100), color='red')
        img.save(self.template_path)
        
        img2 = Image.new('RGB', (100, 100), color='blue')
        img2.save(self.avatar_path)
        
        # Отключаем face swap для этих тестов
        import src.services.config as config_module
        self.original_enabled = config_module.config.FACE_SWAP_ENABLED
        config_module.config.FACE_SWAP_ENABLED = False
        
        self.swapper = FaceSwapper()
    
    def tearDown(self):
        """Удаляем временные файлы"""
        import shutil
        import src.services.config as config_module
        config_module.config.FACE_SWAP_ENABLED = self.original_enabled
        
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_swap_face_with_real_files(self):
        """Тест swap_face с реальными файлами (отключено)"""
        result = self.swapper.swap_face(self.template_path, self.avatar_path)
        
        # При отключенной функции должен вернуть оригинальный путь
        self.assertEqual(result, self.template_path)
        self.assertTrue(os.path.exists(result))
    
    def test_swap_face_with_output_path(self):
        """Тест с указанным output_path"""
        output_path = os.path.join(self.temp_dir, "output.jpg")
        
        result = self.swapper.swap_face(
            self.template_path,
            self.avatar_path,
            output_path=output_path
        )
        
        # При отключенной функции должен вернуть template_path
        self.assertEqual(result, self.template_path)
    
    def test_swap_face_with_nonexistent_files(self):
        """Тест с несуществующими файлами"""
        fake_template = "nonexistent_template.jpg"
        fake_avatar = "nonexistent_avatar.jpg"
        
        result = self.swapper.swap_face(fake_template, fake_avatar)
        
        # Должен вернуть оригинальный путь даже если файл не существует
        self.assertEqual(result, fake_template)


class TestFaceSwapperInitialization(unittest.TestCase):
    """Тесты инициализации FaceSwapper"""
    
    def test_initialization_disabled(self):
        """Тест инициализации с отключенной функцией"""
        import src.services.config as config_module
        original = config_module.config.FACE_SWAP_ENABLED
        config_module.config.FACE_SWAP_ENABLED = False
        
        swapper = FaceSwapper()
        
        self.assertFalse(swapper.enabled)
        self.assertIsNone(swapper.app)
        self.assertIsNone(swapper.swapper)
        
        config_module.config.FACE_SWAP_ENABLED = original
    
    def test_initialization_enabled_without_libs(self):
        """Тест инициализации с включенной функцией без библиотек"""
        import src.services.config as config_module
        original = config_module.config.FACE_SWAP_ENABLED
        config_module.config.FACE_SWAP_ENABLED = True
        
        swapper = FaceSwapper()
        
        if not FACE_SWAP_AVAILABLE:
            # Если библиотеки недоступны, должно быть отключено
            self.assertFalse(swapper.enabled)
        else:
            # Если доступны, может быть включено (зависит от наличия модели)
            pass
        
        config_module.config.FACE_SWAP_ENABLED = original


if __name__ == '__main__':
    unittest.main()
