"""Вспомогательные функции для OpenAPI-метаданных FastAPI-приложения."""

from __future__ import annotations

from importlib.metadata import (
    PackageNotFoundError,
)
from importlib.metadata import (
    version as load_package_version,
)
from typing import Any

DEFAULT_OPENAPI_LANGUAGE = "ru"
OPENAPI_LANGUAGE_LABELS = {
    "ru": "Русский",
    "en": "English",
}

OPENAPI_DESCRIPTION = (
    "Надежный серверный API для генерации рецептов с помощью ИИ по расписанию, "
    "публикации и выдачи опубликованных рецептов.\n\n"
    "Используйте группу `Публичное API` для клиентобезопасного чтения рецептов, "
    "`Администрирование` для операторских действий, `Генерация` для ручного запуска "
    "генерации и проверки заданий, а `Состояние сервиса` для публичной проверки "
    "доступности и авторизованной проверки готовности зависимостей."
)

OPENAPI_TAGS = [
    {
        "name": "Публичное API",
        "description": (
            "Публичные эндпоинты рецептов, которые отдают только опубликованный "
            "и клиентобезопасный контент."
        ),
    },
    {
        "name": "Администрирование",
        "description": (
            "Аутентифицированные операторские эндпоинты для публикации "
            "и операционного управления."
        ),
    },
    {
        "name": "Генерация",
        "description": "Эндпоинты для ручного запуска генерации и просмотра статуса заданий.",
    },
    {
        "name": "Состояние сервиса",
        "description": "Эндпоинты для проверки доступности API и готовности его зависимостей.",
    },
]

