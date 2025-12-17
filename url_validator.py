"""
Módulo para validar URLs de YouTube.

Este módulo se encarga de:
- Validar que las URLs sean válidas para YouTube
- Verificar formato de URLs
"""


def validar_url_youtube(url: str) -> bool:
    """
    Valida que una URL sea válida para YouTube.
    
    Args:
        url: La URL a validar.
    
    Returns:
        bool: True si la URL es válida, False en caso contrario.
    """
    if not url or not isinstance(url, str):
        return False
    
    # Verificar que sea una URL de YouTube
    youtube_domains = ['youtube.com', 'youtu.be', 'www.youtube.com']
    return any(domain in url.lower() for domain in youtube_domains)

