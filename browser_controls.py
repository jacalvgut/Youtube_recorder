"""
Módulo para controlar la reproducción y visualización de videos.

Este módulo se encarga de:
- Reproducir videos
- Configurar pantalla completa
- Cerrar popups y anuncios
- Monitorear reproducción
"""

import time
import logging
from selenium.webdriver.common.by import By
from browser_popups import cerrar_popups_youtube, intentar_omitir_anuncios


class BrowserControls:
    """
    Clase encargada de controlar la reproducción y visualización de videos.
    
    Maneja la interacción con el reproductor de YouTube.
    """
    
    def __init__(self, driver):
        """
        Inicializa el controlador del navegador.
        
        Args:
            driver: Instancia de WebDriver de Selenium.
        """
        self.driver = driver
    
    def reproducir_video(self) -> bool:
        """
        Reproduce el video actual en YouTube SIN cambiar el foco ni traer la ventana al frente.
        
        OBS ya tiene la ventana seleccionada, no necesitamos interferir con el foco.
        Usa JavaScript para reproducir sin interrupciones.
        
        Returns:
            bool: True si la reproducción se inició correctamente, False en caso contrario.
        """
        if not self.driver:
            logging.error("ERROR: El navegador no está inicializado")
            return False
        
        try:
            logging.info("Iniciando reproducción del video...")
            
            # Asegurar que estamos en la ventana correcta (sin cambiar foco)
            self.driver.switch_to.window(self.driver.current_window_handle)
            
            # Hacer scroll al inicio suavemente
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.2)
            
            # Reproducir usando JavaScript directamente (no cambia foco)
            try:
                self.driver.execute_script("""
                    // Intentar reproducir el video directamente
                    var video = document.querySelector('video');
                    if (video) {
                        video.play().catch(function(e) {
                            console.log('Error al reproducir video:', e);
                        });
                    }
                    
                    // También intentar con el botón de play
                    var playButton = document.querySelector('.ytp-play-button');
                    if (playButton) {
                        var ariaLabel = playButton.getAttribute('aria-label') || '';
                        if (ariaLabel.toLowerCase().includes('play') || 
                            ariaLabel.toLowerCase().includes('reproducir')) {
                            playButton.click();
                        }
                    }
                """)
                logging.info("✓ Comando de reproducción enviado")
            except Exception as e:
                logging.warning(f"Error al enviar comando de reproducción: {e}")
            
            # Esperar un momento breve para que el video comience
            time.sleep(0.3)
            
            # Cerrar popups y anuncios (modo silencioso, sin interferir)
            cerrar_popups_youtube(self.driver, max_intentos=1, silencioso=True)
            intentar_omitir_anuncios(self.driver, max_intentos=1)
            
            logging.info("✓ Video configurado para reproducir")
            return True
        
        except Exception as e:
            logging.error(f"ERROR al reproducir video: {e}")
            return False
    
    def configurar_pantalla_completa(self) -> bool:
        """
        Configura el video en pantalla completa presionando la tecla F.
        
        Returns:
            bool: True si se configuró correctamente, False en caso contrario.
        """
        if not self.driver:
            logging.error("ERROR: El navegador no está inicializado")
            return False
        
        try:
            # Maximizar la ventana primero
            try:
                self.driver.maximize_window()
            except:
                pass
            
            # Verificar si YA está en pantalla completa
            try:
                ya_en_fullscreen = self.driver.execute_script("""
                    return !!(document.fullscreenElement || 
                             document.webkitFullscreenElement || 
                             document.mozFullScreenElement || 
                             document.msFullscreenElement);
                """)
                
                if ya_en_fullscreen:
                    logging.info("✓ El video ya está en pantalla completa")
                    return True
            except:
                pass
            
            # Activar pantalla completa presionando la tecla F
            logging.info("Activando pantalla completa presionando la tecla F...")
            
            try:
                body = self.driver.find_element(By.TAG_NAME, "body")
                body.send_keys("f")
                time.sleep(0.1)
                
                # Verificar que realmente entró en pantalla completa
                en_fullscreen = self.driver.execute_script("""
                    return !!(document.fullscreenElement || 
                             document.webkitFullscreenElement || 
                             document.mozFullScreenElement || 
                             document.msFullscreenElement);
                """)
                
                if en_fullscreen:
                    logging.info("✓ Pantalla completa activada correctamente con la tecla F")
                    return True
                else:
                    logging.warning("La tecla F fue presionada pero no se activó pantalla completa")
                    return False
                    
            except Exception as e:
                logging.error(f"ERROR al presionar la tecla F: {e}")
                return False
        
        except Exception as e:
            logging.error(f"ERROR al configurar pantalla completa: {e}")
            return False
    
    def salir_pantalla_completa(self) -> None:
        """Sale de pantalla completa antes de cerrar la pestaña."""
        if not self.driver:
            return
        
        try:
            # Verificar si está en pantalla completa
            en_fullscreen = self.driver.execute_script("""
                return !!(document.fullscreenElement || 
                         document.webkitFullscreenElement || 
                         document.mozFullScreenElement || 
                         document.msFullscreenElement);
            """)
            
            if en_fullscreen:
                # Salir de pantalla completa
                self.driver.execute_script("""
                    if (document.exitFullscreen) {
                        document.exitFullscreen();
                    } else if (document.webkitExitFullscreen) {
                        document.webkitExitFullscreen();
                    } else if (document.mozCancelFullScreen) {
                        document.mozCancelFullScreen();
                    } else if (document.msExitFullscreen) {
                        document.msExitFullscreen();
                    }
                """)
                time.sleep(0.3)
                logging.debug("Salido de pantalla completa")
        except:
            pass  # Si falla, no es crítico
    
    def monitorear_reproduccion(self, duracion_segundos: int, intervalo: int = 2) -> None:
        """
        Monitorea la reproducción del video y cierra popups periódicamente.
        
        Args:
            duracion_segundos: Duración total del video en segundos.
            intervalo: Intervalo en segundos entre verificaciones.
        """
        if not self.driver:
            return
        
        tiempo_transcurrido = 0
        
        while tiempo_transcurrido < duracion_segundos:
            tiempo_restante = duracion_segundos - tiempo_transcurrido
            tiempo_dormir = min(intervalo, tiempo_restante)
            time.sleep(tiempo_dormir)
            tiempo_transcurrido += tiempo_dormir
            
            # Intentar cerrar popups y omitir anuncios periódicamente
            if tiempo_transcurrido % 5 == 0:  # Cada 5 segundos
                cerrar_popups_youtube(self.driver, max_intentos=1)
                intentar_omitir_anuncios(self.driver, max_intentos=2)

