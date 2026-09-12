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

// 5. İLK AÇILIŞ SƏHİFƏSİ (QEYDİYYAT/GİRİŞ İNTERFEYSİ)
app.get('/', (req, res) => {
    res.send(`
    <!DOCTYPE html>
    <html lang="az">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Win_Wid - Xoş Gəlmisiniz</title>
        <style>
            body { font-family: Arial, sans-serif; background: #121212; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .auth-card { background: #1e1e1e; padding: 30px; border-radius: 12px; width: 320px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); text-align: center; }
            h2 { margin-bottom: 20px; color: #bb86fc; }
            input { width: 100%; padding: 12px; margin: 8px 0; border-radius: 6px; border: 1px solid #333; background: #2b2b2b; color: #fff; box-sizing: border-box; }
            button { width: 100%; padding: 12px; background: #bb86fc; border: none; color: #000; font-weight: bold; border-radius: 6px; cursor: pointer; margin-top: 10px; }
            button:hover { background: #9955e8; }
            .toggle-btn { background: transparent; color: #03dac6; border: none; margin-top: 15px; text-decoration: underline; cursor: pointer; }
            .hidden { display: none; }
            #main-app { display: none; text-align: center; }
        </style>
    </head>
    <body>

        <!-- QEYDİYYAT VƏ GİRİŞ İNTERFEYSİ -->
        <div id="auth-container" class="auth-card">
            <h2 id="form-title">Win_Wid Qeydiyyat</h2>
            
            <input type="text" id="username" placeholder="İstifadəçi adı" required>
            <input type="password" id="password" placeholder="Şifrə" required>
            
            <button id="auth-btn" onclick="handleAuth()">Qeydiyyatdan Keç</button>
            <p id="error-msg" style="color: #cf6679; font-size: 14px; margin-top: 10px;"></p>
            
            <button class="toggle-btn" onclick="toggleMode()" id="toggle-btn">Hesabınız var? Giriş edin</button>
        </div>

        <!-- UĞURLU GİRİŞDƏN SONRA AÇILAN ƏSAS SƏHİFƏ -->
        <div id="main-app">
            <h1 style="color: #03dac6;">Win_Wid Şəbəkəsinə Xoş Gəldiniz!</h1>
            <p id="user-welcome"></p>
        </div>

        <script>
            let isLoginMode = false;

            function toggleMode() {
                isLoginMode = !isLoginMode;
                document.getElementById('form-title').innerText = isLoginMode ? "Win_Wid Giriş" : "Win_Wid Qeydiyyat";
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

// 6. REAL-VAXTLI ÇAT VƏ ŞƏXSİ MESAJLAŞMA (DM)
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

    socket.on('send_private_message', async (data) => {
        const { senderId, receiverId, message } = data;
        const isSafe = await checkTextSafety(senderId, message);
        if (!isSafe) {
            socket.emit('error_message', '18+ kontentə görə hesabınız BLOKLANDI!');
            return;
        }
        socket.to(receiverId).emit('receive_private_message', { senderId, message });
    });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log(`Win_Wid serveri ${PORT} portunda işləyir...`);
});
