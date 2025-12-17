"""
Módulo para gestionar el navegador Brave y cargar URLs de videos.

Este módulo se encarga de:
- Conectar o abrir el navegador Brave
- Cargar URLs de YouTube
- Delegar controles e información a módulos especializados
"""

import time
import logging
from typing import Optional
from selenium import webdriver
import config
from browser_info import BrowserInfo
from browser_controls import BrowserControls
from browser_connection import conectar_a_navegador_existente
from browser_url_loader import cargar_url_en_navegador


class BrowserManager:
    """
    Clase encargada de gestionar el navegador Brave y las interacciones con YouTube.
    
    Esta clase maneja la conexión al navegador y la carga de URLs.
    Delega las operaciones de control e información a módulos especializados.
    """
    
    def __init__(self):
        """Inicializa el gestor del navegador."""
        self.driver: Optional[webdriver.Chrome] = None
        self.nombre_navegador = "Brave" if config.NAVEGADOR.lower() == "brave" else "Chrome"
        self.browser_info: Optional[BrowserInfo] = None
        self.browser_controls: Optional[BrowserControls] = None
    
    def inicializar_navegador(self) -> bool:
        """
        Conecta al navegador existente que debe estar abierto con --remote-debugging-port.
        
        Returns:
            bool: True si la conexión fue exitosa, False en caso contrario.
        """
        logging.info("")
        logging.info("=" * 70)
        logging.info(f"VERIFICACIÓN: Conectando a navegador {self.nombre_navegador}...")
        logging.info("=" * 70)
        
        try:
            # Conectar a navegador existente
            self.driver = conectar_a_navegador_existente(self.nombre_navegador)
            
            if not self.driver:
                logging.error("ERROR CRÍTICO: No se pudo conectar al navegador.")
                return False
            
            # Verificar que el navegador está funcionando
            try:
                self.driver.current_url
                logging.info("✓ Navegador conectado y funcionando")
                logging.info(f"  - URL actual: {self.driver.current_url}")
                logging.info(f"  - Título: {self.driver.title}")
                logging.info(f"  - Ventanas abiertas: {len(self.driver.window_handles)}")
            except Exception as e:
                logging.error(f"ERROR CRÍTICO: El navegador no responde: {e}")
                return False
            
            # Inicializar módulos especializados
            self.browser_info = BrowserInfo(self.driver)
            self.browser_controls = BrowserControls(self.driver)
            
            logging.info("=" * 70)
            return True
        
        except Exception as e:
            logging.error(f"ERROR CRÍTICO al inicializar navegador: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def cargar_url(self, url: str) -> bool:
        """
        Carga una URL en el navegador.
        
        Args:
            url: La URL a cargar.
        
        Returns:
            bool: True si la carga fue exitosa, False en caso contrario.
        """
        if not self.driver:
            logging.error("ERROR: El navegador no está inicializado")
            return False
        
        try:
            # Reintentar conexión si hay problemas
            try:
                self.driver.window_handles
            except:
                logging.error("Error al obtener ventanas. Reintentando conexión...")
                if not self.inicializar_navegador():
                    return False
            
            return cargar_url_en_navegador(self.driver, url)
        
        except Exception as e:
            logging.error(f"ERROR al cargar URL: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def cerrar_pestaña_actual(self) -> bool:
        """
        Cierra la pestaña actual del navegador.
        
        Returns:
            bool: True si se cerró correctamente, False en caso contrario.
        """
        if not self.driver:
            return False
        
        try:
            ventanas_actuales = self.driver.window_handles
            logging.info(f"Cerrando pestaña actual. Pestañas restantes: {len(ventanas_actuales)}")
            
            self.driver.close()
            time.sleep(1)
            
            # Cambiar a otra pestaña si existe
            ventanas_restantes = self.driver.window_handles
            if ventanas_restantes:
                self.driver.switch_to.window(ventanas_restantes[0])
                logging.info(f"✓ Cambiado a pestaña restante. Total: {len(ventanas_restantes)}")
            else:
                logging.info("No hay pestañas restantes. Se abrirá una nueva en el siguiente video.")
            
            return True
        
        except Exception as e:
            logging.warning(f"Error al cerrar pestaña: {e}")
            # Intentar recuperar el control
            try:
                ventanas = self.driver.window_handles
                if ventanas:
                    self.driver.switch_to.window(ventanas[0])
                    logging.info("✓ Control recuperado")
            except:
                pass
            return False
    
    def cerrar_navegador(self) -> None:
        """Cierra el navegador completamente."""
        if self.driver:
            try:
                self.driver.quit()
                logging.info(f"✓ {self.nombre_navegador} cerrado correctamente")
            except Exception as e:
                logging.warning(f"Error al cerrar navegador: {e}")
            finally:
                self.driver = None
                self.browser_info = None
                self.browser_controls = None
    
    # Métodos delegados a BrowserInfo
    def obtener_titulo_video(self) -> Optional[str]:
        """Obtiene el título del video. Delega a BrowserInfo."""
        if self.browser_info:
            return self.browser_info.obtener_titulo_video()
        return None
    
    def obtener_duracion_video_continuo(self, max_segundos_espera: int = 30) -> Optional[int]:
        """Obtiene la duración del video. Delega a BrowserInfo."""
        if self.browser_info:
            return self.browser_info.obtener_duracion_video_continuo(max_segundos_espera)
        return None
    
    # Métodos delegados a BrowserControls
    def reproducir_video(self) -> bool:
        """Reproduce el video. Delega a BrowserControls."""
        if self.browser_controls:
            return self.browser_controls.reproducir_video()
        return False
    
    def configurar_pantalla_completa(self) -> bool:
        """Configura pantalla completa. Delega a BrowserControls."""
        if self.browser_controls:
            return self.browser_controls.configurar_pantalla_completa()
        return False
    
    def salir_pantalla_completa(self) -> None:
        """Sale de pantalla completa. Delega a BrowserControls."""
        if self.browser_controls:
            self.browser_controls.salir_pantalla_completa()
    
    def monitorear_reproduccion(self, duracion_segundos: int, intervalo: int = 2) -> None:
        """Monitorea la reproducción. Delega a BrowserControls."""
        if self.browser_controls:
            self.browser_controls.monitorear_reproduccion(duracion_segundos, intervalo)
