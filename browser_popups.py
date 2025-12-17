"""
Módulo para gestionar popups y anuncios de YouTube.

Este módulo se encarga de:
- Cerrar popups de YouTube
- Omitir anuncios
- Gestionar banners y overlays
"""

import time
import logging
from typing import Optional
from selenium.webdriver.common.by import By
from selenium import webdriver


SELECTORES_POPUPS = [
    # Banner de cookies
    "button[aria-label*='Aceptar']",
    "button[aria-label*='Accept']",
    "button[aria-label*='Aceptar todo']",
    "button[aria-label*='Accept all']",
    "ytd-consent-bump-v2-lightbox button",
    "#content button[aria-label*='Aceptar']",
    
    # Botones de cerrar (X)
    "button[aria-label*='Cerrar']",
    "button[aria-label*='Close']",
    "button[aria-label*='Dismiss']",
    "button[aria-label*='Descartar']",
    ".ytp-ad-overlay-close-button",
    "button.close-button",
    "button.dismiss-button",
    
    # Avisos de inicio de sesión
    "ytd-popup-container button",
    "ytd-modal-with-title-and-button-renderer button",
    "#dismiss-button",
    "button[aria-label*='No, gracias']",
    "button[aria-label*='No thanks']",
    "button[aria-label*='Ahora no']",
    "button[aria-label*='Not now']",
    
    # Ofertas de Premium
    "ytd-mealbar-promo-renderer button",
    "ytd-popup-container ytd-mealbar-promo-renderer button",
    
    # Anuncios de video (Skip Ad)
    "button.ytp-ad-skip-button",
    ".ytp-ad-skip-button",
    "button[aria-label*='Omitir']",
    "button[aria-label*='Skip']",
    "button.ytp-ad-skip-button-modern",
    
    # Overlays de anuncios
    ".ytp-ad-overlay-close-container",
    ".ytp-ad-overlay-close-button",
    "button.ytp-ad-overlay-close-button",
    
    # Banners superiores
    "ytd-banner-promo-renderer button",
    "ytd-popup-container #dismiss-button",
]


def cerrar_popups_youtube(driver: webdriver.Chrome, max_intentos: int = 5, silencioso: bool = False) -> bool:
    """
    Cierra todos los tipos de popups, banners y anuncios de YouTube.
    
    Args:
        driver: Instancia de WebDriver.
        max_intentos: Número máximo de intentos para cerrar popups.
        silencioso: Si es True, no muestra mensajes a menos que cierre popups.
    
    Returns:
        bool: True si se cerraron popups, False en caso contrario.
    """
    if not driver:
        return False
    
    popups_cerrados = 0
    
    for intento in range(max_intentos):
        popups_encontrados = False
        
        for selector in SELECTORES_POPUPS:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, selector)
                for elemento in elementos:
                    try:
                        if elemento.is_displayed() and elemento.is_enabled():
                            driver.execute_script("arguments[0].scrollIntoView(true);", elemento)
                            time.sleep(0.2)
                            
                            elemento.click()
                            if not silencioso:
                                logging.info(f"Popup cerrado: {selector[:50]}...")
                            popups_cerrados += 1
                            popups_encontrados = True
                            time.sleep(0.5)
                            break
                    except:
                        try:
                            driver.execute_script("arguments[0].click();", elemento)
                            if not silencioso:
                                logging.info(f"Popup cerrado (JS): {selector[:50]}...")
                            popups_cerrados += 1
                            popups_encontrados = True
                            time.sleep(0.5)
                            break
                        except:
                            continue
            except:
                continue
        
        if not popups_encontrados:
            break
        
        time.sleep(0.3)
    
    if popups_cerrados > 0:
        logging.info(f"Total de popups cerrados: {popups_cerrados}")
    elif not silencioso:
        logging.debug("No se encontraron popups para cerrar")
    
    return popups_cerrados > 0


def intentar_omitir_anuncios(driver: webdriver.Chrome, max_intentos: int = 10) -> bool:
    """
    Intenta omitir anuncios de YouTube si están presentes.
    
    Args:
        driver: Instancia de WebDriver.
        max_intentos: Número máximo de intentos.
    
    Returns:
        bool: True si se omitió un anuncio, False en caso contrario.
    """
    if not driver:
        return False
    
    selectores_skip = [
        "button.ytp-ad-skip-button",
        ".ytp-ad-skip-button",
        "button[aria-label*='Omitir']",
        "button[aria-label*='Skip']",
        ".ytp-ad-overlay-close-button",
        "button.ytp-ad-skip-button-modern"
    ]
    
    for intento in range(max_intentos):
        try:
            for selector in selectores_skip:
                try:
                    boton_skip = driver.find_element(By.CSS_SELECTOR, selector)
                    if boton_skip.is_displayed():
                        try:
                            boton_skip.click()
                        except:
                            driver.execute_script("arguments[0].click();", boton_skip)
                        logging.info("Anuncio omitido exitosamente")
                        time.sleep(1)
                        return True
                except:
                    continue
            
            # Verificar si aún hay un anuncio activo
            try:
                driver.find_element(By.CLASS_NAME, "ytp-ad-module")
                time.sleep(0.5)
            except:
                break
                
        except:
            pass
        
        time.sleep(0.5)
    
    return False

