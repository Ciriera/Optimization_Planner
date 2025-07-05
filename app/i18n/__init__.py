"""
Çoklu dil desteği (i18n) modülü.
Bu modül, uygulamanın farklı dillerde kullanılabilmesini sağlar.
"""

import os
from typing import Optional, Dict, Any

# Ayarları alma
try:
    from app.core.config import settings
    DEFAULT_LANGUAGE = settings.DEFAULT_LANGUAGE
    SUPPORTED_LANGUAGES = settings.SUPPORTED_LANGUAGES
except ImportError:
    # Bağımlılık döngüsünü önlemek için varsayılan değerler kullanılır
    DEFAULT_LANGUAGE = "tr"
    SUPPORTED_LANGUAGES = ["tr", "en"]

# Dil dosyalarının bulunduğu dizin
TRANSLATIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "translations")

# Çeviri sözlükleri
_translations = {
    "tr": {},
    "en": {}
}

def translate(key: str, locale: Optional[str] = None, **kwargs) -> str:
    """
    Belirtilen anahtara göre metni çevirir.
    
    Args:
        key: Çeviri anahtarı
        locale: Dil kodu (belirtilmezse, varsayılan dil kullanılır)
        **kwargs: Metin içindeki yer tutucular için değerler
    
    Returns:
        Çevrilmiş metin
    """
    # Varsayılan dili kullan
    if not locale or locale not in SUPPORTED_LANGUAGES:
        locale = DEFAULT_LANGUAGE
        
    # Çeviri sözlüğünden anahtarı bul
    text = _get_translation_value(key, locale)
    
    # Yer tutucuları değiştir
    if kwargs:
        try:
            text = text.format(**kwargs)
        except:
            pass
    
    return text

def _get_translation_value(key: str, locale: str) -> str:
    """
    Belirtilen anahtarın çevirisini döndürür.
    
    Args:
        key: Çeviri anahtarı
        locale: Dil kodu
    
    Returns:
        Çevrilmiş metin veya anahtar bulunamazsa anahtarın kendisi
    """
    # Nokta notasyonunu ayrıştır (örn. "common.welcome" -> ["common", "welcome"])
    parts = key.split('.')
    
    # Çeviri sözlüğünde dolaş
    current = _translations.get(locale, {})
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return key
    
    # Bulunan değer bir metin değilse anahtarı döndür
    if not isinstance(current, str):
        return key
    
    return current

def _load_translations():
    """
    Çeviri dosyalarını yükler.
    """
    global _translations
    
    # Dil dosyaları dizininin varlığını kontrol et ve oluştur
    os.makedirs(TRANSLATIONS_DIR, exist_ok=True)
    
    # Desteklenen diller için çeviri dosyalarını yükle
    for locale in SUPPORTED_LANGUAGES:
        file_path = os.path.join(TRANSLATIONS_DIR, f"{locale}.yml")
        
        # Dosya yoksa oluştur
        if not os.path.exists(file_path):
            _create_default_translation_file(locale)
        
        # Dosyayı oku ve çevirileri yükle
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Basit bir YAML parser
            _translations[locale] = _parse_yaml(content)
        except Exception as e:
            print(f"Çeviri dosyası yüklenirken hata oluştu ({locale}): {str(e)}")

def _parse_yaml(content: str) -> Dict[str, Any]:
    """
    Basit bir YAML parser.
    
    Args:
        content: YAML içeriği
    
    Returns:
        Dict[str, Any]: Ayrıştırılmış YAML
    """
    result = {}
    
    # İlk olarak ana dil anahtarını (tr: veya en:) bulup kaldıralım
    lines = content.split('\n')
    language_key = None
    content_lines = []
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith('#'):
            continue
        
        # Dil anahtarını bul (tr: veya en:)
        if not language_key and line_stripped.endswith(':') and ':' in line_stripped:
            language_key = line_stripped[:-1].strip()
            continue
            
        # Diğer satırları içerik olarak ekle
        if language_key:
            content_lines.append(line)
    
    # Şimdi içeriği ayrıştıralım
    current_path = []
    current_indent = -1
    nested_dict = {}
    
    for line in content_lines:
        if not line.strip():
            continue
            
        # Satırın girintisini hesapla
        indent = len(line) - len(line.lstrip())
        line = line.strip()
        
        # Anahtar ve değeri ayır
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            # Girinti seviyesine göre geçerli yolu güncelle
            if current_indent == -1 or indent == current_indent:
                # Aynı seviye
                if current_path:
                    current_path[-1] = key
                else:
                    current_path.append(key)
            elif indent > current_indent:
                # Alt seviye
                current_path.append(key)
            else:
                # Üst seviye
                level_diff = (current_indent - indent) // 2
                current_path = current_path[:-level_diff]
                current_path[-1] = key
                
            current_indent = indent
            
            # Değer varsa (örn. "key: value")
            if value and value.startswith('"') and value.endswith('"'):
                # İç içe sözlükleri oluştur
                temp_dict = nested_dict
                for path_key in current_path[:-1]:
                    if path_key not in temp_dict:
                        temp_dict[path_key] = {}
                    temp_dict = temp_dict[path_key]
                
                # Son anahtara değeri ata
                temp_dict[current_path[-1]] = value[1:-1]  # Tırnak işaretlerini kaldır
            else:
                # İç içe sözlükleri oluştur (alt sözlük başlangıcı için)
                temp_dict = nested_dict
                for path_key in current_path:
                    if path_key not in temp_dict:
                        temp_dict[path_key] = {}
                    temp_dict = temp_dict[path_key]
    
    # Dil anahtarını ekle
    if language_key:
        result[language_key] = nested_dict
    
    return result

