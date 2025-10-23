"""
i18n modülü için yönlendirici.
Bu dosya, app.i18n modülünden gerekli fonksiyonları içe aktarır.
"""

from app.i18n import translate, setup_i18n, set_locale, get_supported_languages, init_i18n

def get_translator():
    """
    Çeviri fonksiyonunu döndürür.
    
    Returns:
        Çeviri fonksiyonu
    """
    return translate

__all__ = ["translate", "get_translator", "init_i18n", "set_locale", "get_supported_languages"] 