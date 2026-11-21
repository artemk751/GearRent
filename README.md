# GearRent
- Це вебплатформа для оренди та прокату спорядження для активного відпочинку, туризму, спорту та фото або відеозйомки.

Застосунок вирішує проблему високої вартості купівлі дорогого обладнання для разових поїздок чи хобі. На сайті користувачі можуть переглядати каталог доступного спорядження, шукати товари за назвою, фільтрувати їх за категоріями, брендами та ціною оренди за добу, а також переглядати детальні характеристики товарів та інформацію про бренд або категорію.

## REST API Endpoints (`/api/v1`)

Усі дані передаються у форматі **JSON**.

### Товари (`/products`)
* `GET /products` — Отримати каталог (query: `search`, `category_id`, `brand_id`, `sort_by`).  
  * **Status:** `200 OK` | **Res:** `[{"id": 1, "name": "Намет", "price_per_day": 250.0, "is_available": true}]`
* `GET /products/{id}` — Деталі товару.  
  * **Status:** `200 OK` | **Res:** `{"id": 1, "name": "Намет", "description": "2-місний", "price_per_day": 250.0}`
* `POST /products` — Додати товар (Admin).  
  * **Req:** `{"name": "Рюкзак", "price_per_day": 180.0, "category_id": 1, "brand_id": 3}`  
  * **Status:** `201 Created` | **Res:** `{"id": 2, "name": "Рюкзак", "price_per_day": 180.0}`
* `PUT /products/{id}` — Оновити товар (Admin).  
  * **Req:** `{"name": "Рюкзак Pro", "price_per_day": 200.0}`  
  * **Status:** `200 OK` | **Res:** `{"id": 2, "name": "Рюкзак Pro", "price_per_day": 200.0}`
* `DELETE /products/{id}` — Видалити товар (Admin).  
  * **Status:** `204 No Content`

### Категорії (`/categories`)
* `GET /categories` — Список категорій.  
  * **Status:** `200 OK` | **Res:** `[{"id": 1, "name": "Намети"}]`
* `GET /categories/{id}/products` — Товари категорії.  
  * **Status:** `200 OK` | **Res:** `[{"id": 1, "name": "Намет", "price_per_day": 250.0}]`
* `POST /categories` — Створити категорію (Admin).  
  * **Req:** `{"name": "Альпінізм"}`  
  * **Status:** `201 Created` | **Res:** `{"id": 2, "name": "Альпінізм"}`


### Авторизація та Користувачі (`/auth`, `/users`)
Використовується JWT (`djangorestframework-simplejwt`). Усі URL записуються без завершального «/».

**Як передавати токен.** Захищені ендпоінти потребують заголовок:

```
Authorization: Bearer <access_token>
```

**Токени.** `access` живе 15 хвилин, `refresh` — 7 днів. Коли access закінчується, API повертає `401`. Клієнт надсилає refresh на `POST /auth/refresh`, отримує новий access (і новий refresh, бо ввімкнено ротацію) та повторює запит. Якщо refresh теж недійсний, користувач має увійти знову. **Logout** виконується на клієнті: збережені токени видаляються.

| Метод | URL | Доступ |
|---|---|---|
| POST | `/auth/register` | усі |
| POST | `/auth/login` | усі |
| POST | `/auth/refresh` | усі (потрібен refresh-токен) |
| GET | `/users/me` | авторизовані |
| GET | `/users` | лише адміністратори |

* `POST /auth/register` — Реєстрація.  
  * **Заголовки:** `Content-Type: application/json`  
  * **Req:** `{"username": "artem", "first_name": "Артем", "last_name": "К", "email": "artem@example.com", "password": "Str0ng!Pass-2026", "password_confirm": "Str0ng!Pass-2026"}`  
  * `first_name` і `last_name` необов'язкові. Обмеження: `username`, `first_name`, `last_name` — до 30 символів, `email` — до 254, `password` — від 8 до 128 символів та перевірка складності (не надто схожий на дані користувача, не з поширених, не лише з цифр). `username` та `email` унікальні, `password_confirm` має збігатися з `password`.  
  * **Status:** `201 Created` | **Res:** `{"id": 1, "username": "artem", "email": "artem@example.com", "first_name": "Артем", "last_name": "К", "is_staff": false}`  
  * **Status:** `400 Bad Request` | **Res:** `{"error": {"code": "bad_request", "message": "Передані дані некоректні. ...", "details": {"email": ["Введіть коректну email-адресу, наприклад name@example.com."], "password_confirm": ["Паролі не збігаються."]}}}`  
  * Пароль зберігається в базі лише у захешованому вигляді.
* `POST /auth/login` — Вхід у систему.  
  * **Req:** `{"username": "artem", "password": "Str0ng!Pass-2026"}`  
  * **Status:** `200 OK` | **Res:** `{"access": "<access_token>", "refresh": "<refresh_token>", "user": {"id": 1, "username": "artem", "email": "artem@example.com", "first_name": "Артем", "last_name": "К", "is_staff": false}}`  
  * **Status:** `401 Unauthorized` | **Res:** `{"error": {"code": "unauthorized", "message": "Невірне ім'я користувача або пароль."}}`
* `POST /auth/refresh` — Оновлення access-токена.  
  * **Req:** `{"refresh": "<refresh_token>"}`  
  * **Status:** `200 OK` | **Res:** `{"access": "<new_access>", "refresh": "<new_refresh>"}`  
  * **Status:** `401 Unauthorized` — refresh недійсний або прострочений.
