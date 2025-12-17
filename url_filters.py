"""
Módulo para aplicar filtros a módulos y URLs.

Este módulo se encarga de:
- Filtrar módulos por inicio
- Aplicar límites de modo prueba
- Configurar índices de inicio de video
"""

import logging
from typing import Dict, List
import config


def aplicar_modulo_inicio(modulos: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Filtra los módulos para empezar desde un módulo específico.
    
    Args:
        modulos: Diccionario de módulos y URLs.
    
    Returns:
        Dict: Diccionario filtrado de módulos.
    """
    if not config.MODULO_INICIO:
        return modulos
    
    modulos_lista = list(modulos.items())
    modulo_encontrado = False
    modulos_filtrados = {}
    
    for nombre_modulo, urls in modulos_lista:
        if nombre_modulo == config.MODULO_INICIO:
            modulo_encontrado = True
            modulos_filtrados[nombre_modulo] = urls
            logging.info(f"Empezando desde el módulo '{nombre_modulo}'")
        elif modulo_encontrado:
            modulos_filtrados[nombre_modulo] = urls
    
    if not modulo_encontrado:
        logging.warning(f"ADVERTENCIA: No se encontró el módulo '{config.MODULO_INICIO}'. Se procesarán todos los módulos.")
        return modulos
    
    modulos_omitidos = len(modulos) - len(modulos_filtrados)
    if modulos_omitidos > 0:
        logging.info(f"Omitiendo {modulos_omitidos} módulo(s) anteriores a '{config.MODULO_INICIO}'")
    
    return modulos_filtrados


def aplicar_limites_prueba(modulos: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Aplica los límites configurados para el modo de prueba.
    
    Args:
        modulos: Diccionario de módulos y URLs.
    
    Returns:
        Dict: Diccionario con límites aplicados.
    """
    if not config.MODO_PRUEBA:
        return modulos
    
    modulos_limitados = modulos.copy()
    
    if config.MAX_MODULOS_PRUEBA:
        modulos_lista = list(modulos_limitados.items())
        modulos_limitados = dict(modulos_lista[:config.MAX_MODULOS_PRUEBA])
        modulos_omitidos = len(modulos) - len(modulos_limitados)
        
        if modulos_omitidos > 0:
            logging.info(f"Modo prueba: Procesando solo {len(modulos_limitados)} de {len(modulos)} módulos")
    
    if config.MAX_VIDEOS_POR_MODULO_PRUEBA:
        for modulo, urls in modulos_limitados.items():
            if len(urls) > config.MAX_VIDEOS_POR_MODULO_PRUEBA:
                urls_limitadas = urls[:config.MAX_VIDEOS_POR_MODULO_PRUEBA]
                logging.info(f"Modo prueba: Limitando '{modulo}' a {len(urls_limitadas)} de {len(urls)} videos")
                modulos_limitados[modulo] = urls_limitadas
    
    return modulos_limitados


def aplicar_inicio_video(modulos: Dict[str, List[str]]) -> Dict[str, int]:
    """
    Aplica la configuración de inicio de video para continuar desde un índice específico.
    
    Args:
        modulos: Diccionario de módulos y URLs (se modifica in-place).
    
    Returns:
        Dict: Diccionario con índices de inicio por módulo.
    """
    indices_inicio = {}
    
    # Si hay configuración por módulo, usarla
    if config.INICIO_VIDEO_POR_MODULO and isinstance(config.INICIO_VIDEO_POR_MODULO, dict):
        for modulo, urls in modulos.items():
            inicio = config.INICIO_VIDEO_POR_MODULO.get(modulo)
            if inicio is not None and inicio > 1:
                if inicio <= len(urls):
                    modulos[modulo] = urls[inicio - 1:]
                    indices_inicio[modulo] = inicio
                    logging.info(f"Continuando '{modulo}' desde el video {inicio} (quedan {len(modulos[modulo])} videos)")
                else:
                    logging.warning(f"ADVERTENCIA: Índice de inicio {inicio} mayor que el número de videos ({len(urls)}) en '{modulo}'. Se procesarán todos los videos.")
                    indices_inicio[modulo] = 1
            else:
                indices_inicio[modulo] = 1
    # Si hay configuración global, aplicarla solo al primer módulo
    elif config.INICIO_VIDEO and config.INICIO_VIDEO > 1:
        primer_modulo = True
        for modulo, urls in modulos.items():
            if primer_modulo:
                inicio = config.INICIO_VIDEO
                if inicio <= len(urls):
                    modulos[modulo] = urls[inicio - 1:]
                    indices_inicio[modulo] = inicio
                    logging.info(f"Continuando '{modulo}' desde el video {inicio} (quedan {len(modulos[modulo])} videos)")
                else:
                    logging.warning(f"ADVERTENCIA: Índice de inicio {inicio} mayor que el número de videos ({len(urls)}) en '{modulo}'. Se procesarán todos los videos.")
                    indices_inicio[modulo] = 1
                primer_modulo = False
            else:
                indices_inicio[modulo] = 1
    else:
        # Sin configuración de inicio, todos empiezan desde 1
        for modulo in modulos.keys():
            indices_inicio[modulo] = 1
    
    return indices_inicio

