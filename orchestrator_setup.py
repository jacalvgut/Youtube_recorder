"""
Módulo de configuración inicial del orquestador.

Este módulo se encarga de:
- Configurar logging
- Mostrar información del modo de prueba
- Mostrar instrucciones de configuración
"""

import time
import logging
import config


def mostrar_info_modo_prueba() -> None:
    """Muestra información sobre el modo de prueba si está activo."""
    if config.MODO_PRUEBA:
        logging.warning("=" * 60)
        logging.warning("MODO DE PRUEBA ACTIVADO")
        logging.warning("=" * 60)
        if config.MAX_MODULOS_PRUEBA:
            logging.info(f"  - Máximo de módulos a procesar: {config.MAX_MODULOS_PRUEBA}")
        if config.MAX_VIDEOS_POR_MODULO_PRUEBA:
            logging.info(f"  - Máximo de videos por módulo: {config.MAX_VIDEOS_POR_MODULO_PRUEBA}")
        if config.DURACION_MAXIMA_PRUEBA:
            logging.info(f"  - Duración máxima por video: {config.DURACION_MAXIMA_PRUEBA} segundos (modo prueba)")
        logging.warning("=" * 60)
        logging.warning("Para procesar todos los videos, cambia MODO_PRUEBA = False en config.py")
        logging.warning("=" * 60)
        time.sleep(3)


def mostrar_instrucciones_configuracion() -> None:
    """Muestra instrucciones de configuración necesarias."""
    logging.info("")
    logging.info("=" * 70)
    logging.info("CONFIGURACIÓN REQUERIDA")
    logging.info("=" * 70)
    logging.info("IMPORTANTE: Asegúrate de que:")
    logging.info(f"  1. {config.NAVEGADOR.capitalize()} esté abierto con --remote-debugging-port={config.DEBUG_PORT}")
    logging.info("  2. OBS esté configurado para capturar la ventana del navegador")
    logging.info("  3. La ventana del navegador esté visible en el monitor correcto")
    logging.info("=" * 70)
    logging.info("")
    time.sleep(2)

