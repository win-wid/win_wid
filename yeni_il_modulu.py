# yeni_il_modulu.py
# Dekabr və Yeni il bayramı üçün xüsusi əlavələr (Əsas app.py-ə toxunmadan işləyir)

YENI_IL_BANNERI = '''
<!-- Yeni il xüsusi reklam lenti və ya elanı -->
<div style="width: 100%; max-width: 700px; margin: 0 auto 15px auto; background: linear-gradient(135deg, #dc2626, #16a34a); border: 2px solid #fbbf24; border-radius: 14px; padding: 12px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.5);">
    <a href="#" style="text-decoration: none; color: #ffffff; font-size: 14px; font-weight: 700; display: block;">
        🎄✨ WİN_WİD ailəsi olaraq Yeni iliniz mübarək! 2026-cı ilə ən çox Won ilə girən siz olun! 🎅🎁
    </a>
</div>
'''

QAR_VE_BAYRAM_SCRIPTI = '''
<!-- Qar yağma effekti və Yeni il abu-havası üçün script -->
<style>
    /* Qar dənəciklərinin ümumi görünüşü */
    .snowflake {
        position: fixed;
        top: -10px;
        z-index: 999999;
        user-select: none;
        pointer-events: none;
        color: #ffffff;
        font-size: 1.2em;
        animation: fall linear infinite;
    }
    @keyframes fall {
        0% { transform: translateY(-10vh) translateX(0); opacity: 1; }
        100% { transform: translateY(105vh) translateX(20px); opacity: 0.3; }
    }
</style>
<script>
    // Avtomatik səhifəyə qar dənəcikləri əlavə edən mexanizm
    document.addEventListener("DOMContentLoaded", function() {
        const snowflakeCount = 25;
        for (let i = 0; i < snowflakeCount; i++) {
            let sf = document.createElement('div');
            sf.className = 'snowflake';
            sf.innerHTML = '❄';
            sf.style.left = Math.random() * 100 + 'vw';
            sf.style.animationDuration = (Math.random() * 3 + 2) + 's';
            sf.style.animationDelay = Math.random() * 5 + 's';
            sf.style.fontSize = (Math.random() * 10 + 10) + 'px';
            document.body.appendChild(sf);
        }
    });
</script>
'''

# Yeni ilə özəl əlavə hədiyyələr / stikerlər siyahısı
YENI_IL_HEDIYYELERI = ['🎅', '🎄', '⛄', '🎁', '🍾', '❄️', '⭐', '🌟', '🥶']
