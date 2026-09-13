from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'win_wid_gizli_kalit'

# Bazanın yaradılması və cədvəllərin qurulması
def init_db():
    conn = sqlite3.connect('win_wid.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            nickname TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Giriş və Qeydiyyat Səhifəsi
INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Giriş</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            background-color: #1e3a8a; 
            color: #ffffff; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            height: 100vh; 
            margin: 0; 
        }
        .container { 
            width: 320px; 
            padding: 30px; 
            background: #172554; 
            border-radius: 12px; 
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3); 
            text-align: center; 
            border: 1px solid #3b82f6; 
        }
        h1 { 
            font-size: 20px; 
            margin-bottom: 20px; 
            color: #ffffff; 
        }
        input { 
            width: 100%; 
            padding: 12px; 
            margin: 10px 0; 
            border: 1px solid #3b82f6; 
            border-radius: 6px; 
            background: #1e3a8a; 
            color: #ffffff; 
            box-sizing: border-box; 
        }
        input::placeholder { color: #93c5fd; }
        button { 
            width: 100%; 
            padding: 12px; 
            margin: 8px 0; 
            background: #2563eb; 
            color: white; 
            border: none; 
            border-radius: 6px; 
            cursor: pointer; 
            font-weight: bold; 
        }
        button:hover { background: #1d4ed8; }
        .error { color: #f87171; font-size: 14px; margin-bottom: 10px; }
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
            <input type="password" name="password" placeholder="Kod" required>
            <button type="submit" name="action" value="login">Daxil Ol</button>
            <button type="submit" name="action" value="register">Qeydiyyat Keç</button>
        </form>
    </div>
</body>
</html>
'''

# Əsas Menyu və Narıncı Çərçivə daxilində bölmələr
MENU_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Menyu</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 15px; 
            background: #1e3a8a; 
            color: #ffffff; 
            display: flex; 
            flex-direction: column; 
            height: 100vh; 
            box-sizing: border-box; 
        }
        .header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            background: #172554; 
            color: white; 
            padding: 12px 20px; 
            border-radius: 8px; 
            border: 1px solid #3b82f6; 
            margin-bottom: 15px;
        }
        .header h2 {
            font-size: 16px;
            margin: 0;
        }
        /* Narıncı Çərçivə - Menyu bölmələri */
        .menu-box { 
            background: #172554; 
            border: 2px solid #f97316; 
            border-radius: 8px; 
            padding: 20px; 
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
        }
        .menu-btn {
            background: #1e3a8a;
            color: white;
            border: 1px solid #3b82f6;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            text-decoration: none;
            font-weight: bold;
            font-size: 15px;
            transition: 0.2s;
        }
        .menu-btn:hover {
            background: #2563eb;
            border-color: #f97316;
        }
        a.logout { 
            color: white; 
            text-decoration: none; 
            background: #dc2626; 
            padding: 6px 12px; 
            border-radius: 6px; 
            font-size: 13px; 
        }
        a.logout:hover { background: #b91c1c; }
    </style>
</head>
<body>
    <div class="header">
        <h2>WİN_WİD'Ə XOŞ GƏLMİSİZ, {{ user }}!</h2>
        <a href="/logout" class="logout">Çıxış</a>
    </div>

    <!-- Narıncı Çərçivə və 6 Bölmə -->
    <div class="menu-box">
        <a href="/chat" class="menu-btn">1. ÇAT</a>
        <a href="/sekil" class="menu-btn">2. ŞƏKİL</a>
        <a href="/vidyo" class="menu-btn">3. VİDYO</a>
        <a href="/oyun" class="menu-btn">4. OYUN</a>
        <a href="/magaza" class="menu-btn">5. MAGAZA</a>
        <a href="/profil" class="menu-btn">6. PROFİL</a>
    </div>
</body>
</html>
'''

# Çat Səhifəsi
CHAT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Çat</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 15px; 
            background: #1e3a8a; 
            color: #ffffff; 
            display: flex; 
            flex-direction: column; 
            height: 100vh; 
            box-sizing: border-box; 
        }
        .header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            background: #172554; 
            color: white; 
            padding: 12px 20px; 
            border-radius: 8px; 
            border: 1px solid #3b82f6; 
            margin-bottom: 15px;
        }
        .chat-box { 
            background: #172554; 
            flex: 1; 
            border: 2px solid #f97316; 
            border-radius: 8px; 
            padding: 15px; 
            overflow-y: auto; 
            color: #ffffff; 
            margin-bottom: 15px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .chat-box p {
            background: #1e3a8a;
            padding: 10px 14px;
            border-radius: 6px;
            margin: 0;
            border-left: 4px solid #3b82f6;
            word-break: break-all;
        }
        .message-form { 
            display: flex; 
            gap: 10px; 
            background: #172554;
            padding: 12px;
            border: 2px solid #f97316;
            border-radius: 8px;
        }
        input[type="text"] { 
            flex: 1; 
            padding: 12px; 
            border: 1px solid #3b82f6; 
            border-radius: 6px; 
            background: #1e3a8a; 
            color: #ffffff; 
            font-size: 14px;
        }
        button[type="submit"] { 
            padding: 12px 22px; 
            background: #22c55e; 
            color: white; 
            border: none; 
            border-radius: 6px; 
            cursor: pointer; 
            font-weight: bold; 
        }
        a.back { 
            color: white; 
            text-decoration: none; 
            background: #2563eb; 
            padding: 6px 12px; 
            border-radius: 6px; 
            font-size: 13px; 
        }
    </style>
</head>
<body>
    <div class="header">
        <h2>Çat Bölməsi</h2>
        <a href="/menu" class="back">Geri Qayıt</a>
    </div>

    <div class="chat-box">
        {% if messages %}
            {% for msg in messages %}
                <p>{{ msg }}</p>
            {% endfor %}
        {% else %}
            <p style="color: #93c5fd; text-align: center; border-left: none; background: transparent;">Hələ ki mesaj yoxdur. İlk mesajı sən yaz!</p>
        {% endif %}
    </div>

    <form method="POST" class="message-form">
        <input type="text" name="message" placeholder="Mesajınızı yazın..." autocomplete="off" required>
        <button type="submit">Göndər</button>
    </form>
</body>
</html>
'''

# Digər səhifələr üçün ümumi şablon
SUB_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - {{ title }}</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 15px; 
            background: #1e3a8a; 
            color: #ffffff; 
            display: flex; 
            flex-direction: column; 
            height: 100vh; 
            box-sizing: border-box; 
        }
        .header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            background: #172554; 
            color: white; 
            padding: 12px 20px; 
            border-radius: 8px; 
            border: 1px solid #3b82f6; 
            margin-bottom: 15px;
        }
        .content-box { 
            background: #172554; 
            flex: 1; 
            border: 2px solid #f97316; 
            border-radius: 8px; 
            padding: 20px; 
            text-align: center;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 18px;
            color: #93c5fd;
        }
        a.back { 
            color: white; 
            text-decoration: none; 
            background: #2563eb; 
            padding: 6px 12px; 
            border-radius: 6px; 
            font-size: 13px; 
        }
    </style>
</head>
<body>
    <div class="header">
        <h2>{{ title }} Bölməsi</h2>
        <a href="/menu" class="back">Geri Qayıt</a>
    </div>
    <div class="content-box">
        <p>{{ title }} bölməsi tezliklə aktiv olacaq!</p>
    </div>
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
        else:
            conn = sqlite3.connect('win_wid.db')
            cursor = conn.cursor()
            
            if action == 'register':
                cursor.execute("SELECT * FROM users WHERE nickname = ?", (nickname,))
                if cursor.fetchone():
                    error = "Bu nikname artıq istifadədədir!"
                else:
                    cursor.execute("INSERT INTO users (nickname, password) VALUES (?, ?)", (nickname, password))
                    conn.commit()
                    session['user'] = nickname
                    conn.close()
                    return redirect(url_for('menu'))
                    
            elif action == 'login':
                cursor.execute("SELECT password FROM users WHERE nickname = ?", (nickname,))
                row = cursor.fetchone()
                if row and row[0] == password:
                    session['user'] = nickname
                    conn.close()
                    return redirect(url_for('menu'))
                else:
                    error = "Yanlış nikname və ya kod!"
            conn.close()
                
    return render_template_string(INDEX_TEMPLATE, error=error)

@app.route('/menu')
def menu():
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template_string(MENU_TEMPLATE, user=session['user'])

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'user' not in session:
        return redirect(url_for('index'))
        
    conn = sqlite3.connect('win_wid.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        msg = request.form.get('message').strip()
        if msg:
            full_msg = f"{session['user']}: {msg}"
            cursor.execute("INSERT INTO messages (content) VALUES (?)", (full_msg,))
            conn.commit()
        conn.close()
        return redirect(url_for('chat'))
        
    cursor.execute("SELECT content FROM messages")
    messages = [row[0] for row in cursor.fetchall()]
    conn.close()
        
    return render_template_string(CHAT_TEMPLATE, messages=messages)

@app.route('/sekil')
def sekil():
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template_string(SUB_TEMPLATE, title="ŞƏKİL")

@app.route('/vidyo')
def vidyo():
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template_string(SUB_TEMPLATE, title="VİDYO")

@app.route('/oyun')
def oyun():
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template_string(SUB_TEMPLATE, title="OYUN")

@app.route('/magaza')
def magaza():
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template_string(SUB_TEMPLATE, title="MAGAZA")

@app.route('/profil')
def profil():
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template_string(SUB_TEMPLATE, title="PROFİL")

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
