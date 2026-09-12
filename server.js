// WIN_WID - Backend Server Kodu
const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const mongoose = require('mongoose');
const multer = require('multer');
const badWordsFilter = require('bad-words');
const path = require('path');

const app = express();
const server = http.createServer(app);
const io = socketIo(server);

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// 1. VERİLƏNLƏR BAZASI MODELLƏRİ
const UserSchema = new mongoose.Schema({
    username: { type: String, unique: true, required: true },
    password: { type: String, required: true },
    profilePic: { type: String, default: 'default.jpg' },
    followers: [{ type: mongoose.Schema.Types.ObjectId, ref: 'User' }],
    following: [{ type: mongoose.Schema.Types.ObjectId, ref: 'User' }],
    isBanned: { type: Boolean, default: false }
});
const User = mongoose.model('User', UserSchema);

const PostSchema = new mongoose.Schema({
    userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
    mediaUrl: String,
    mediaType: String,
    createdAt: { type: Date, default: Date.now }
});
const Post = mongoose.model('Post', PostSchema);

// 2. WIN_WID TƏHLÜKƏSİZLİK SİSTEMİ (18+ FİLTR VƏ BLOKLAMA)
const filter = new badWordsFilter();

async function checkTextSafety(userId, text) {
    if (filter.isProfane(text)) {
        await User.findByIdAndUpdate(userId, { isBanned: true });
        return false;
    }
    return true;
}

async function checkMediaSafety(userId, fileBuffer) {
    let isNsfw = false; 
    if (isNsfw) {
        await User.findByIdAndUpdate(userId, { isBanned: true });
        return false;
    }
    return true;
}

// 3. İSTİFADƏÇİ VƏ PROFİL SİSTEMİ (QEYDİYYAT VƏ GİRİŞ)
app.post('/api/register', async (req, res) => {
    const { username, password } = req.body;
    try {
        const user = new User({ username, password });
        await user.save();
        res.json({ success: true, message: "Hesab yaradıldı! İndi giriş edə bilərsiniz." });
    } catch (err) {
        res.status(400).json({ error: "İstifadəçi adı artıq mövcuddur!" });
    }
});

app.post('/api/login', async (req, res) => {
    const { username, password } = req.body;
    try {
        const user = await User.findOne({ username, password });
        if (!user) {
            return res.status(400).json({ error: "İstifadəçi adı və ya şifrə yanlışdır!" });
        }
        if (user.isBanned) {
            return res.status(403).json({ error: "Hesabınız 18+ qayda pozuntusuna görə BLOKLANIB!" });
        }
        res.json({ success: true, user: { id: user._id, username: user.username } });
    } catch (err) {
        res.status(500).json({ error: "Giriş zamanı xəta baş verdi!" });
    }
});

app.post('/api/follow', async (req, res) => {
    const { currentUserId, targetUserId } = req.body;
    await User.findByIdAndUpdate(currentUserId, { $addToSet: { following: targetUserId } });
    await User.findByIdAndUpdate(targetUserId, { $addToSet: { followers: currentUserId } });
    res.json({ success: true, message: "Uğurla izləyirsiniz!" });
});

// 4. ŞƏKİL VƏ VİDEO PAYLAŞIMI
const upload = multer({ dest: 'uploads/' });

app.post('/api/upload', upload.single('media'), async (req, res) => {
    const { userId, mediaType } = req.body;
    const user = await User.findById(userId);
    if (user.isBanned) {
        return res.status(403).json({ error: "Hesabınız 18+ qayda pozuntusuna görə BLOKLANIB!" });
    }

    const isSafe = await checkMediaSafety(userId, req.file);
    if (!isSafe) {
        return res.status(400).json({ error: "18+ Məzmun aşkar edildi! Hesabınız bloklandı." });
    }

    const newPost = new Post({ userId, mediaUrl: req.file.path, mediaType });
    await newPost.save();
    res.json({ success: true, post: newPost });
});