* `GET /users/me` — Профіль поточного користувача.  
  * **Заголовки:** `Authorization: Bearer <access_token>`  
  * **Status:** `200 OK` | **Res:** `{"id": 1, "username": "artem", "email": "artem@example.com", "first_name": "Артем", "last_name": "К", "is_staff": false}`  
  * **Status:** `401 Unauthorized` — токена немає або він недійсний.
* `GET /users` — Список користувачів (лише адміністратор).  
  * **Заголовки:** `Authorization: Bearer <access_token>`  
  * **Status:** `200 OK` | **Res:** масив користувачів, як у `/users/me`  
  * **Status:** `401 Unauthorized` — немає токена; `403 Forbidden` — користувач не адміністратор.

### Права доступу

| Дія | Хто може |
|---|---|
| `GET` для товарів, категорій і брендів | усі |
| `POST`, `PUT`, `PATCH` | авторизовані користувачі |
| `DELETE` | адміністратори (`is_staff`) |

Помилки доступу повертаються в загальному форматі:

* `401 Unauthorized` — `{"error": {"code": "unauthorized", "message": "Потрібна автентифікація. Передайте токен у заголовку Authorization: Bearer <access_token>."}}` (або повідомлення про недійсний чи прострочений токен).
* `403 Forbidden` — `{"error": {"code": "forbidden", "message": "Недостатньо прав для виконання цієї дії."}}`

Адміністратора створюють командою `python manage.py createsuperuser`.

## Як запустити проєкт

Адреси й порти:


1. Запустіть бекенд:

   ```bash
   python manage.py migrate
   python manage.py loaddata demo_data
   python manage.py runserver
   ```
2. Відкрийте в браузері `http://127.0.0.1:8000/api/v1`.


### Змінні середовища (`.env`)


| Змінна | Опис | Значення за замовчуванням |
|---|---|---|
| `SECRET_KEY` | Секретний ключ Django (**обов'язкова**) | немає |
| `DEBUG` | Режим налагодження (`True`/`False`) | `False` |
| `ALLOWED_HOSTS` | Дозволені хости через кому | `127.0.0.1,localhost` |
| `DB_ENGINE` | Бекенд бази даних Django | `django.db.backends.sqlite3` |
| `DB_NAME` | Назва БД або файл SQLite | `db.sqlite3` |
| `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Параметри підключення (для PostgreSQL/MySQL) | порожньо |
| `CORS_ALLOWED_ORIGINS` | Адреси фронтенду через кому | `http://localhost:5500,http://127.0.0.1:5500` |
| `ACCESS_TOKEN_LIFETIME_MINUTES` | Термін життя access-токена | `15` |
| `REFRESH_TOKEN_LIFETIME_DAYS` | Термін життя refresh-токена | `7` |
| `LOG_LEVEL` | Рівень логування: `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |
| `LOG_FILE` | Файл для логів (порожньо = лише консоль) | порожньо |

## Документація API (OpenAPI)
Після запуску сервера:

| Що | Адреса |
|---|---|
| **Swagger UI** (інтерактивна документація) | http://127.0.0.1:8000/api/docs/ |
| **ReDoc** | http://127.0.0.1:8000/api/redoc/ |
| **OpenAPI-схема** (YAML) | http://127.0.0.1:8000/api/schema/ |
| OpenAPI-схема (JSON) | http://127.0.0.1:8000/api/schema/?format=json |


**Як авторизуватися в Swagger UI:** виконайте `POST /api/v1/auth/login`, скопіюйте значення `access`, натисніть **Authorize** і вставте токен (без слова `Bearer`). Токен зберігається між оновленнями сторінки.

## Тестування

Тести написано з використанням [pytest](https://docs.pytest.org/) і `pytest-django`.

```bash
pip install pytest pytest-django
pytest
```

Налаштування pytest і coverage знаходяться в `pyproject.toml`. Додатково діють тести в стилі Django (`python manage.py test`), вони теж запускаються через `pytest`.

Що покрито:

* `tests/test_products_api.py`: основний ресурс «Товари»: `GET` (список, деталі, пошук, фільтри, сортування), `POST`, `PUT`, `PATCH`, `DELETE`; ролі (анонім, звичайний користувач, адміністратор); негативні сценарії (невалідні дані, неіснуючий об'єкт, 401, 403, 405, 415, зламаний JSON); справжні JWT-токени (логін, refresh, прострочений, недійсний, токен деактивованого користувача); перевірка логів.
* `tests/test_catalog_permissions.py`: права для категорій і брендів, дублікати (409), видалення об'єктів з товарами (409).
* `tests/test_openapi_docs.py`: схема генерується і містить описані ендпоінти, параметри та вимоги до токена; Swagger UI та ReDoc відкриваються.
* `accounts/tests.py`, `Rent/tests.py`: реєстрація, логін, профіль, список користувачів, CRUD.

## Логування

Налаштовано в `config/settings.py` (`LOGGING`): вивід у консоль, за потреби також у файл із ротацією (`LOG_FILE`). Рівень задається змінною `LOG_LEVEL`.

| Рівень | Що логується |
|---|---|
| `DEBUG` | Параметри фільтрації каталогу |
| `INFO` | Створення, оновлення й видалення товарів, категорій та брендів (id об'єкта й користувача); реєстрація й успішний вхід; помилки клієнта 400, 404, 405, 415 |
| `WARNING` | Відповіді 401 і 403 (спроби доступу без токена чи прав, невдалий вхід) та 409 (конфлікти даних) |
| `ERROR` | Необроблені винятки (500) зі стеком викликів |



