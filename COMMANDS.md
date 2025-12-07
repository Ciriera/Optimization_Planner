# ============================================
# ÖNEMLİ: setupProxy.js dosyası oluşturuldu
# Frontend'i YENİDEN BAŞLATIN (Ctrl+C sonra tekrar başlatın)
# ============================================

# Frontend başlatma (PowerShell için execution policy sorunu çözümü ile)
# Yöntem 1: Execution policy'yi geçici olarak bypass et (ÖNERİLEN)
cd frontend; $env:DANGEROUSLY_DISABLE_HOST_CHECK="true"; $env:PORT="3000"; powershell -ExecutionPolicy Bypass -Command "npm start"

# Yöntem 2: Execution policy'yi ayarla (sadece ilk defa gerekli, kalıcı çözüm)
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# Sonra normal komutu kullan:
# cd frontend; $env:DANGEROUSLY_DISABLE_HOST_CHECK="true"; $env:PORT="3000"; npm start

# Yöntem 3: npm.cmd kullan (execution policy sorunu olmaz)
# cd frontend; $env:DANGEROUSLY_DISABLE_HOST_CHECK="true"; $env:PORT="3000"; npm.cmd start

# Backend başlatma (0.0.0.0 tüm network interface'lerinden erişime izin verir)
# ÖNEMLİ: -u flag'i Python'un unbuffered modunu aktif eder (log'lar hemen görünür)
# --log-level debug ile tüm log'lar görünür
# Python 3.9 path: C:\Users\cavul\AppData\Local\Programs\Python\Python39
# ÖNEMLİ: Komutu proje root dizininden (Optimization_Planner-main) çalıştırın!
&"C:\Users\cavul\AppData\Local\Programs\Python\Python39\python.exe" -u -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug

# Alternatif 1: Sadece localhost üzerinden (bazı sistemlerde daha güvenli)
# &"C:\Users\cavul\AppData\Local\Programs\Python\Python39\python.exe" -u -m uvicorn app.main:app --reload --host localhost --port 8000 --log-level debug

# Alternatif 2: Eğer Python PATH'e eklenmişse (python komutu çalışıyorsa):
# python -u -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug

# NOT: Python 3.9 tam path'i kullanılıyor. Eğer farklı bir Python versiyonu kullanıyorsanız path'i güncelleyin.

# ============================================
# SORUN GİDERME:
# 1. Backend çalışıyor mu? http://localhost:8000/docs kontrol edin
# 2. Frontend proxy log'larını browser console'da kontrol edin
# 3. Network tab'da API isteklerinin nereye gittiğini kontrol edin
# 4. Her iki uygulamayı da yeniden başlatın
# ============================================