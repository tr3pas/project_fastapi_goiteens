# RepairHub — Service Desk FastAPI Application

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green?logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue?logo=postgresql)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7+-red?logo=redis)](https://redis.io/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-orange?logo=python)](https://www.sqlalchemy.org/)
[![JWT](https://img.shields.io/badge/Auth-JWT-black?logo=jsonwebtokens)](https://jwt.io/)

---

## Опис проєкту

**RepairHub** — веб-додаток (Service Desk) для управління заявками на ремонт техніки.  
Користувачі можуть створювати та відстежувати заявки, а адміністратори — керувати ними, змінювати статуси та спілкуватися з клієнтами.

Проєкт створений як навчальний, але має повноцінну архітектуру реального backend-сервісу.

---

## Функціонал

### Для користувачів
- Реєстрація та авторизація (JWT)
- Створення заявок на ремонт з описом та фото
- Перегляд статусу заявок
- Редагування та видалення заявок
- Вказування бажаного терміну виконання

### Для адміністраторів
- Перегляд усіх заявок з фільтрацією
- Прийняття заявок в роботу
- Зміна статусів заявок
- Додавання коментарів
- Призначення заявок собі

---

## Технологічний стек

- FastAPI
- Python 3.11+
- PostgreSQL
- SQLAlchemy (async)
- Alembic
- Redis
- JWT
- Werkzeug
- Jinja2
- HTML, Bootstrap 5

---

## Встановлення та запуск

### Вимоги
- Python 3.11+
- PostgreSQL 12+
- Redis
- pip

---

### Крок 1: Клонування репозиторію
```bash
git clone https://github.com/your-username/repairhub.git
cd repairhub
```

### Крок 2: Створення віртуального середовища
```
python -m venv .venv
source .venv/bin/activate      # Linux / MacOS
.venv\Scripts\activate         # Windows
```

### Крок 3: Встановлення залежностей
```
pip install -r requirements.txt
```

### Крок 4: Налаштування середовища
Створіть файл `.env` у корені проєкту:

```
DATABASE_NAME=alembic_async_db
DB_USER=postgres
DB_PASSWORD=your_password

SECRET_KEY=your_secret_key
```

### Крок 5: Створення бази даних
```
createdb repairhub_db
```
### Крок 6: Міграції
```
alembic upgrade head
```

### Крок 7: Створення тестових даних
```
python mockdata.py
```

##  стек технологій:

 - Fastapi
 - SQLAlchemy
 - pydantic
 - JWT
 - Redis
 - Alembic
 - postgresql
 


