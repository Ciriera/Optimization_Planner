"""
Internationalization (i18n) Service
Proje açıklamasına göre: Çoklu dil desteği
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class I18nService:
    """
    Çoklu dil desteği servisi.
    Proje açıklamasına göre: Çoklu dil desteği
    """
    
    def __init__(self):
        self.translations_dir = Path("app/static/translations")
        self.translations_dir.mkdir(parents=True, exist_ok=True)
        self.supported_languages = ["tr", "en", "de", "fr", "es"]
        self.default_language = "tr"
        self.translations = {}
        self._load_translations()
    
    def _load_translations(self):
        """Çevirileri yükle"""
        try:
            for lang in self.supported_languages:
                translation_file = self.translations_dir / f"{lang}.json"
                if translation_file.exists():
                    with open(translation_file, 'r', encoding='utf-8') as f:
                        self.translations[lang] = json.load(f)
                else:
                    # Varsayılan çevirileri oluştur
                    self.translations[lang] = self._get_default_translations(lang)
                    self._save_translations(lang, self.translations[lang])
        except Exception as e:
            logger.error(f"Error loading translations: {str(e)}")
    
    def _get_default_translations(self, language: str) -> Dict[str, Any]:
        """Varsayılan çevirileri getir"""
        translations = {
            "tr": {
                "common": {
                    "save": "Kaydet",
                    "cancel": "İptal",
                    "delete": "Sil",
                    "edit": "Düzenle",
                    "create": "Oluştur",
                    "search": "Ara",
                    "filter": "Filtrele",
                    "loading": "Yükleniyor...",
                    "error": "Hata",
                    "success": "Başarılı"
                },
                "navigation": {
                    "dashboard": "Ana Sayfa",
                    "projects": "Projeler",
                    "instructors": "Hocalar",
                    "classrooms": "Sınıflar",
                    "algorithms": "Algoritmalar",
                    "reports": "Raporlar",
                    "settings": "Ayarlar"
                },
                "project": {
                    "title": "Proje Başlığı",
                    "type": "Proje Türü",
                    "responsible": "Danışman",
                    "participants": "Katılımcılar",
                    "bitirme": "Bitirme",
                    "ara": "Ara",
                    "final": "Final",
                    "makeup": "Bütünleme"
                },
                "algorithm": {
                    "run": "Çalıştır",
                    "stop": "Durdur",
                    "status": "Durum",
                    "progress": "İlerleme",
                    "recommendation": "Öneri",
                    "parameters": "Parametreler"
                }
            },
            "en": {
                "common": {
                    "save": "Save",
                    "cancel": "Cancel",
                    "delete": "Delete",
                    "edit": "Edit",
                    "create": "Create",
                    "search": "Search",
                    "filter": "Filter",
                    "loading": "Loading...",
                    "error": "Error",
                    "success": "Success"
                },
                "navigation": {
                    "dashboard": "Dashboard",
                    "projects": "Projects",
                    "instructors": "Instructors",
                    "classrooms": "Classrooms",
                    "algorithms": "Algorithms",
                    "reports": "Reports",
                    "settings": "Settings"
                },
                "project": {
                    "title": "Project Title",
                    "type": "Project Type",
                    "responsible": "Advisor",
                    "participants": "Participants",
                    "bitirme": "Thesis",
                    "ara": "Midterm",
                    "final": "Final",
                    "makeup": "Makeup"
                },
                "algorithm": {
                    "run": "Run",
                    "stop": "Stop",
                    "status": "Status",
                    "progress": "Progress",
                    "recommendation": "Recommendation",
                    "parameters": "Parameters"
                }
            }
        }
        
        return translations.get(language, translations["tr"])
    
    async def get_translation(self, key: str, language: str = None, **kwargs) -> str:
        """
        Çeviri getirir.
        
        Args:
            key: Çeviri anahtarı (örn: "common.save")
            language: Dil kodu (varsayılan: default_language)
            **kwargs: Çeviri parametreleri
            
        Returns:
            Çevrilmiş metin
        """
        try:
            if language is None:
                language = self.default_language
            
            if language not in self.translations:
                language = self.default_language
            
            # Anahtarı böl (örn: "common.save" -> ["common", "save"])
            key_parts = key.split(".")
            translation = self.translations[language]
            
            # İç içe geçmiş sözlükte gezin
            for part in key_parts:
                if isinstance(translation, dict) and part in translation:
                    translation = translation[part]
                else:
                    # Çeviri bulunamadı, anahtarı döndür
                    return key
            
            # Parametreleri değiştir
            if isinstance(translation, str) and kwargs:
                try:
                    translation = translation.format(**kwargs)
                except (KeyError, ValueError):
                    # Format hatası, orijinal metni döndür
                    pass
            
            return translation
            
        except Exception as e:
            logger.error(f"Error getting translation for key '{key}': {str(e)}")
            return key
    
    async def get_all_translations(self, language: str = None) -> Dict[str, Any]:
        """Tüm çevirileri getirir"""
        if language is None:
            language = self.default_language
        
        return self.translations.get(language, {})
    
    async def update_translation(self, key: str, value: str, language: str = None) -> bool:
        """
        Çeviri günceller.
        
        Args:
            key: Çeviri anahtarı
            value: Yeni çeviri değeri
            language: Dil kodu
            
        Returns:
            Güncelleme başarılı mı
        """
        try:
            if language is None:
                language = self.default_language
            
            if language not in self.translations:
                self.translations[language] = {}
            
            # Anahtarı böl ve iç içe geçmiş sözlükte güncelle
            key_parts = key.split(".")
            current_dict = self.translations[language]
            
            # Son anahtar hariç tüm parçalar için sözlük oluştur
            for part in key_parts[:-1]:
                if part not in current_dict:
                    current_dict[part] = {}
                current_dict = current_dict[part]
            
            # Son anahtarı güncelle
            current_dict[key_parts[-1]] = value
            
            # Dosyaya kaydet
            self._save_translations(language, self.translations[language])
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating translation for key '{key}': {str(e)}")
            return False
    
    def _save_translations(self, language: str, translations: Dict[str, Any]):
        """Çevirileri dosyaya kaydet"""
        try:
            translation_file = self.translations_dir / f"{language}.json"
            with open(translation_file, 'w', encoding='utf-8') as f:
                json.dump(translations, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving translations for language '{language}': {str(e)}")
    
    async def get_supported_languages(self) -> List[Dict[str, Any]]:
        """Desteklenen dilleri getirir"""
        return [
            {"code": "tr", "name": "Türkçe", "native_name": "Türkçe"},
            {"code": "en", "name": "English", "native_name": "English"},
            {"code": "de", "name": "Deutsch", "native_name": "Deutsch"},
            {"code": "fr", "name": "Français", "native_name": "Français"},
            {"code": "es", "name": "Español", "native_name": "Español"}
        ]
    
    async def format_date(self, date: datetime, language: str = None, format_type: str = "medium") -> str:
        """Tarihi dile göre formatla"""
        if language is None:
            language = self.default_language
        
        # Basit tarih formatları
        formats = {
            "tr": {
                "short": "%d.%m.%Y",
                "medium": "%d %B %Y",
                "long": "%d %B %Y, %A"
            },
            "en": {
                "short": "%m/%d/%Y",
                "medium": "%B %d, %Y",
                "long": "%A, %B %d, %Y"
            }
        }
        
        lang_formats = formats.get(language, formats["tr"])
        date_format = lang_formats.get(format_type, lang_formats["medium"])
        
        try:
            return date.strftime(date_format)
        except:
            return date.strftime("%Y-%m-%d")
    
    async def format_number(self, number: float, language: str = None) -> str:
        """Sayıyı dile göre formatla"""
        if language is None:
            language = self.default_language
        
        # Basit sayı formatları
        if language == "tr":
            return f"{number:,.2f}".replace(",", " ").replace(".", ",")
        elif language == "de":
            return f"{number:,.2f}".replace(",", " ")
        else:  # en, fr, es
            return f"{number:,.2f}"
    
    async def get_rtl_languages(self) -> List[str]:
        """Sağdan sola yazılan dilleri getirir"""
        return ["ar", "he", "fa", "ur"]  # Arapça, İbranice, Farsça, Urduca
    
    async def is_rtl_language(self, language: str) -> bool:
        """Dil sağdan sola mı kontrol et"""
        return language in await self.get_rtl_languages()
    
    async def validate_translation_key(self, key: str, language: str = None) -> bool:
        """Çeviri anahtarı geçerli mi kontrol et"""
        try:
            translation = await self.get_translation(key, language)
            return translation != key  # Anahtar ile çeviri aynı değilse geçerli
        except:
            return False
    
    async def get_missing_translations(self, reference_language: str = "tr") -> Dict[str, List[str]]:
        """Eksik çevirileri bul"""
        missing = {}
        
        if reference_language not in self.translations:
            return missing
        
        reference_keys = self._get_all_keys(self.translations[reference_language])
        
        for language in self.supported_languages:
            if language == reference_language:
                continue
            
            if language not in self.translations:
                missing[language] = reference_keys
                continue
            
            language_keys = self._get_all_keys(self.translations[language])
            missing_keys = [key for key in reference_keys if key not in language_keys]
            
            if missing_keys:
                missing[language] = missing_keys
        
        return missing
    
    def _get_all_keys(self, translations: Dict[str, Any], prefix: str = "") -> List[str]:
        """Tüm anahtarları getir"""
        keys = []
        
        for key, value in translations.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                keys.extend(self._get_all_keys(value, full_key))
            else:
                keys.append(full_key)
        
        return keys
