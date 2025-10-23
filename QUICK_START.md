# ⚡ Quick Start Guide

## 🚀 Hızlı Başlangıç (5 Dakika)

### 1️⃣ .env Dosyası Oluştur
```powershell
# env.example'dan kopyala
cp env.example .env
```

**`.env` içeriğini düzenle**:
```env
DATABASE_URL=postgresql://postgres:Fer.153624987@localhost:5432/ceng_project
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=Fer.153624987
POSTGRES_DB=ceng_project
SECRET_KEY=your-secret-key-change-in-production
```

### 2️⃣ PostgreSQL'i Başlat
```powershell
# Windows
net start postgresql-x64-13

# Linux/Mac
sudo systemctl start postgresql
```

### 3️⃣ Database Oluştur
```powershell
psql -U postgres
CREATE DATABASE ceng_project;
\q
```

### 4️⃣ Dependencies Kur
```powershell
# Backend
pip install -r requirements.txt

# Frontend
cd frontend ; npm install ; cd ..
```

### 5️⃣ Migration Çalıştır
```powershell
alembic upgrade head
```

### 6️⃣ Test Et
```powershell
python test_synchronization.py
```

### 7️⃣ Başlat
```powershell
# Backend (Terminal 1)
uvicorn app.main:app --reload

# Frontend (Terminal 2)
cd frontend ; npm start
```

## ✅ Başarı Kontrolleri

- [ ] PostgreSQL çalışıyor: http://localhost:5432
- [ ] Backend çalışıyor: http://localhost:8000/docs
- [ ] Frontend çalışıyor: http://localhost:3000
- [ ] Test script başarılı: `python test_synchronization.py`

## 🎯 Sonraki Adımlar

1. Admin kullanıcısı oluştur: `POST http://localhost:8000/api/v1/auth/create-admin`
2. Login ol: Frontend'den giriş yap
3. Test data ekle: Dashboard'dan veri ekle

## 📝 Notlar

- **Backend Port**: 8000
- **Frontend Port**: 3000
- **Database Port**: 5432
- **API Docs**: http://localhost:8000/docs

---

Daha detaylı bilgi için `SETUP_GUIDE.md` dosyasına bakın.

