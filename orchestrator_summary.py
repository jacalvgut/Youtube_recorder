"""
Módulo para generar resúmenes y estadísticas del orquestador.

Este módulo se encarga de:
- Calcular estadísticas finales
- Mostrar resumen de ejecución
- Formatear información de resultados
"""

import logging
from pathlib import Path
from typing import Dict, List
from utils import formatear_tiempo, formatear_tamaño


def calcular_tamaño_total(modulos_procesados: List[str]) -> int:
    """
    Calcula el tamaño total de archivos en las carpetas de módulos procesados.
    
    Args:
        modulos_procesados: Lista de nombres de módulos procesados.
    
    Returns:
        int: Tamaño total en bytes.
    """
    directorio_base = Path.cwd()
    tamaño_total = 0
    
    try:
        for nombre_modulo in modulos_procesados:
            ruta_modulo = directorio_base / nombre_modulo
            if ruta_modulo.exists() and ruta_modulo.is_dir():
                for archivo in ruta_modulo.iterdir():
                    if archivo.is_file():
                        tamaño_total += archivo.stat().st_size
    except Exception as e:
        logging.warning(f"Error al calcular tamaño total: {e}")
    
    return tamaño_total


def mostrar_resumen_final(estadisticas: Dict, modulos_procesados: List[str]) -> None:
    """
    Muestra el resumen final de la ejecución.
    
    Args:
        estadisticas: Diccionario con estadísticas de la ejecución.
        modulos_procesados: Lista de nombres de módulos procesados.
    """
    logging.info("")
    logging.info("=" * 70)
    logging.info("RESUMEN FINAL DE EJECUCIÓN")
    logging.info("=" * 70)
    
    # Calcular tamaño total de archivos
    tamaño_total_calculado = calcular_tamaño_total(modulos_procesados)
    
    # Usar el tamaño calculado si es mayor
    if tamaño_total_calculado > estadisticas['tamaño_total_bytes']:
        estadisticas['tamaño_total_bytes'] = tamaño_total_calculado
    
    # Mostrar estadísticas
    logging.info(f"  ✓ Videos grabados exitosamente: {estadisticas['videos_grabados']}")
    
    if estadisticas['duracion_total_segundos'] > 0:
        tiempo_formateado = formatear_tiempo(estadisticas['duracion_total_segundos'])
        logging.info(f"  ✓ Duración total grabada: {tiempo_formateado}")
        horas_totales = estadisticas['duracion_total_segundos'] / 3600
        if horas_totales >= 1:
            logging.info(f"    ({horas_totales:.2f} horas)")
    else:
        logging.info(f"  ✓ Duración total grabada: 0 segundos")
    
    if estadisticas['tamaño_total_bytes'] > 0:
        tamaño_formateado = formatear_tamaño(estadisticas['tamaño_total_bytes'])
        logging.info(f"  ✓ Tamaño total de archivos: {tamaño_formateado}")
    else:
        logging.info(f"  ✓ Tamaño total de archivos: 0 bytes")
    
    logging.info("=" * 70)
    logging.info("")

