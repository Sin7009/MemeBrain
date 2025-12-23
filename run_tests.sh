#!/bin/bash
# Скрипт для комплексного запуска всех тестов MemeBrain

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Функция для печати заголовков
print_header() {
    echo -e "\n${CYAN}═══════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════${NC}\n"
}

# Функция для печати успеха
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Функция для печати ошибки
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Функция для печати информации
print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Проверка наличия pytest
if ! command -v pytest &> /dev/null; then
    print_error "pytest не установлен!"
    print_info "Установите зависимости: pip install -r requirements.txt"
    exit 1
fi

# Установка переменных окружения для тестов
export TELEGRAM_BOT_TOKEN="dummy_token"
export TAVILY_API_KEY="dummy_key"
export OPENROUTER_API_KEY="dummy_key"
export PYTHONPATH="."

# Счетчики
total_tests=0
failed_tests=0

# Функция для запуска категории тестов
run_test_category() {
    local category=$1
    local test_path=$2
    local description=$3
    
    print_header "$description"
    
    if pytest "$test_path" -v --tb=short; then
        print_success "$category тесты пройдены успешно"
        return 0
    else
        print_error "$category тесты провалились"
        failed_tests=$((failed_tests + 1))
        return 1
    fi
}

# Главная функция
main() {
    print_header "КОМПЛЕКСНЫЙ ЗАПУСК ТЕСТОВ MEMEBRAIN"
    
    echo -e "${BLUE}Версия Python: $(python --version)${NC}"
    echo -e "${BLUE}Версия pytest: $(pytest --version)${NC}\n"
    
    # 1. Unit тесты
    run_test_category "Unit" "tests/test_config.py tests/test_history.py tests/test_llm.py tests/test_image_gen.py tests/test_search.py tests/test_utils.py tests/test_validation.py" "1. ЮНИТ-ТЕСТЫ (Unit Tests)"
    
    # 2. Extended тесты
    run_test_category "Extended" "tests/test_history_extended.py tests/test_llm_extended.py tests/test_handlers_extended.py" "2. РАСШИРЕННЫЕ ТЕСТЫ (Extended Tests)"
    
    # 3. Integration тесты
    run_test_category "Integration" "tests/test_handlers.py" "3. ИНТЕГРАЦИОННЫЕ ТЕСТЫ (Integration Tests)"
    
    # 4. E2E тесты
    run_test_category "E2E" "tests/test_e2e_integration.py" "4. END-TO-END ТЕСТЫ (E2E Tests)"
    
    # 5. Stress тесты
    run_test_category "Stress" "tests/test_stress.py" "5. СТРЕСС-ТЕСТЫ (Stress Tests)"
    
    # 6. Destructive тесты
    run_test_category "Destructive" "tests/test_destructive_meme.py tests/test_destructive_text_wrapping.py" "6. ДЕСТРУКТИВНЫЕ ТЕСТЫ (Destructive Tests)"
    
    # Итоговый отчет
    print_header "ИТОГОВЫЙ ОТЧЕТ"
    
    if [ $failed_tests -eq 0 ]; then
        echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║  ✓✓✓ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО! ✓✓✓  ║${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════╝${NC}\n"
        exit 0
    else
        echo -e "${RED}╔════════════════════════════════════════╗${NC}"
        echo -e "${RED}║      ОБНАРУЖЕНЫ ПРОВАЛЕННЫЕ ТЕСТЫ      ║${NC}"
        echo -e "${RED}║  Проваленных категорий: $failed_tests               ║${NC}"
        echo -e "${RED}╚════════════════════════════════════════╝${NC}\n"
        exit 1
    fi
}

# Обработка аргументов командной строки
case "${1:-all}" in
    unit)
        run_test_category "Unit" "tests/test_config.py tests/test_history.py tests/test_llm.py tests/test_image_gen.py tests/test_search.py tests/test_utils.py" "ЮНИТ-ТЕСТЫ"
        ;;
    integration)
        run_test_category "Integration" "tests/test_handlers.py tests/test_handlers_extended.py" "ИНТЕГРАЦИОННЫЕ ТЕСТЫ"
        ;;
    e2e)
        run_test_category "E2E" "tests/test_e2e_integration.py" "E2E ТЕСТЫ"
        ;;
    stress)
        run_test_category "Stress" "tests/test_stress.py" "СТРЕСС-ТЕСТЫ"
        ;;
    destructive)
        run_test_category "Destructive" "tests/test_destructive_*.py" "ДЕСТРУКТИВНЫЕ ТЕСТЫ"
        ;;
    coverage)
        print_header "ТЕСТЫ С ПОКРЫТИЕМ КОДА"
        pytest tests/ --ignore=tests/test_generation_integration_legacy.py --cov=src --cov-report=html --cov-report=term-missing --cov-report=xml -v
        print_success "Отчет о покрытии создан в htmlcov/index.html"
        ;;
    fast)
        print_header "БЫСТРЫЕ ТЕСТЫ (без стресс-тестов)"
        pytest tests/ --ignore=tests/test_stress.py --ignore=tests/test_e2e_integration.py --ignore=tests/test_generation_integration_legacy.py -v
        ;;
    all)
        main
        ;;
    help)
        echo "Использование: ./run_tests.sh [категория]"
        echo ""
        echo "Доступные категории:"
        echo "  all          - Запустить все тесты (по умолчанию)"
        echo "  unit         - Только юнит-тесты"
        echo "  integration  - Только интеграционные тесты"
        echo "  e2e          - Только E2E тесты"
        echo "  stress       - Только стресс-тесты"
        echo "  destructive  - Только деструктивные тесты"
        echo "  coverage     - Тесты с покрытием кода"
        echo "  fast         - Быстрые тесты (без медленных)"
        echo "  help         - Показать эту справку"
        ;;
    *)
        print_error "Неизвестная категория: $1"
        echo "Используйте './run_tests.sh help' для справки"
        exit 1
        ;;
esac
