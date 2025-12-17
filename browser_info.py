"""
Módulo para obtener información de videos en YouTube.

Este módulo se encarga de:
- Obtener el título del video
- Obtener la duración del video
- Validar información del video
"""

import time
import logging
from typing import Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from utils import parsear_duracion_a_segundos


class BrowserInfo:
    """
    Clase encargada de obtener información de videos en YouTube.
    
    Maneja la extracción de título y duración de videos.
    """
    
    def __init__(self, driver):
        """
        Inicializa el extractor de información.
        
        Args:
            driver: Instancia de WebDriver de Selenium.
        """
        self.driver = driver
    
    def obtener_titulo_video(self) -> Optional[str]:
        """
        Obtiene solo el título del video de forma rápida.
        
        Returns:
            str: Título del video, o None si hay error.
        """
        if not self.driver:
            return None
        
        try:
            wait = WebDriverWait(self.driver, 10)
            
            # Intentar múltiples selectores para el título
            selectores_titulo = [
                "h1.ytd-watch-metadata yt-formatted-string",
                "h1.style-scope.ytd-watch-metadata",
                "h1.ytd-video-primary-info-renderer",
                ".ytd-watch-metadata h1",
                "h1.ytd-watch-metadata",
                "ytd-watch-metadata h1",
            ]
            
            for selector in selectores_titulo:
                try:
                    titulo_elemento = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    titulo_video = titulo_elemento.text.strip()
                    if titulo_video:
                        logging.info(f"✓ Título obtenido: {titulo_video[:60]}...")
                        return titulo_video
                except:
                    continue
            
            # Método alternativo: desde el título de la página
            try:
                titulo_video = self.driver.title.replace(" - YouTube", "").strip()
                if titulo_video and len(titulo_video) > 0:
                    logging.info(f"✓ Título obtenido desde título de página: {titulo_video[:60]}...")
                    return titulo_video
            except:
                pass
            
            return None
        
        except Exception as e:
            logging.warning(f"Error al obtener título: {e}")
            return None
    
    def obtener_duracion_video_continuo(self, max_segundos_espera: int = 30) -> Optional[int]:
        """
        Obtiene la duración del video de forma continua mientras ya está grabando.
        
        Intenta múltiples métodos y sigue intentando hasta obtenerla o alcanzar el tiempo máximo.
        
        Args:
            max_segundos_espera: Tiempo máximo en segundos para intentar obtener la duración.
        
        Returns:
            int: Duración en segundos, o None si no se pudo obtener.
        """
        if not self.driver:
            return None
        
        inicio = time.time()
        intento = 0
        
        while (time.time() - inicio) < max_segundos_espera:
            intento += 1
            
            # Método 1: Intentar con selectores CSS
            duracion_segundos = self._obtener_duracion_por_selectores()
            if duracion_segundos and duracion_segundos > 0:
                return duracion_segundos
            
            # Método 2: Intentar con JavaScript
            duracion_segundos = self._obtener_duracion_por_javascript()
            if duracion_segundos and duracion_segundos > 0:
                return duracion_segundos
            
            # Esperar un poco antes del siguiente intento
            if (time.time() - inicio) < max_segundos_espera - 1:
                time.sleep(1)
                if intento % 3 == 0:  # Log cada 3 intentos para no saturar
                    logging.info(f"Intentando obtener duración... (intento {intento}, ya llevan {(int(time.time() - inicio))}s)")
        
        logging.warning(f"No se pudo obtener la duración después de {max_segundos_espera} segundos")
        return None
    
    def _obtener_duracion_por_selectores(self) -> Optional[int]:
        """Intenta obtener la duración usando selectores CSS."""
        selectores_duracion = [
            (By.CLASS_NAME, "ytp-time-duration"),
            (By.CSS_SELECTOR, ".ytp-time-duration"),
            (By.CSS_SELECTOR, "span.ytp-time-duration"),
        ]
        
        for selector_type, selector_value in selectores_duracion:
            try:
                duracion_elemento = self.driver.find_element(selector_type, selector_value)
                if duracion_elemento and duracion_elemento.is_displayed():
                    duracion_str = duracion_elemento.text.strip()
                    if duracion_str and duracion_str != "0:00":
                        duracion_segundos = parsear_duracion_a_segundos(duracion_str)
                        if duracion_segundos > 0:
                            logging.info(f"✓ Duración obtenida: {duracion_str} ({duracion_segundos}s)")
                            return duracion_segundos
            except:
                continue
        
        return None
    
    def _obtener_duracion_por_javascript(self) -> Optional[int]:
        """Intenta obtener la duración usando JavaScript."""
        try:
            duracion_str = self.driver.execute_script("""
                var player = document.querySelector('video');
                if (player && player.duration && player.duration > 0) {
                    var duration = player.duration;
                    var hours = Math.floor(duration / 3600);
                    var minutes = Math.floor((duration % 3600) / 60);
                    var seconds = Math.floor(duration % 60);
                    if (hours > 0) {
                        return hours + ':' + (minutes < 10 ? '0' : '') + minutes + ':' + (seconds < 10 ? '0' : '') + seconds;
                    } else {
                        return minutes + ':' + (seconds < 10 ? '0' : '') + seconds;
                    }
                }
                return null;
            """)
            
            if duracion_str:
                duracion_segundos = parsear_duracion_a_segundos(duracion_str)
                if duracion_segundos > 0:
                    logging.info(f"✓ Duración obtenida con JavaScript: {duracion_str} ({duracion_segundos}s)")
                    return duracion_segundos
        except:
            pass
        
        return None

