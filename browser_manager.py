"""
Módulo para gestionar el navegador Brave y cargar URLs de videos.

Este módulo se encarga de:
- Conectar o abrir el navegador Brave
- Cargar URLs de YouTube
- Cerrar popups y anuncios
- Obtener información de los videos (título, duración)
- Controlar la reproducción de videos
"""

import os
import time
import logging
import platform
import socket
from pathlib import Path
from typing import Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import config

# Importar librerías para control de ventanas en Windows
WINDOWS_API_AVAILABLE = False
if platform.system() == "Windows":
    try:
        import win32gui
        import win32con
        import win32api
        WINDOWS_API_AVAILABLE = True
    except ImportError:
        WINDOWS_API_AVAILABLE = False


class BrowserManager:
    """
    Clase encargada de gestionar el navegador Brave y las interacciones con YouTube.
    
    Esta clase maneja toda la lógica relacionada con:
    - Conexión al navegador
    - Carga de URLs
    - Interacción con elementos de la página
    - Cierre de popups y anuncios
    """
    
    def __init__(self):
        """Inicializa el gestor del navegador."""
        self.driver: Optional[webdriver.Chrome] = None
        self.nombre_navegador = "Brave" if config.NAVEGADOR.lower() == "brave" else "Chrome"
    
    def inicializar_navegador(self) -> bool:
        """
        Inicializa y conecta al navegador Brave.
        
        Si USAR_NAVEGADOR_EXISTENTE es True, se conecta a una instancia existente.
        De lo contrario, abre una nueva ventana del navegador.
        
        Returns:
            bool: True si la inicialización fue exitosa, False en caso contrario.
        """
        logging.info("")
        logging.info("=" * 70)
        logging.info(f"VERIFICACIÓN: Iniciando navegador {self.nombre_navegador}...")
        logging.info("=" * 70)
        
        try:
            if config.USAR_NAVEGADOR_EXISTENTE:
                self.driver = self._conectar_a_navegador_existente()
            else:
                self.driver = self._abrir_nueva_ventana_navegador()
            
            if not self.driver:
                logging.error("ERROR CRÍTICO: No se pudo iniciar o conectar al navegador.")
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
            
            logging.info("=" * 70)
            return True
        
        except Exception as e:
            logging.error(f"ERROR CRÍTICO al inicializar navegador: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def _verificar_puerto_disponible(self, port: int) -> bool:
        """
        Verifica si un puerto está disponible/abierto.
        
        Args:
            port: Número de puerto a verificar.
        
        Returns:
            bool: True si el puerto está abierto, False en caso contrario.
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result == 0  # True si el puerto está abierto
        except Exception as e:
            logging.warning(f"Error al verificar puerto {port}: {e}")
            return False
    
    def _obtener_ruta_navegador(self) -> str:
        """
        Obtiene la ruta del ejecutable del navegador según la configuración.
        
        Returns:
            str: Ruta al ejecutable del navegador.
        """
        if config.NAVEGADOR.lower() == "brave":
            rutas_brave = [
                os.path.expanduser("~\\AppData\\Local\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"),
                "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
                "C:\\Program Files (x86)\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
            ]
            for ruta in rutas_brave:
                if os.path.exists(ruta):
                    return ruta
            return "brave.exe"  # Intentar desde PATH
        else:
            rutas_chrome = [
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
            ]
            for ruta in rutas_chrome:
                if os.path.exists(ruta):
                    return ruta
            return "chrome.exe"  # Intentar desde PATH
    
    def _abrir_brave_con_puerto_depuracion(self) -> bool:
        """
        Intenta abrir Brave automáticamente con el puerto de depuración habilitado.
        
        Returns:
            bool: True si se abrió correctamente, False en caso contrario.
        """
        import subprocess
        
        ruta_navegador = self._obtener_ruta_navegador()
        
        if not os.path.exists(ruta_navegador):
            logging.error(f"No se encontró {self.nombre_navegador} en: {ruta_navegador}")
            return False
        
        try:
            logging.info(f"Abriendo {self.nombre_navegador} con puerto de depuración...")
            # Abrir Brave con el puerto de depuración en segundo plano
            subprocess.Popen([
                ruta_navegador,
                f"--remote-debugging-port={config.DEBUG_PORT}",
                "--new-window"
            ], shell=False)
            
            # Esperar a que el puerto esté disponible
            logging.info(f"Esperando a que {self.nombre_navegador} inicie el puerto de depuración...")
            for intento in range(10):
                time.sleep(1)
                if self._verificar_puerto_disponible(config.DEBUG_PORT):
                    logging.info(f"✓ {self.nombre_navegador} iniciado correctamente con puerto de depuración")
                    return True
            
            logging.warning(f"{self.nombre_navegador} se abrió pero el puerto aún no está disponible")
            return False
        
        except Exception as e:
            logging.error(f"Error al abrir {self.nombre_navegador}: {e}")
            return False
    
    def _conectar_a_navegador_existente(self) -> Optional[webdriver.Chrome]:
        """
        Se conecta a una instancia existente del navegador.
        
        El navegador debe estar ejecutándose con --remote-debugging-port.
        Si no está abierto, intenta abrirlo automáticamente.
        
        Returns:
            webdriver.Chrome si la conexión fue exitosa, None en caso contrario.
        """
        logging.info(f"VERIFICACIÓN: Intentando conectarse a {self.nombre_navegador}...")
        
        # Verificar primero si el puerto está disponible
        if not self._verificar_puerto_disponible(config.DEBUG_PORT):
            logging.info("=" * 70)
            logging.info(f"El puerto {config.DEBUG_PORT} no está disponible")
            logging.info("=" * 70)
            logging.info("")
            logging.info(f"{self.nombre_navegador} no está abierto con el puerto de depuración habilitado.")
            logging.info("")
            logging.info(f"ACCION: Abriendo {self.nombre_navegador} automáticamente con el puerto de depuración...")
            logging.info("")
            
            # Intentar abrir Brave automáticamente
            if self._abrir_brave_con_puerto_depuracion():
                # Esperar un poco más para asegurar que esté listo
                time.sleep(3)
                logging.info(f"✓ {self.nombre_navegador} abierto correctamente")
            else:
                logging.error("=" * 70)
                logging.error(f"ERROR: No se pudo abrir {self.nombre_navegador} automáticamente")
                logging.error("=" * 70)
                logging.error("")
                logging.error("SOLUCIÓN MANUAL:")
                logging.error("")
                logging.error("1. Cierra TODAS las ventanas de Brave")
                logging.error("")
                logging.error("2. Abre PowerShell y ejecuta:")
                logging.error("")
                ruta_navegador = self._obtener_ruta_navegador()
                if os.path.exists(ruta_navegador):
                    logging.error(f'   & "{ruta_navegador}" --remote-debugging-port={config.DEBUG_PORT}')
                else:
                    nombre_exe = "brave.exe" if config.NAVEGADOR.lower() == "brave" else "chrome.exe"
                    logging.error(f'   {nombre_exe} --remote-debugging-port={config.DEBUG_PORT}')
                logging.error("")
                logging.error("3. Luego ejecuta este script nuevamente")
                logging.error("")
                logging.error("=" * 70)
                return None
        
        try:
            chrome_options = Options()
            # Conectar al navegador existente usando el puerto de depuración
            chrome_options.add_experimental_option("debuggerAddress", f"localhost:{config.DEBUG_PORT}")
            
            # No necesitamos Service ya que no vamos a iniciar el navegador
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            logging.info(f"✓ Conectado exitosamente a {self.nombre_navegador} existente (puerto {config.DEBUG_PORT})")
            logging.info(f"  Ventana actual: {driver.title}")
            logging.info(f"  URL actual: {driver.current_url}")
            
            return driver
        
        except WebDriverException as e:
            error_str = str(e)
            logging.error("=" * 70)
            logging.error(f"ERROR: No se pudo conectar a {self.nombre_navegador} existente")
            logging.error("=" * 70)
            logging.error("")
            
            if "cannot connect to chrome" in error_str.lower() or "not reachable" in error_str.lower():
                logging.error(f"El puerto {config.DEBUG_PORT} está abierto pero {self.nombre_navegador} no responde.")
                logging.error("")
                logging.error("POSIBLES CAUSAS:")
                logging.error("  1. Brave está abierto pero NO con --remote-debugging-port")
                logging.error("  2. Hay múltiples instancias de Brave abiertas")
                logging.error("  3. El puerto está siendo usado por otra aplicación")
            else:
                logging.error(f"Error inesperado al conectar con {self.nombre_navegador}.")
            
            logging.error(f"Error técnico: {e}")
            return None
        except Exception as e:
            logging.error(f"ERROR inesperado al conectar al navegador: {e}")
            return None
    
    def _abrir_nueva_ventana_navegador(self) -> Optional[webdriver.Chrome]:
        """
        Abre una nueva ventana del navegador (Chrome o Brave).
        
        Returns:
            webdriver.Chrome si se abrió correctamente, None en caso contrario.
        """
        logging.info(f"Abriendo nueva ventana de {self.nombre_navegador}...")
        try:
            chrome_options = Options()
            
            # Si es Brave, especificar la ruta del ejecutable
            if config.NAVEGADOR.lower() == "brave":
                ruta_brave = self._obtener_ruta_navegador()
                if os.path.exists(ruta_brave):
                    chrome_options.binary_location = ruta_brave
                    logging.info(f"Usando Brave en: {ruta_brave}")
                else:
                    logging.warning(f"No se encontró Brave en las rutas comunes. Intentando desde PATH...")
            
            # NO usar headless - la ventana debe ser visible para OBS
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Deshabilitar notificaciones y popups
            prefs = {
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_settings.popups": 0,
                "profile.managed_default_content_settings.images": 1,
                "profile.default_content_setting_values.media_stream": 1,
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Esperar un momento para que la ventana se cree
            time.sleep(2)
            
            # Maximizar la ventana
            driver.maximize_window()
            
            # Navegar a una página de prueba
            try:
                driver.get("about:blank")
                time.sleep(1)
            except:
                pass
            
            logging.info(f"✓ {self.nombre_navegador} iniciado correctamente")
            return driver
        
        except WebDriverException as e:
            logging.error(f"Error al iniciar {self.nombre_navegador}. ¿Está instalado? Error: {e}")
            return None
        except Exception as e:
            logging.error(f"ERROR inesperado al abrir navegador: {e}")
            return None
    
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
            logging.info("")
            logging.info("=" * 70)
            logging.info("VERIFICACIÓN: Cargando video en navegador...")
            logging.info("=" * 70)
            logging.info(f"URL: {url}")
            
            # Obtener ventanas antes de abrir nueva pestaña
            try:
                ventanas_antes = self.driver.window_handles
                logging.info(f"Ventanas abiertas antes: {len(ventanas_antes)}")
            except:
                logging.error("Error al obtener ventanas. Reintentando conexión...")
                if not self.inicializar_navegador():
                    return False
                ventanas_antes = self.driver.window_handles
            
            # Intentar abrir en nueva pestaña
            try:
                self.driver.execute_script(f"window.open('{url}', '_blank');")
                time.sleep(2)
                
                # Verificar que se creó una nueva pestaña
                ventanas_despues = self.driver.window_handles
                logging.info(f"Ventanas antes: {len(ventanas_antes)}, después: {len(ventanas_despues)}")
                
                if len(ventanas_despues) > len(ventanas_antes):
                    nueva_ventana = [w for w in ventanas_despues if w not in ventanas_antes][0]
                    self.driver.switch_to.window(nueva_ventana)
                    logging.info("✓ Nueva pestaña creada y activada")
                elif len(ventanas_despues) > 0:
                    self.driver.switch_to.window(ventanas_despues[-1])
                    logging.info("✓ Usando última pestaña disponible")
                else:
                    logging.warning("No se pudo abrir nueva pestaña. Usando driver.get()...")
                    self.driver.get(url)
            except Exception as e:
                logging.warning(f"Error al abrir nueva pestaña: {e}")
                logging.info("Intentando con driver.get() directamente...")
                self.driver.get(url)
            
            # Esperar a que la página cargue completamente
            wait = WebDriverWait(self.driver, 30)
            try:
                wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
                logging.info("✓ Página cargada completamente (readyState = complete)")
            except TimeoutException:
                logging.error("ERROR: Timeout esperando carga completa de la página")
                return False
            
            # Verificar que estamos en YouTube
            url_actual = self.driver.current_url
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
    
    def obtener_info_video(self) -> Tuple[Optional[str], Optional[int]]:
        """
        Obtiene el título y la duración del video actual en YouTube.
        
        Returns:
            Tupla (titulo, duracion_segundos). Si hay error, retorna (None, None).
        """
        if not self.driver:
            logging.error("ERROR: El navegador no está inicializado")
            return None, None
        
        try:
            wait = WebDriverWait(self.driver, 30)
            
            # Asegurar que estamos en la ventana correcta
            self.driver.switch_to.window(self.driver.current_window_handle)
            time.sleep(2)
            
            # Cerrar popups iniciales (solo si existen, modo silencioso)
            self.cerrar_popups_youtube(max_intentos=3, silencioso=True)
            time.sleep(2)
            
            # Esperar a que el reproductor de video esté presente
            logging.info("Esperando a que el reproductor de video cargue...")
            try:
                # Esperar a que el reproductor esté presente
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "html5-video-player")))
                logging.info("✓ Reproductor de video detectado")
            except TimeoutException:
                logging.warning("No se detectó el reproductor HTML5, continuando de todas formas...")
            
            # Esperar un poco más para que el reproductor se inicialice completamente
            time.sleep(3)
            
            # Intentar múltiples selectores para el título
            titulo_video = None
            selectores_titulo = [
                "h1.ytd-watch-metadata yt-formatted-string",
                "h1.style-scope.ytd-watch-metadata",
                "h1.ytd-video-primary-info-renderer",
                ".ytd-watch-metadata h1",
                "h1.ytd-watch-metadata",
                "ytd-watch-metadata h1",
                "h1.title"
            ]
            
            logging.info("Obteniendo título del video...")
            for selector in selectores_titulo:
                try:
                    titulo_elemento = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    titulo_video = titulo_elemento.text.strip()
                    if titulo_video:
                        logging.info(f"✓ Título obtenido con selector: {selector[:50]}...")
                        break
                except:
                    continue
            
            if not titulo_video:
                logging.warning(f"No se pudo obtener el título del video con ningún selector. Intentando método alternativo...")
                # Intentar obtener el título desde el meta tag o la URL
                try:
                    titulo_video = self.driver.title.replace(" - YouTube", "").strip()
                    if titulo_video and len(titulo_video) > 0:
                        logging.info(f"✓ Título obtenido desde el título de la página: {titulo_video[:50]}...")
                    else:
                        titulo_video = "video_sin_titulo"
                except:
                    titulo_video = "video_sin_titulo"
            
            logging.info(f"Título final: {titulo_video}")
            
            # Obtener duración - esperar a que el reproductor esté listo
            logging.info("Obteniendo duración del video...")
            duracion_str = None
            selectores_duracion = [
                (By.CLASS_NAME, "ytp-time-duration"),
                (By.CSS_SELECTOR, ".ytp-time-duration"),
                (By.CSS_SELECTOR, "span.ytp-time-duration"),
                (By.CSS_SELECTOR, ".ytp-time-display span"),
            ]
            
            # Esperar más tiempo para que la duración esté disponible
            for intento in range(10):
                for selector_type, selector_value in selectores_duracion:
                    try:
                        if selector_type == By.CLASS_NAME:
                            duracion_elemento = self.driver.find_element(selector_type, selector_value)
                        else:
                            duracion_elemento = self.driver.find_element(selector_type, selector_value)
                        
                        if duracion_elemento and duracion_elemento.is_displayed():
                            duracion_str = duracion_elemento.text.strip()
                            if duracion_str and duracion_str != "0:00":
                                logging.info(f"✓ Duración obtenida: {duracion_str}")
                                break
                    except:
                        continue
                
                if duracion_str and duracion_str != "0:00":
                    break
                
                # Si no se encontró, esperar un poco más
                if intento < 9:
                    time.sleep(1)
                    logging.info(f"Esperando duración del video... (intento {intento + 1}/10)")
            
            # Si aún no se encontró, intentar método alternativo con JavaScript
            if not duracion_str or duracion_str == "0:00":
                logging.warning("No se pudo obtener la duración con selectores. Intentando con JavaScript...")
                try:
                    # Intentar obtener la duración desde el objeto del reproductor
                    duracion_str = self.driver.execute_script("""
                        var player = document.querySelector('video');
                        if (player && player.duration) {
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
                        logging.info(f"✓ Duración obtenida con JavaScript: {duracion_str}")
                except Exception as e:
                    logging.warning(f"No se pudo obtener la duración con JavaScript: {e}")
            
            # Si aún no hay duración, usar valor por defecto
            if not duracion_str or duracion_str == "0:00":
                logging.warning(f"No se pudo obtener la duración. Usando valor por defecto.")
                duracion_str = "0:00"
            
            from utils import parsear_duracion_a_segundos
            duracion_segundos = parsear_duracion_a_segundos(duracion_str)
            
            if duracion_segundos == 0:
                logging.error(f"ERROR: La duración parseada es 0. String original: '{duracion_str}'")
            else:
                logging.info(f"Duración detectada: {duracion_str} ({duracion_segundos} segundos)")
            
            return titulo_video, duracion_segundos
        
        except Exception as e:
            logging.error(f"ERROR al obtener información del video: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            return None, None
    
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
        
        from utils import parsear_duracion_a_segundos
        
        inicio = time.time()
        intento = 0
        
        while (time.time() - inicio) < max_segundos_espera:
            intento += 1
            
            # Método 1: Intentar con selectores CSS
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
                                logging.info(f"✓ Duración obtenida (intento {intento}): {duracion_str} ({duracion_segundos}s)")
                                return duracion_segundos
                except:
                    continue
            
            # Método 2: Intentar con JavaScript desde el elemento video
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
                        logging.info(f"✓ Duración obtenida con JavaScript (intento {intento}): {duracion_str} ({duracion_segundos}s)")
                        return duracion_segundos
            except:
                pass
            
            # Esperar un poco antes del siguiente intento
            if (time.time() - inicio) < max_segundos_espera - 1:
                time.sleep(1)
                if intento % 3 == 0:  # Log cada 3 intentos para no saturar
                    logging.info(f"Intentando obtener duración... (intento {intento}, ya llevan {(int(time.time() - inicio))}s)")
        
        logging.warning(f"No se pudo obtener la duración después de {max_segundos_espera} segundos")
        return None
    
    def configurar_pantalla_completa(self) -> bool:
        """
        Configura el video en pantalla completa presionando la tecla F.
        
        Espera a que el reproductor esté completamente inicializado y el video
        esté reproduciéndose antes de activar pantalla completa.
        
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
                time.sleep(0.3)
            except:
                pass
            
            # Esperar a que el reproductor esté completamente cargado e inicializado
            wait = WebDriverWait(self.driver, 20)
            
            logging.info("Esperando a que el reproductor esté completamente listo...")
            
            # Esperar a que el reproductor de video esté presente
            try:
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "html5-video-player")))
                logging.info("✓ Reproductor HTML5 detectado")
            except:
                logging.warning("Reproductor HTML5 no detectado, continuando de todas formas...")
            
            # Esperar a que el reproductor de YouTube (#movie_player) esté presente
            try:
                wait.until(EC.presence_of_element_located((By.ID, "movie_player")))
                logging.info("✓ Reproductor de YouTube detectado")
            except:
                logging.warning("Reproductor de YouTube no detectado, continuando de todas formas...")
            
            # Esperar a que el video esté cargado y listo
            video_listo = False
            for intento in range(10):
                try:
                    estado_video = self.driver.execute_script("""
                        var video = document.querySelector('video');
                        if (video) {
                            return {
                                ready: video.readyState >= 2, // HAVE_CURRENT_DATA o superior
                                hasDuration: video.duration > 0,
                                playerReady: document.querySelector('#movie_player') !== null
                            };
                        }
                        return {ready: false, hasDuration: false, playerReady: false};
                    """)
                    
                    if estado_video.get('ready') and estado_video.get('playerReady'):
                        video_listo = True
                        logging.info("✓ Video listo para pantalla completa")
                        break
                except:
                    pass
                
                if intento < 9:
                    time.sleep(0.5)
            
            # Esperar un poco más para asegurar que todo esté completamente inicializado
            time.sleep(1)
            
            # Verificar si YA está en pantalla completa
            ya_en_fullscreen = self.driver.execute_script("""
                return !!(document.fullscreenElement || 
                         document.webkitFullscreenElement || 
                         document.mozFullScreenElement || 
                         document.msFullscreenElement);
            """)
            
            if ya_en_fullscreen:
                logging.info("✓ El video ya está en pantalla completa")
                return True
            
            # Activar pantalla completa presionando la tecla F
            logging.info("Activando pantalla completa presionando la tecla F...")
            
            try:
                # Obtener el body o el elemento del reproductor para enviar la tecla
                body = self.driver.find_element(By.TAG_NAME, "body")
                body.send_keys("f")
                time.sleep(1.5)
                
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
            import traceback
            logging.debug(f"Traceback: {traceback.format_exc()}")
            return False
    
    def salir_pantalla_completa(self) -> None:
        """
        Sale de pantalla completa antes de cerrar la pestaña.
        
        Asegura que el navegador no quede en pantalla completa al cambiar de video.
        """
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
            
            # Esperar un momento para que el video comience
            time.sleep(2)
            
            # Cerrar popups y anuncios (modo silencioso, sin interferir)
            self.cerrar_popups_youtube(max_intentos=2, silencioso=True)
            self.intentar_omitir_anuncios(max_intentos=2)
            
            logging.info("✓ Video configurado para reproducir")
            return True
        
        except Exception as e:
            logging.error(f"ERROR al reproducir video: {e}")
            return False
    
    def cerrar_popups_youtube(self, max_intentos: int = 5, silencioso: bool = False) -> bool:
        """
        Cierra todos los tipos de popups, banners y anuncios de YouTube.
        
        Args:
            max_intentos: Número máximo de intentos para cerrar popups.
            silencioso: Si es True, no muestra mensajes a menos que cierre popups.
        
        Returns:
            bool: True si se cerraron popups, False en caso contrario.
        """
        if not self.driver:
            return False
        
        popups_cerrados = 0
        
        # Lista exhaustiva de selectores para diferentes tipos de popups
        selectores_popups = [
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
        
        for intento in range(max_intentos):
            popups_encontrados = False
            
            for selector in selectores_popups:
                try:
                    elementos = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elemento in elementos:
                        try:
                            if elemento.is_displayed() and elemento.is_enabled():
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", elemento)
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
                                self.driver.execute_script("arguments[0].click();", elemento)
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
            # Solo mostrar si no está en modo silencioso y no se cerró nada
            logging.debug("No se encontraron popups para cerrar")
        
        return popups_cerrados > 0
    
    def intentar_omitir_anuncios(self, max_intentos: int = 10) -> bool:
        """
        Intenta omitir anuncios de YouTube si están presentes.
        
        Args:
            max_intentos: Número máximo de intentos.
        
        Returns:
            bool: True si se omitió un anuncio, False en caso contrario.
        """
        if not self.driver:
            return False
        
        for intento in range(max_intentos):
            try:
                selectores_skip = [
                    "button.ytp-ad-skip-button",
                    ".ytp-ad-skip-button",
                    "button[aria-label*='Omitir']",
                    "button[aria-label*='Skip']",
                    ".ytp-ad-overlay-close-button",
                    "button.ytp-ad-skip-button-modern"
                ]
                
                for selector in selectores_skip:
                    try:
                        boton_skip = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if boton_skip.is_displayed():
                            try:
                                boton_skip.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", boton_skip)
                            logging.info("Anuncio omitido exitosamente")
                            time.sleep(1)
                            return True
                    except:
                        continue
                
                # Verificar si aún hay un anuncio activo
                try:
                    self.driver.find_element(By.CLASS_NAME, "ytp-ad-module")
                    time.sleep(0.5)
                except:
                    break
                    
            except:
                pass
            
            time.sleep(0.5)
        
        return False
    
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
                self.cerrar_popups_youtube(max_intentos=1)
                self.intentar_omitir_anuncios(max_intentos=2)
    
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
    
    def _obtener_handle_ventana(self):
        """Obtiene el handle de la ventana de Windows para el navegador."""
        if not WINDOWS_API_AVAILABLE:
            return None
        
        try:
            titulo_ventana = self.driver.title if self.driver.title else ""
            nombre_buscar = "brave" if config.NAVEGADOR.lower() == "brave" else "chrome"
            
            windows_found = []
            
            def callback(hwnd, extra):
                if win32gui.IsWindowVisible(hwnd):
                    window_title = win32gui.GetWindowText(hwnd)
                    if nombre_buscar in window_title.lower() or "google chrome" in window_title.lower():
                        if win32gui.GetParent(hwnd) == 0:
                            windows_found.append(hwnd)
                return True
            
            win32gui.EnumWindows(callback, None)
            
            if windows_found:
                for hwnd in windows_found:
                    window_title = win32gui.GetWindowText(hwnd)
                    if titulo_ventana and titulo_ventana.lower() in window_title.lower():
                        return hwnd
                return windows_found[0]
            
            return None
        except Exception as e:
            logging.warning(f"No se pudo obtener el handle de la ventana: {e}")
            return None
    
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