ENGLISH_OPENAPI_TRANSLATIONS = {
    OPENAPI_DESCRIPTION: (
        "Trusted backend API for scheduled AI recipe generation, publication workflows, "
        "and public recipe delivery.\n\n"
        "Use the `Public API` group for client-safe recipe reads, `Administration` for "
        "operator-only controls, `Generation` for manual generation dispatch and job "
        "inspection, and `Service Health` for public liveness or authenticated readiness "
        "checks."
    ),
    "Публичное API": "Public API",
    (
        "Публичные эндпоинты рецептов, которые отдают только опубликованный "
        "и клиентобезопасный контент."
    ): (
        "Public recipe endpoints that expose only published, client-safe content."
    ),
    "Администрирование": "Administration",
    "Аутентифицированные операторские эндпоинты для публикации и операционного управления.": (
        "Authenticated operator endpoints for publication and operational controls."
    ),
    "Генерация": "Generation",
    "Эндпоинты для ручного запуска генерации и просмотра статуса заданий.": (
        "Manual generation dispatch and generation job inspection endpoints."
    ),
    "Состояние сервиса": "Service Health",
    "Эндпоинты для проверки доступности API и готовности его зависимостей.": (
        "Liveness and readiness endpoints for API and dependency checks."
    ),
    "Проверить доступность API": "Check API availability",
    "Возвращает укороченный публичный статус сервиса без деталей внутренних зависимостей.": (
        "Returns a shallow public service status without internal dependency details."
    ),
    "Публичный статус доступности API.": "Public API availability status.",
    "Получить последний опубликованный рецепт": "Get the latest published recipe",
    "Возвращает последний опубликованный рецепт в клиентобезопасном формате.": (
        "Returns the latest published recipe in a client-safe format."
    ),
    "Последний опубликованный рецепт.": "Latest published recipe.",
    "Получить ленту опубликованных рецептов": "Get the published recipe feed",
    "Возвращает страницу ленты опубликованных рецептов с поддержкой пагинации.": (
        "Returns a paginated page of the published recipe feed."
    ),
    "Страница ленты опубликованных рецептов.": "Published recipe feed page.",
    "Максимальное количество опубликованных рецептов в ответе.": (
        "Maximum number of published recipes to return."
    ),
    "Смещение от начала ленты в опубликованных рецептах, начиная с нуля.": (
        "Zero-based number of published recipes to skip."
    ),
    "Получить опубликованный рецепт по идентификатору": "Get a published recipe by ID",
    "Возвращает опубликованный рецепт по его идентификатору в клиентобезопасном формате.": (
        "Returns a published recipe by identifier in a client-safe format."
    ),
    "Опубликованный рецепт.": "Published recipe.",
    "Идентификатор опубликованного рецепта.": "Published recipe identifier.",
    "Запустить генерацию сейчас": "Run generation now",
    (
        "Подготавливает и, если требуется, запускает генерацию "
        "для текущего часового слота или переданного времени UTC."
    ): (
        "Prepares and, when needed, starts generation for the current hourly slot or the "
        "provided UTC time."
    ),
    "Статус постановки задания генерации.": "Generation dispatch status.",
    "Параметры запуска": "Run parameters",
    "Необязательные параметры ручного запуска генерации.": (
        "Optional parameters for manual generation dispatch."
    ),
    "Получить статус задания генерации": "Get generation job status",
    "Возвращает текущее состояние задания генерации по его идентификатору.": (
        "Returns the current state of a generation job by its identifier."
    ),
    "Текущее состояние задания генерации.": "Current generation job state.",
    "Идентификатор задания генерации.": "Generation job identifier.",
    "Проверить готовность зависимостей": "Check dependency readiness",
    "Возвращает детальный статус внутренних зависимостей для авторизованного администратора.": (
        "Returns detailed internal dependency readiness for an authenticated administrator."
    ),
    "Статус готовности зависимостей.": "Dependency readiness status.",
    "Опубликовать рецепт": "Publish recipe",
    "Переводит рецепт в опубликованное состояние, если он готов к публикации.": (
        "Moves a recipe to the published state when it is ready for publication."
    ),
    "Идентификатор рецепта.": "Recipe identifier.",
    "Снять рецепт с публикации": "Unpublish recipe",
    "Переводит рецепт из опубликованного состояния обратно в непубличное.": (
        "Moves a recipe from the published state back to a non-public state."
    ),
    "Рецепт после снятия с публикации.": "Recipe after unpublishing.",
    (
        "Bearer-токен для доступа к административным эндпоинтам. Используйте токен, "
        "настроенный через ADMIN_IDENTITIES или ADMIN_BEARER_TOKEN."
    ): (
        "Bearer token for authenticated admin endpoints. Use a token configured through "
        "ADMIN_IDENTITIES or ADMIN_BEARER_TOKEN."
    ),
    "Непрозрачный токен": "Opaque token",
    "Стандартизированная схема ошибки API.": "Standardized API error payload.",
    "Необязательное тело запроса для ручного запуска генерации.": (
        "Optional manual generation request payload."
    ),
    (
        "UTC-время часового слота, для которого нужно запустить генерацию. "
        "Если не указано, используется текущий UTC-час."
    ): (
        "UTC hour slot to run generation for. If omitted, the current UTC hour is used."
    ),
    "Сериализованный ответ со статусом задания генерации.": "Serialized generation job response.",
    "Тип задания генерации.": "Generation job type.",
    "UTC-время часового слота, к которому относится задание.": (
        "UTC hour slot associated with the job."
    ),
    "Идемпотентный ключ, защищающий от повторного запуска.": (
        "Idempotency key that protects against duplicate execution."
    ),
    "Время начала выполнения задания в UTC.": "Generation job start time in UTC.",
    "Время завершения задания в UTC.": "Generation job finish time in UTC.",
    "Текст ошибки, если задание завершилось неуспешно.": "Error message if the job failed.",
    "Количество повторных попыток выполнения.": "Number of retry attempts.",
    "Время создания задания в UTC.": "Generation job creation time in UTC.",
    "Ответ эндпоинта ручного запуска генерации.": (
        "Response returned from the manual generation endpoint."
    ),
    "UTC-время часового слота, для которого обработан запрос.": (
        "UTC hour slot processed by the request."
    ),
    "Идентификатор рецепта, если он уже был создан.": (
        "Recipe identifier, if a recipe has already been created."
    ),
    "Признак того, что выполнение было поставлено в фоновую очередь.": (
        "Whether execution was enqueued for background processing."
    ),
    "Человекочитаемое пояснение результата постановки задания.": (
        "Human-readable dispatch result message."
    ),
    "Статус отдельного компонента инфраструктуры.": "Per-component infrastructure status.",
    "Статус конкретного компонента.": "Status of the specific component.",
    "Дополнительная диагностическая информация, если она доступна.": (
        "Additional diagnostic information, when available."
    ),
    "Верхнеуровневый ответ о готовности сервиса.": "Top-level service readiness response.",
    "Общий статус готовности сервиса.": "Overall service readiness status.",
    "Время формирования ответа в UTC.": "Response generation time in UTC.",
    "Статусы отдельных зависимостей и компонентов.": (
        "Statuses of individual dependencies and components."
    ),
    "Укороченный публичный ответ о доступности сервиса.": (
        "Shallow public service availability response."
    ),
    "Публичный статус доступности сервиса.": "Public service availability status.",
    "Схема ингредиента в ответе API.": "Ingredient response item.",
    "Схема шага рецепта в ответе API.": "Recipe step response item.",
    "Снимок параметров генерации, сохраненных вместе с рецептом.": (
        "Generation parameter snapshot stored with a recipe."
    ),
    "Метаданные изображения рецепта, доступные клиентам.": (
        "Recipe image metadata exposed to clients."
    ),
    "Клиентобезопасные метаданные изображения рецепта для публичного API.": (
        "Client-safe recipe image metadata for the public API."
    ),
    "Краткий ответ с рецептом для ленты и административных списков.": (
        "Recipe summary response for feed and admin list endpoints."
    ),
    "Клиентобезопасная краткая схема рецепта для публичной ленты.": (
        "Client-safe recipe summary for the public feed."
    ),
    "Подробная схема рецепта для административного и внутреннего API.": (
        "Detailed recipe schema for admin and internal API consumers."
    ),
    "Клиентобезопасная подробная схема рецепта для публичного API.": (
        "Client-safe detailed recipe schema for the public API."
    ),
    "Ответ с лентой опубликованных рецептов.": "Published recipe feed response.",
    "Ошибка валидации запроса": "Validation Error",
    "HTTPОшибкаВалидации": "HTTPValidationError",
    "Ошибки валидации входных данных HTTP-запроса.": "HTTP request validation errors.",
    "Ошибки": "Detail",
    "ОшибкаВалидации": "ValidationError",
    "Описание конкретной ошибки валидации.": "Description of a specific validation error.",
    "Путь": "Location",
    "Сообщение": "Message",
    "Тип ошибки": "Error Type",
    "Входные данные": "Input",
    "Контекст": "Context",
}

