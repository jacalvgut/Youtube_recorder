"""
Módulo para cargar URLs en el navegador.

Este módulo se encarga de:
- Cargar URLs en nuevas pestañas
- Verificar carga completa de páginas
- Validar que estamos en YouTube
"""

import time
import logging
from typing import Optional
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException


def cargar_url_en_navegador(driver: webdriver.Chrome, url: str) -> bool:
    """
    Carga una URL en el navegador.
    
    Args:
        driver: Instancia de WebDriver.
        url: La URL a cargar.
    
    Returns:
        bool: True si la carga fue exitosa, False en caso contrario.
    """
    if not driver:
        logging.error("ERROR: El navegador no está inicializado")
        return False
    
    try:
        logging.info("")
        logging.info("=" * 70)
        logging.info("VERIFICACIÓN: Cargando video en navegador...")
        logging.info("=" * 70)
        logging.info(f"URL: {url}")
        
        # Obtener ventanas antes de abrir nueva pestaña
        try:
            ventanas_antes = driver.window_handles
            logging.info(f"Ventanas abiertas antes: {len(ventanas_antes)}")
        except:
            logging.error("Error al obtener ventanas.")
            return False
        
        # Intentar abrir en nueva pestaña
        try:
            driver.execute_script(f"window.open('{url}', '_blank');")
            time.sleep(2)
            
            # Verificar que se creó una nueva pestaña
            ventanas_despues = driver.window_handles
            logging.info(f"Ventanas antes: {len(ventanas_antes)}, después: {len(ventanas_despues)}")
            
            if len(ventanas_despues) > len(ventanas_antes):
                nueva_ventana = [w for w in ventanas_despues if w not in ventanas_antes][0]
                driver.switch_to.window(nueva_ventana)
                logging.info("✓ Nueva pestaña creada y activada")
            elif len(ventanas_despues) > 0:
                driver.switch_to.window(ventanas_despues[-1])
                logging.info("✓ Usando última pestaña disponible")
            else:
                logging.warning("No se pudo abrir nueva pestaña. Usando driver.get()...")
                driver.get(url)
        except Exception as e:
            logging.warning(f"Error al abrir nueva pestaña: {e}")
            logging.info("Intentando con driver.get() directamente...")
            driver.get(url)
        
        # Esperar a que la página cargue completamente
        wait = WebDriverWait(driver, 30)
        try:
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            logging.info("✓ Página cargada completamente (readyState = complete)")
        except TimeoutException:
            logging.error("ERROR: Timeout esperando carga completa de la página")
            return False
        
        # Verificar que estamos en YouTube
        url_actual = driver.current_url
        if "youtube.com" not in url_actual.lower():
            logging.error(f"ERROR: No se está en YouTube. URL actual: {url_actual}")
            return False
        
        logging.info(f"✓ Confirmado: Estamos en YouTube ({url_actual[:50]}...)")
        
        # Esperar adicional para que YouTube cargue completamente
        time.sleep(5)
        logging.info("✓ Tiempo de espera adicional completado")
        
        return True
    
    except Exception as e:
        logging.error(f"ERROR al cargar URL: {e}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        return False

