"""
Módulo de utilidades compartidas.

Contiene funciones auxiliares utilizadas por múltiples módulos del sistema.
"""

import re
import logging
from pathlib import Path


def sanitizar_nombre_archivo(nombre: str) -> str:
    """
    Limpia un string para que sea un nombre de archivo válido.
    
    Elimina o reemplaza caracteres especiales que no son válidos en nombres
    de archivo según el sistema operativo.
    
    Args:
        nombre: El nombre de archivo original que necesita ser sanitizado.
    
    Returns:
        str: El nombre de archivo limpio y válido (máximo 150 caracteres).
    
    Ejemplo:
        >>> sanitizar_nombre_archivo("Video: Test | Parte 1/2")
        'Video_Test_Parte_1_2'
    """
    try:
        # Reemplazar espacios, | y : con _
        nombre = re.sub(r'[\s|:]+', '_', nombre)
        # Eliminar caracteres no válidos para nombres de archivo
        nombre = re.sub(r'[\\/*?"<>|]', "", nombre)
        # Limitar la longitud
        return nombre[:150]
    except Exception as e:
        logging.error(f"Error al sanitizar nombre de archivo '{nombre}': {e}")
        return "video_sin_nombre"


def parsear_duracion_a_segundos(duration_str: str) -> int:
    """
    Convierte un string de duración (ej. "1:05:30" o "15:20") a segundos.
    
    Soporta múltiples formatos:
    - HH:MM:SS (horas:minutos:segundos)
    - MM:SS (minutos:segundos)
    - SS (solo segundos)
    
    Args:
        duration_str: String con la duración en formato de tiempo.
    
    Returns:
        int: Duración total en segundos. Retorna 0 si hay un error.
    
    Ejemplo:
        >>> parsear_duracion_a_segundos("1:05:30")
        3930
        >>> parsear_duracion_a_segundos("15:20")
        920
        >>> parsear_duracion_a_segundos("45")
        45
    """
    if not duration_str or not duration_str.strip():
        return 0
    
    try:
        # Limpiar el string y dividir por ':'
        partes_str = duration_str.strip().split(':')
        # Filtrar partes vacías y convertir a int
        partes = [int(p) for p in partes_str if p.strip()]
        
        if len(partes) == 3:  # HH:MM:SS
            return partes[0] * 3600 + partes[1] * 60 + partes[2]
        if len(partes) == 2:  # MM:SS
            return partes[0] * 60 + partes[1]
        if len(partes) == 1:  # SS
            return partes[0]
        return 0
    except (ValueError, IndexError) as e:
        logging.warning(f"Error al parsear duración '{duration_str}': {e}")
        return 0


def formatear_tiempo(segundos: int) -> str:
    """
    Convierte segundos a un formato legible (días, horas, minutos, segundos).
    
    Args:
        segundos: Número total de segundos a formatear.
    
    Returns:
        str: String formateado con la duración legible.
    
    Ejemplo:
        >>> formatear_tiempo(3665)
        '1 hora(s) y 1 minuto(s) y 5 segundo(s)'
    """
    if segundos < 60:
        return f"{segundos} segundo(s)"
    
    minutos = segundos // 60
    segundos_restantes = segundos % 60
    
    if minutos < 60:
        if segundos_restantes > 0:
            return f"{minutos} minuto(s) y {segundos_restantes} segundo(s)"
        return f"{minutos} minuto(s)"
    
    horas = minutos // 60
    minutos_restantes = minutos % 60
    
    if horas < 24:
        if minutos_restantes > 0:
            return f"{horas} hora(s) y {minutos_restantes} minuto(s)"
        return f"{horas} hora(s)"
    
    dias = horas // 24
    horas_restantes = horas % 24
    
    if horas_restantes > 0:
        return f"{dias} día(s) y {horas_restantes} hora(s)"
    return f"{dias} día(s)"


def formatear_tamaño(bytes_size: int) -> str:
    """
    Convierte bytes a un formato legible (KB, MB, GB, TB).
    
    Args:
        bytes_size: Tamaño en bytes a formatear.
    
    Returns:
        str: String formateado con el tamaño legible y unidad apropiada.
    
    Ejemplo:
        >>> formatear_tamaño(1048576)
        '1.00 MB'
    """
    if bytes_size < 1024:
        return f"{bytes_size} B"
    
    kb = bytes_size / 1024
    if kb < 1024:
        return f"{kb:.2f} KB"
    
    mb = kb / 1024
    if mb < 1024:
        return f"{mb:.2f} MB"
    
    gb = mb / 1024
    if gb < 1024:
        return f"{gb:.2f} GB"
    
    tb = gb / 1024
    return f"{tb:.2f} TB"


def configurar_logging():
    """
    Configura el sistema de logging para mostrar información clara.
    
    Establece el formato de los mensajes de log con fecha, nivel y mensaje.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

