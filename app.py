from flask import Flask, request, redirect, jsonify, render_template_string
import string
import random

app = Flask(__name__)

# Временное хранилище ссылок 
# Формат: {короткий_код: длинный_url}
url_mapping = {}

# Функция для генерации случайного кода длиной 6 символов
def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits  # a-z, A-Z, 0-9
    short_code = ''.join(random.choice(chars) for _ in range(length))
    return short_code

# Домашняя страница с простой формой
@app.route('/')
def home():
    return render_template_string('''
        <h1>Сокращатель ссылок</h1>
        <form action="/shorten" method="post">
            <input type="url" name="url" placeholder="Введите длинный URL" required size="50">
            <button type="submit">Сократить</button>
        </form>
    ''')

# Эндпоинт для создания короткой ссылки
@app.route('/shorten', methods=['POST'])
def shorten():
    original_url = request.form.get('url')
    
    if not original_url:
        return jsonify({"error": "URL не предоставлен"}), 400
    
    # Генерируем уникальный код (проверяем, что такого ещё нет)
    short_code = generate_short_code()
    while short_code in url_mapping:
        short_code = generate_short_code()
    
    # Сохраняем в наше временное хранилище
    url_mapping[short_code] = original_url
    
    # Формируем короткую ссылку
    short_url = request.host_url + short_code
    
    return jsonify({
        "original_url": original_url,
        "short_url": short_url,
        "short_code": short_code
    })

# Эндпоинт для редиректа
@app.route('/<short_code>')
def redirect_to_original(short_code):
    # Ищем оригинальный URL по коду
    original_url = url_mapping.get(short_code)
    
    if original_url:
        return redirect(original_url)
    else:
        return jsonify({"error": "Короткая ссылка не найдена"}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)