// 5. İLK AÇILIŞ SƏHİFƏSİ (MƏRKƏZLƏŞDİRİLMİŞ QEYDİYYAT İNTERFEYSİ)
app.get('/', (req, res) => {
    res.send(`
    <!DOCTYPE html>
    <html lang="az">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Win_Wid Social Platform</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
                background-color: #121212; 
                color: #ffffff; 
                display: flex; 
                flex-direction: column;
                justify-content: center; 
                align-items: center; 
                min-height: 100vh; 
                padding: 20px;
            }
            .header-title {
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 25px;
                text-align: center;
            }
            .auth-card { 
                background: #1e1e1e; 
                padding: 24px; 
                border-radius: 12px; 
                width: 100%;
                max-width: 380px; 
                box-shadow: 0 8px 24px rgba(0,0,0,0.6); 
                border: 1px solid #2a2a2a;
            }
            .auth-card h2 { 
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 20px; 
                color: #ffffff; 
            }
            input { 
                width: 100%; 
                padding: 14px 16px; 
                margin-bottom: 12px; 
                border-radius: 8px; 
                border: 1px solid #333333; 
                background: #ffffff; 
                color: #000000; 
                font-size: 15px;
                outline: none;
            }
            input::placeholder { color: #777777; }
            button.main-btn { 
                width: 100%; 
                padding: 14px; 
                background: #0084c7; 
                border: none; 
                color: #ffffff; 
                font-size: 15px;
                font-weight: 600; 
                border-radius: 8px; 
                cursor: pointer; 
                margin-top: 5px; 
                transition: background 0.2s;
            }
            button.main-btn:hover { background: #0070ab; }
            .toggle-btn { 
                background: transparent; 
                color: #0084c7; 
                border: none; 
                margin-top: 18px; 
                font-size: 14px;
                cursor: pointer; 
                width: 100%;
                text-align: center;
            }
            #error-msg { color: #ff5252; font-size: 14px; margin-top: 12px; text-align: center; }
            #main-app { display: none; text-align: center; }
        </style>
    </head>
    <body>

        <div class="header-title">Win_Wid Social Platform</div>

        <!-- YALNIZ MƏRKƏZƏ YERLƏŞDİRİLMİŞ QEYDİYYAT/GİRİŞ KART-I -->
        <div id="auth-container" class="auth-card">
            <h2 id="form-title">Giriş / Qeydiyyat</h2>
            
            <input type="text" id="username" placeholder="İstifadəçi adı" required>
            <input type="password" id="password" placeholder="Şifrə" required>
            
            <button class="main-btn" id="auth-btn" onclick="handleAuth()">Qeydiyyatdan Keç</button>
            <div id="error-msg"></div>
            
            <button class="toggle-btn" onclick="toggleMode()" id="toggle-btn">Hesabınız var? Giriş edin</button>
        </div>

        <div id="main-app">
            <h2 style="color: #0084c7; margin-bottom: 10px;">Win_Wid Platformasına Xoş Gəldiniz!</h2>
            <p id="user-welcome"></p>
        </div>

        <script>
            let isLoginMode = false;

            function toggleMode() {
                isLoginMode = !isLoginMode;
                document.getElementById('form-title').innerText = isLoginMode ? "Giriş" : "Giriş / Qeydiyyat";
                document.getElementById('auth-btn').innerText = isLoginMode ? "Giriş Et" : "Qeydiyyatdan Keç";
                document.getElementById('toggle-btn').innerText = isLoginMode ? "Hesabınız yoxdur? Qeydiyyatdan keçin" : "Hesabınız var? Giriş edin";
                document.getElementById('error-msg').innerText = "";
            }

            async function handleAuth() {
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                const endpoint = isLoginMode ? '/api/login' : '/api/register';

                if(!username || !password) {
                    document.getElementById('error-msg').innerText = "Zəhmət olmasa xanaları doldurun!";
                    return;
                }

                try {
                    const res = await fetch(endpoint, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username, password })
                    });
                    const data = await res.json();

                    if(res.ok) {
                        if(isLoginMode) {
                            document.getElementById('auth-container').style.display = 'none';
                            document.getElementById('main-app').style.display = 'block';
                            document.getElementById('user-welcome').innerText = "Xoş gəldin, " + data.user.username + "!";
                        } else {
                            alert(data.message);
                            toggleMode();
                        }
                    } else {
                        document.getElementById('error-msg').innerText = data.error;
                    }
                } catch(err) {
                    document.getElementById('error-msg').innerText = "Xəta baş verdi, yenidən cəhd edin.";
                }
            }
        </script>
    </body>
    </html>
    `);
});

// 6. SOCKET.IO SİSTEMİ
io.on('connection', (socket) => {
    socket.on('send_global_message', async (data) => {
        const { userId, message } = data;
        const isSafe = await checkTextSafety(userId, message);
        if (!isSafe) {
            socket.emit('error_message', '18+ kontentə görə hesabınız BLOKLANDI!');
            return;
        }
        io.emit('receive_global_message', { userId, message });
    });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log(`Win_Wid serveri ${PORT} portunda işləyir...`);
});
