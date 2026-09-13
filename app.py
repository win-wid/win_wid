from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'win_wid_gizli_kalit'  # Sessiyanı idarə etmək üçün

# Sadə yaddaş (müvəqqəti olaraq siyahıda saxlanılır)
messages = []
users = {}  # {nickname: password}

# Giriş və Qeydiyyat Səhifəsinin HTML/CSS şablonu
INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Giriş</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; background-color: #f4f4f9; }
        .container { width: 300px; margin: 0 auto; padding: 20px; background: white; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        input { width: 90%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 4px; }
        button { padding: 10px 15px; margin: 5px; background: #007BFF; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .error { color: red; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>WİN_WİD'Ə XOŞ GƏLMİSİZ</h1>
        {% if error %}
            <p class="error">{{ error }}</p>
        {% endif %}
        <form method="POST">
            <input type="text" name="nickname" placeholder="Nik name" required>
            <input type="password" name="password" placeholder="Kod" required><br>
            <button type="submit" name="action" value="login">Daxil Ol</button>
            <button type="submit" name="action" value="register">Qeydiyyat Keç</button>
        </form>
    </div>
</body>
</html>
'''

# Mesajlaşma Panelinin HTML/CSS şablonu
CHAT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Çat Paneli</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f4f4f9; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #007BFF; color: white; padding: 10px 20px; border-radius: 5px; }
        .chat-box { background: white; height: 300px; border: 1px solid #ccc; border-radius: 5px; margin-top: 20px; padding: 10px; overflow-y: scroll; }
        .message-form { margin-top: 20px; display: flex; }
        input[type="text"] { flex: 1; padding: 10px; border: 1px solid #ccc; border-radius: 4px 0 0 4px; }
        button { padding: 10px 20px; background: #28a745; color: white; border: none; border-radius: 0 4px 4px 0; cursor: pointer; }
        a.logout { color: white; text-decoration: none; background: #dc3545; padding: 5px 10px; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="header">
        <h2>WİN_WİD'Ə XOŞ GƏLMİSİZ, {{ user }}!</h2>
        <a href="/logout" class="logout">Çıxış</a>
    </div>

    <div class="chat-box">
        {% for msg in messages %}
            <p>{{ msg }}</p>
        {% endfor %}
    </div>

    <form method="POST" class="message-form">
        <input type="text" name="message" placeholder="Mesajınızı yazın..." autocomplete="off" required>
        <button type="submit">Göndər</button>
    </form>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    if request.method == 'POST':
        action = request.form.get('action')
        nickname = request.form.get('nickname').strip()
        password = request.form.get('password').strip()
        
        if not nickname or not password:
            error = "Xanalar boş ola bilməz!"
        elif action == 'register':
            if nickname in users:
                error = "Bu nikname artıq istifadədədir!"
            else:
                users[nickname] = password
                session['user'] = nickname
                return redirect(url_for('chat'))
        elif action == 'login':
            if nickname in users and users[nickname] == password:
                session['user'] = nickname
                return redirect(url_for('chat'))
            else:
                error = "Yanlış nikname və ya kod!"
                
    return render_template_string(INDEX_TEMPLATE, error=error)

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'user' not in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        msg = request.form.get('message').strip()
        if msg:
            full_msg = f"{session['user']}: {msg}"
            messages.append(full_msg)
        return redirect(url_for('chat'))
        
    return render_template_string(CHAT_TEMPLATE, user=session['user'], messages=messages)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