def _create_default_translation_file(locale: str):
    """
    Varsayılan çeviri dosyasını oluşturur.
    
    Args:
        locale: Dil kodu
    """
    file_path = os.path.join(TRANSLATIONS_DIR, f"{locale}.yml")
    
    # Türkçe çeviri dosyası
    if locale == "tr":
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("""tr:
  common:
    welcome: "Proje Atama Sistemine Hoşgeldiniz"
    login: "Giriş Yap"
    logout: "Çıkış Yap"
    dashboard: "Kontrol Paneli"
    settings: "Ayarlar"
    save: "Kaydet"
    cancel: "İptal"
    delete: "Sil"
    edit: "Düzenle"
    add: "Ekle"
    search: "Ara"
    loading: "Yükleniyor..."
    no_data: "Veri bulunamadı"
    success: "Başarılı"
    error: "Hata"
    yes: "Evet"
    no: "Hayır"
  
  algorithms:
    title: "Algoritmalar"
    select: "Algoritma Seç"
    run: "Çalıştır"
    running: "Algoritma çalışıyor..."
    success: "Algoritma başarıyla çalıştırıldı"
    error: "Algoritma çalıştırılırken hata oluştu"
    recommend: "En İyi Algoritmayı Öner"
    invalid_algorithm: "Geçersiz algoritma türü"
    not_completed: "Algoritma henüz tamamlanmadı"
    run_not_found: "Algoritma çalıştırması bulunamadı"
    status_error: "Algoritma durumu alınırken hata oluştu"
    execution_error: "Algoritma çalıştırılırken hata oluştu"
    recommendation_error: "Algoritma önerisi alınırken hata oluştu"
    completed: "Algoritma başarıyla tamamlandı"
""")
    # İngilizce çeviri dosyası
    elif locale == "en":
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("""en:
  common:
    welcome: "Welcome to Project Assignment System"
    login: "Login"
    logout: "Logout"
    dashboard: "Dashboard"
    settings: "Settings"
    save: "Save"
    cancel: "Cancel"
    delete: "Delete"
    edit: "Edit"
    add: "Add"
    search: "Search"
    loading: "Loading..."
    no_data: "No data found"
    success: "Success"
    error: "Error"
    yes: "Yes"
    no: "No"
  
  algorithms:
    title: "Algorithms"
    select: "Select Algorithm"
    run: "Run"
    running: "Algorithm is running..."
    success: "Algorithm ran successfully"
    error: "Error running algorithm"
    recommend: "Recommend Best Algorithm"
    invalid_algorithm: "Invalid algorithm type"
    not_completed: "Algorithm not yet completed"
    run_not_found: "Algorithm run not found"
    status_error: "Error getting algorithm status"
    execution_error: "Error executing algorithm"
    recommendation_error: "Error getting algorithm recommendation"
    completed: "Algorithm completed successfully"
""")

def get_supported_languages():
    """
    Desteklenen dillerin listesini döndürür.
    
    Returns:
        Desteklenen dil kodlarının listesi
    """
    return SUPPORTED_LANGUAGES

def set_locale(locale: str):
    """
    Aktif dili ayarlar.
    
    Args:
        locale: Dil kodu (örneğin "tr", "en")
    
    Returns:
        bool: Dil başarıyla ayarlandıysa True, desteklenmeyen bir dilse False
    """
    global DEFAULT_LANGUAGE
    if locale in SUPPORTED_LANGUAGES:
        DEFAULT_LANGUAGE = locale
        return True
    return False

def init_i18n():
    """
    i18n modülünü başlatır ve çeviri dosyalarını yükler.
    """
    _load_translations()

# Kısayollar
t = translate
_ = translate

# Başlangıçta çeviri dosyalarını yükle
_load_translations() 