OPENAPI_TEXT_TRANSLATIONS = {
    "en": ENGLISH_OPENAPI_TRANSLATIONS,
}


def normalize_openapi_language(language: str | None) -> str:
    """Normalize the requested OpenAPI language to a supported value."""

    if language in OPENAPI_LANGUAGE_LABELS:
        return language
    return DEFAULT_OPENAPI_LANGUAGE


def translate_openapi_texts_in_place(schema: Any, *, language: str) -> None:
    """Translate human-readable OpenAPI texts in place for the requested language."""

    translations = OPENAPI_TEXT_TRANSLATIONS.get(normalize_openapi_language(language))
    if not translations:
        return
    _translate_node_in_place(schema, translations)


def _translate_node_in_place(node: Any, translations: dict[str, str]) -> None:
    """Recursively translate string values inside a nested OpenAPI structure."""

    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(value, str):
                node[key] = translations.get(value, value)
            else:
                _translate_node_in_place(value, translations)
        return
    if isinstance(node, list):
        for index, value in enumerate(node):
            if isinstance(value, str):
                node[index] = translations.get(value, value)
            else:
                _translate_node_in_place(value, translations)


def localize_generated_openapi_terms(schema: dict[str, Any]) -> None:
    """Локализует автоматически добавленные FastAPI элементы OpenAPI-схемы."""

    for path_item in schema.get("paths", {}).values():
        if not isinstance(path_item, dict):
            continue
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            responses = operation.get("responses")
            if not isinstance(responses, dict):
                continue
            validation_response = responses.get("422")
            if isinstance(validation_response, dict) and validation_response.get(
                "description"
            ) == "Validation Error":
                validation_response["description"] = "Ошибка валидации запроса"

    components = schema.get("components", {})
    if not isinstance(components, dict):
        return
    schemas = components.get("schemas", {})
    if not isinstance(schemas, dict):
        return

    http_validation_error = schemas.get("HTTPValidationError")
    if isinstance(http_validation_error, dict):
        http_validation_error["title"] = "HTTPОшибкаВалидации"
        http_validation_error["description"] = "Ошибки валидации входных данных HTTP-запроса."
        properties = http_validation_error.get("properties", {})
        if isinstance(properties, dict):
            detail = properties.get("detail")
            if isinstance(detail, dict):
                detail["title"] = "Ошибки"

    validation_error = schemas.get("ValidationError")
    if isinstance(validation_error, dict):
        validation_error["title"] = "ОшибкаВалидации"
        validation_error["description"] = "Описание конкретной ошибки валидации."
        properties = validation_error.get("properties", {})
        if isinstance(properties, dict):
            if isinstance(properties.get("loc"), dict):
                properties["loc"]["title"] = "Путь"
            if isinstance(properties.get("msg"), dict):
                properties["msg"]["title"] = "Сообщение"
            if isinstance(properties.get("type"), dict):
                properties["type"]["title"] = "Тип ошибки"
            if isinstance(properties.get("input"), dict):
                properties["input"]["title"] = "Входные данные"
            if isinstance(properties.get("ctx"), dict):
                properties["ctx"]["title"] = "Контекст"


def get_application_version() -> str:
    """Return the installed project version with a safe fallback."""

    try:
        return load_package_version("pech-da-lozhka-backend")
    except PackageNotFoundError:
        return "0.1.0"
