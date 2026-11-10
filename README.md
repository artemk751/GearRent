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

