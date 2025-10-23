# Test ortamını hazırla
$Env:PYTHONPATH = "."
$Env:TESTING = "True"
$Env:ENVIRONMENT = "test"
$Env:DATABASE_URL = "postgresql+asyncpg://postgres:Fer.153624987@localhost:5432/ceng_project_test"
$Env:SECRET_KEY = "test_secret_key_for_testing_only"

# Test veritabanı dosyasını temizle (eğer varsa)
if (Test-Path -Path "test.db") {
    Remove-Item -Path "test.db" -Force
}

# Testleri çalıştır
Write-Host "Redis testleri çalıştırılıyor..."
python -m pytest tests/test_redis.py -v --asyncio-mode=auto

# Test sonrası temizlik
if (Test-Path -Path "test.db") {
    Remove-Item -Path "test.db" -Force
} 