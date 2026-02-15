from flask import Flask, request, redirect, jsonify, render_template_string
import string
import random
import os
import psycopg2
from psycopg2.extras import DictCursor

app = Flask(__name__)

# Функция для подключения к БД
def get_db_connection():
    database_url = os.getenv('DATABASE_URL', 'postgresql://admin:admin123@localhost:5432/urlshortener')
    conn = psycopg2.connect(database_url)
    return conn

# Функция для создания таблицы (если её нет)
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS urls (
            id SERIAL PRIMARY KEY,
            short_code VARCHAR(10) UNIQUE NOT NULL,
            original_url TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()
    print("База данных инициализирована")

# Инициализируем БД при запуске
init_db()

# Функция для генерации случайного кода
def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    short_code = ''.join(random.choice(chars) for _ in range(length))
    return short_code

# Домашняя страница
@app.route('/')
def home():
    # Получаем последние 5 ссылок из БД
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("SELECT short_code, original_url FROM urls ORDER BY created_at DESC LIMIT 5")
    recent_links = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template_string('''
        <h1>Сокращатель ссылок</h1>
        <form action="/shorten" method="post">
            <input type="url" name="url" placeholder="Введите длинный URL" required size="50">
            <button type="submit">Сократить</button>
        </form>
        <hr>
        <h3>Последние созданные ссылки:</h3>
        <ul>
        {% for link in links %}
            <li><a href="{{ link.short_url }}" target="_blank">{{ link.short_url }}</a> -> {{ link.original_url }}</li>
        {% endfor %}
        </ul>
    ''', links=[{
        'short_url': request.host_url + link['short_code'],
        'original_url': link['original_url']
    } for link in recent_links])

# Эндпоинт для создания короткой ссылки
@app.route('/shorten', methods=['POST'])
def shorten():
    original_url = request.form.get('url')
    
    if not original_url:
        return jsonify({"error": "URL не предоставлен"}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Генерируем уникальный код
    short_code = generate_short_code()
    
    # Проверяем, не занят ли код
    cur.execute("SELECT short_code FROM urls WHERE short_code = %s", (short_code,))
    while cur.fetchone():
        short_code = generate_short_code()
        cur.execute("SELECT short_code FROM urls WHERE short_code = %s", (short_code,))
    
    # Сохраняем в БД
    cur.execute(
        "INSERT INTO urls (short_code, original_url) VALUES (%s, %s)",
        (short_code, original_url)
    )
    conn.commit()
    
    cur.close()
    conn.close()
    
    short_url = request.host_url + short_code
    
    return jsonify({
        "original_url": original_url,
        "short_url": short_url,
        "short_code": short_code
    })

# Эндпоинт для редиректа
@app.route('/<short_code>')
def redirect_to_original(short_code):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    
    cur.execute("SELECT original_url FROM urls WHERE short_code = %s", (short_code,))
    result = cur.fetchone()
    
    cur.close()
    conn.close()
    
    if result:
        return redirect(result['original_url'])
    else:
        return jsonify({"error": "Короткая ссылка не найдена"}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)