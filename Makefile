.PHONY: help install test test-unit test-integration test-e2e test-stress test-all test-coverage test-fast lint clean

# Цвета для красивого вывода
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Показать справку по доступным командам
	@echo "$(CYAN)MemeBrain - Доступные команды:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Установить все зависимости
	@echo "$(YELLOW)Установка зависимостей...$(NC)"
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install pytest-cov pytest-timeout pytest-asyncio pytest-mock
	@echo "$(GREEN)✓ Зависимости установлены$(NC)"

test: ## Запустить все тесты
	@echo "$(YELLOW)Запуск всех тестов...$(NC)"
	PYTHONPATH=. pytest tests/ --ignore=tests/test_generation_integration_legacy.py
	@echo "$(GREEN)✓ Все тесты выполнены$(NC)"

test-unit: ## Запустить только юнит-тесты
	@echo "$(YELLOW)Запуск юнит-тестов...$(NC)"
	PYTHONPATH=. pytest tests/test_config.py tests/test_history.py tests/test_llm.py tests/test_image_gen.py tests/test_search.py tests/test_utils.py tests/test_validation.py -v
	@echo "$(GREEN)✓ Юнит-тесты выполнены$(NC)"

test-integration: ## Запустить интеграционные тесты
	@echo "$(YELLOW)Запуск интеграционных тестов...$(NC)"
	PYTHONPATH=. pytest tests/test_handlers.py tests/test_handlers_extended.py -v
	@echo "$(GREEN)✓ Интеграционные тесты выполнены$(NC)"

test-e2e: ## Запустить E2E тесты
	@echo "$(YELLOW)Запуск E2E тестов...$(NC)"
	PYTHONPATH=. pytest tests/test_e2e_integration.py -v
	@echo "$(GREEN)✓ E2E тесты выполнены$(NC)"

test-stress: ## Запустить стресс-тесты
	@echo "$(YELLOW)Запуск стресс-тестов...$(NC)"
	PYTHONPATH=. pytest tests/test_stress.py -v
	@echo "$(GREEN)✓ Стресс-тесты выполнены$(NC)"

test-destructive: ## Запустить деструктивные тесты (граничные случаи)
	@echo "$(YELLOW)Запуск деструктивных тестов...$(NC)"
	PYTHONPATH=. pytest tests/test_destructive_*.py -v
	@echo "$(GREEN)✓ Деструктивные тесты выполнены$(NC)"

test-all: ## Запустить все категории тестов последовательно
	@echo "$(CYAN)═══════════════════════════════════════$(NC)"
	@echo "$(CYAN)  КОМПЛЕКСНЫЙ ЗАПУСК ВСЕХ ТЕСТОВ$(NC)"
	@echo "$(CYAN)═══════════════════════════════════════$(NC)"
	@make test-unit
	@echo ""
	@make test-integration
	@echo ""
	@make test-e2e
	@echo ""
	@make test-stress
	@echo ""
	@make test-destructive
	@echo ""
	@echo "$(GREEN)✓✓✓ ВСЕ ТЕСТЫ УСПЕШНО ВЫПОЛНЕНЫ! ✓✓✓$(NC)"

test-coverage: ## Запустить тесты с отчетом о покрытии
	@echo "$(YELLOW)Запуск тестов с coverage...$(NC)"
	PYTHONPATH=. pytest tests/ --ignore=tests/test_generation_integration_legacy.py --cov=src --cov-report=html --cov-report=term-missing --cov-report=xml
	@echo "$(GREEN)✓ Отчет о покрытии создан в htmlcov/index.html$(NC)"

test-fast: ## Быстрые тесты (без медленных и стресс-тестов)
	@echo "$(YELLOW)Запуск быстрых тестов...$(NC)"
	PYTHONPATH=. pytest tests/ --ignore=tests/test_stress.py --ignore=tests/test_e2e_integration.py --ignore=tests/test_generation_integration_legacy.py -v
	@echo "$(GREEN)✓ Быстрые тесты выполнены$(NC)"

test-verbose: ## Запустить тесты с максимальной детализацией
	@echo "$(YELLOW)Запуск тестов в verbose режиме...$(NC)"
	PYTHONPATH=. pytest tests/ --ignore=tests/test_generation_integration_legacy.py -vv -s
	@echo "$(GREEN)✓ Тесты выполнены$(NC)"

lint: ## Проверить код линтером (если установлен flake8 или ruff)
	@echo "$(YELLOW)Проверка кода линтером...$(NC)"
	@if command -v ruff > /dev/null; then \
		ruff check src/ tests/ --exclude tests/test_generation_integration_legacy.py; \
		echo "$(GREEN)✓ Проверка ruff завершена$(NC)"; \
	elif command -v flake8 > /dev/null; then \
		flake8 src/ tests/ --exclude=tests/test_generation_integration_legacy.py --max-line-length=120 --ignore=E501,W503; \
		echo "$(GREEN)✓ Проверка flake8 завершена$(NC)"; \
	else \
		echo "$(YELLOW)! Линтер не установлен (установите ruff или flake8)$(NC)"; \
	fi

format: ## Форматировать код (если установлен black или ruff)
	@echo "$(YELLOW)Форматирование кода...$(NC)"
	@if command -v ruff > /dev/null; then \
		ruff format src/ tests/; \
		echo "$(GREEN)✓ Код отформатирован с помощью ruff$(NC)"; \
	elif command -v black > /dev/null; then \
		black src/ tests/ --line-length=120; \
		echo "$(GREEN)✓ Код отформатирован с помощью black$(NC)"; \
	else \
		echo "$(YELLOW)! Форматтер не установлен (установите ruff или black)$(NC)"; \
	fi

clean: ## Удалить временные файлы и кеш
	@echo "$(YELLOW)Очистка временных файлов...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov/ .ruff_cache/ 2>/dev/null || true
	@echo "$(GREEN)✓ Временные файлы удалены$(NC)"

run: ## Запустить бота
	@echo "$(YELLOW)Запуск бота...$(NC)"
	python -m src.main

check: clean lint test ## Полная проверка: очистка + линтинг + тесты
	@echo "$(GREEN)✓✓✓ Проверка завершена успешно! ✓✓✓$(NC)"

ci: ## Эмуляция CI пайплайна локально
	@echo "$(CYAN)═══════════════════════════════════════$(NC)"
	@echo "$(CYAN)  ЭМУЛЯЦИЯ CI ПАЙПЛАЙНА$(NC)"
	@echo "$(CYAN)═══════════════════════════════════════$(NC)"
	@make clean
	@make install
	@make lint || true
	@make test-coverage
	@echo "$(GREEN)✓✓✓ CI пайплайн завершен! ✓✓✓$(NC)"

# По умолчанию показываем справку
.DEFAULT_GOAL := help
