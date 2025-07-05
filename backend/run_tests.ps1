# Test bağımlılıklarını yükle
pip install -r requirements-test.txt

# Testleri çalıştır
pytest --verbose --cov=app --cov-report=term-missing --cov-report=html

# Test sonuçlarını göster
Write-Host "`nTest coverage report has been generated in htmlcov/index.html" 