"""
Módulo para procesar videos individuales.

Este módulo se encarga de:
- Coordinar la grabación de un video individual
- Gestionar el flujo completo de grabación
- Manejar errores durante la grabación
"""

import time
import logging
from pathlib import Path
from typing import Optional
from selenium.common.exceptions import TimeoutException
import config
from browser_manager import BrowserManager
from obs_manager import OBSManager
from file_manager import FileManager


class VideoProcessor:
    """
    Clase encargada de procesar videos individuales.
    
    Coordina el flujo completo de grabación de un video:
    1. Configurar directorio de grabación
    2. Iniciar grabación
    3. Cargar y reproducir video
    4. Monitorear reproducción
    5. Detener grabación
    6. Gestionar archivo grabado
    """
    
    def __init__(
        self,
        browser_manager: BrowserManager,
        obs_manager: OBSManager,
        file_manager: FileManager
    ):
        """
        Inicializa el procesador de videos.
        
        Args:
            browser_manager: Gestor del navegador.
            obs_manager: Gestor de OBS.
            file_manager: Gestor de archivos.
        """
        self.browser_manager = browser_manager
        self.obs_manager = obs_manager
        self.file_manager = file_manager
    
    def procesar_video(
        self,
        url: str,
        ruta_modulo: Path,
        nombre_modulo: str,
        numero_video: int,
        indice_lista: int,
        total_videos: int
    ) -> bool:
        """
        Procesa un video completo desde la URL hasta el archivo final.
        
        Args:
            url: URL del video de YouTube.
            ruta_modulo: Carpeta del módulo donde guardar.
            nombre_modulo: Nombre del módulo.
            numero_video: Número del video para el nombre del archivo.
            indice_lista: Índice del video en la lista (para logging).
            total_videos: Total de videos en el módulo.
        
        Returns:
            bool: True si se procesó correctamente, False en caso contrario.
        """
        try:
            logging.info("")
            logging.info("=" * 70)
            logging.info(f"Procesando video {indice_lista}/{total_videos}: {url}")
            logging.info("=" * 70)
            
            # PASO 0: Configurar directorio de grabación
            if not self._configurar_directorio(ruta_modulo, nombre_modulo):
                return False
            
            # PASO 1: Iniciar grabación
            if not self._iniciar_grabacion():
                return False
            
            # PASO 2: Esperar margen inicial
            self._esperar_margen_inicial()
            
            # PASO 3: Cargar URL en navegador
            if not self._cargar_url(url):
                self.obs_manager.detener_grabacion()
                return False
            
            # PASO 4: Reproducir video
            self._reproducir_video()
            
            # PASO 5: Configurar pantalla completa
            self._configurar_pantalla_completa()
            
            # PASO 6: Obtener información del video
            titulo_video, duracion_segundos = self._obtener_informacion_video()
            
            # PASO 7: Monitorear reproducción
            self._monitorear_reproduccion(duracion_segundos)
            
            # PASO 8: Esperar margen final
            self._esperar_margen_final()
            
            # PASO 9: Detener grabación y gestionar archivo
            if not self._finalizar_grabacion(
                ruta_modulo, titulo_video, numero_video, duracion_segundos, indice_lista, total_videos
            ):
                return False
            
            # Limpieza antes del siguiente video
            self._limpiar_antes_siguiente_video()
            
            logging.info("=" * 70)
            logging.info(f"✓ Video {indice_lista}/{total_videos} completado")
            logging.info("=" * 70)
            logging.info("")
            
            return True
        
        except TimeoutException as e:
            logging.error(f"Tiempo de espera agotado al cargar el video {url}")
            logging.error(f"Puede ser un video privado, eliminado o la conexión es lenta.")
            logging.error(f"Error: {e}")
            self.obs_manager.asegurar_grabacion_detenida()
            return False
        
        except Exception as e:
            logging.error(f"Ocurrió un error inesperado al procesar {url}: {e}")
            logging.error(f"Tipo de error: {type(e).__name__}")
            import traceback
            logging.error(f"Traceback completo:\n{traceback.format_exc()}")
            self.obs_manager.asegurar_grabacion_detenida()
            return False
    
    def _configurar_directorio(self, ruta_modulo: Path, nombre_modulo: str) -> bool:
        """Configura el directorio de grabación en OBS."""
        logging.info("")
        logging.info("=" * 70)
        logging.info("PASO 0: CONFIGURANDO DIRECTORIO DE GRABACIÓN")
        logging.info("=" * 70)
        
        if not self.obs_manager.configurar_directorio_grabacion(ruta_modulo):
            logging.error(f"ERROR CRÍTICO: No se pudo configurar directorio en OBS para '{nombre_modulo}'")
            return False
        return True
    
    def _iniciar_grabacion(self) -> bool:
        """Inicia la grabación en OBS."""
        logging.info("")
        logging.info("=" * 70)
        logging.info("PASO 1: INICIANDO GRABACIÓN EN OBS")
        logging.info("=" * 70)
        
        if not self.obs_manager.iniciar_grabacion():
            logging.error("ERROR: No se pudo iniciar la grabación. Saltando video...")
            return False
        return True
    
    def _esperar_margen_inicial(self) -> None:
        """Espera el margen inicial mientras ya está grabando."""
        logging.info("")
        logging.info("=" * 70)
        logging.info("PASO 2: ESPERANDO MARGEN INICIAL (grabación activa)")
        logging.info("=" * 70)
        
        margen_inicial = config.MARGEN_INICIAL_PRUEBA if config.MODO_PRUEBA else config.MARGEN_INICIAL
        if margen_inicial > 0:
            logging.info(f"Esperando {margen_inicial} segundos de margen inicial (ya está grabando)...")
            time.sleep(margen_inicial)
    
    def _cargar_url(self, url: str) -> bool:
        """Carga la URL en el navegador."""
        logging.info("")
        logging.info("=" * 70)
        logging.info("PASO 3: CARGANDO VIDEO EN NAVEGADOR")
        logging.info("=" * 70)
        
        if not self.browser_manager.cargar_url(url):
            logging.error(f"ERROR: No se pudo cargar la URL. Deteniendo grabación y saltando video...")
            return False
        return True
    
    def _reproducir_video(self) -> None:
        """Reproduce el video."""
        logging.info("")
        logging.info("=" * 70)
        logging.info("PASO 4: REPRODUCIENDO VIDEO")
        logging.info("=" * 70)
        
        if not self.browser_manager.reproducir_video():
            logging.warning("No se pudo reproducir el video. Continuando de todas formas...")
    
    def _configurar_pantalla_completa(self) -> None:
        """Configura pantalla completa."""
        logging.info("")
        logging.info("=" * 70)
        logging.info("PASO 5: CONFIGURANDO PANTALLA COMPLETA")
        logging.info("=" * 70)
        
        if not self.browser_manager.configurar_pantalla_completa():
            logging.warning("No se pudo configurar pantalla completa. Continuando de todas formas...")
    
    def _obtener_informacion_video(self) -> tuple:
        """Obtiene información del video (título y duración)."""
        logging.info("")
        logging.info("=" * 70)
        logging.info("PASO 6: OBTENIENDO INFORMACIÓN DEL VIDEO (grabación activa)")
        logging.info("=" * 70)
        
        # Obtener título
        titulo_video = self.browser_manager.obtener_titulo_video()
        if not titulo_video:
            logging.warning("No se pudo obtener el título. Usando nombre por defecto...")
            titulo_video = "video_sin_titulo"
        
        # Obtener duración continuamente mientras está grabando
        logging.info("Obteniendo duración del video (continuará intentando mientras graba)...")
        duracion_segundos = self.browser_manager.obtener_duracion_video_continuo()
        
        if not duracion_segundos or duracion_segundos == 0:
            logging.warning("No se pudo obtener la duración. Usando duración por defecto de 60 segundos...")
            duracion_segundos = 60
        
        # Aplicar limitación de duración en modo prueba
        duracion_original = duracion_segundos
        if config.MODO_PRUEBA and config.DURACION_MAXIMA_PRUEBA:
            duracion_segundos = min(duracion_segundos, config.DURACION_MAXIMA_PRUEBA)
            if duracion_original > config.DURACION_MAXIMA_PRUEBA:
                logging.info(f"Modo prueba: Limitando grabación a {config.DURACION_MAXIMA_PRUEBA}s (duración real: {duracion_original}s)")
        
        return titulo_video, duracion_segundos
    
    def _monitorear_reproduccion(self, duracion_segundos: int) -> None:
        """Monitorea la reproducción durante la duración restante."""
        logging.info("")
        logging.info("=" * 70)
        logging.info("PASO 7: MONITOREANDO REPRODUCCIÓN")
        logging.info("=" * 70)
        logging.info(f"Grabando video durante {duracion_segundos} segundos (duración del contenido)...")
        self.browser_manager.monitorear_reproduccion(duracion_segundos)
    
    def _esperar_margen_final(self) -> None:
        """Espera el margen final antes de detener la grabación."""
        margen_final = config.MARGEN_FINAL_PRUEBA if config.MODO_PRUEBA else config.MARGEN_FINAL
        if margen_final > 0:
            logging.info("")
            logging.info("=" * 70)
            logging.info("PASO 8: ESPERANDO MARGEN FINAL")
            logging.info("=" * 70)
            logging.info(f"Esperando {margen_final} segundos de margen final antes de detener la grabación...")
            time.sleep(margen_final)
    
    def _finalizar_grabacion(
        self,
        ruta_modulo: Path,
        titulo_video: str,
        numero_video: int,
        duracion_segundos: int,
        indice_lista: int,
        total_videos: int
    ) -> bool:
        """Detiene la grabación y gestiona el archivo."""
        logging.info("")
        logging.info("=" * 70)
        logging.info("PASO 9: DETENIENDO GRABACIÓN")
        logging.info("=" * 70)
        
        # Detener grabación y obtener ruta
        ruta_original = self.obs_manager.detener_grabacion()
        
        # Si la ruta no está en el directorio correcto, buscar el archivo más reciente
        if ruta_original:
            ruta_original_normalizada = Path(ruta_original).resolve()
            directorio_actual_normalizado = Path(ruta_modulo).resolve()
            
            if ruta_original_normalizada.parent != directorio_actual_normalizado:
                logging.warning(f"ADVERTENCIA: La ruta obtenida ({ruta_original}) no está en el directorio del módulo actual ({ruta_modulo})")
                logging.info("Buscando el archivo más reciente en el directorio del módulo actual...")
                
                archivo_reciente = self.file_manager.buscar_archivo_reciente(ruta_modulo)
                if archivo_reciente:
                    ruta_original = archivo_reciente
                    logging.info(f"✓ Archivo encontrado en el directorio correcto: {ruta_original}")
        
        # Gestionar archivo grabado
        if ruta_original:
            return self.file_manager.gestionar_archivo_grabado(
                ruta_original,
                ruta_modulo,
                titulo_video,
                numero_video,
                duracion_segundos
            )
        else:
            logging.warning("No se pudo obtener la ruta del archivo grabado")
            return False
    
    def _limpiar_antes_siguiente_video(self) -> None:
        """Limpia recursos antes del siguiente video."""
        # Pausa entre videos
        logging.info("Esperando antes del siguiente video...")
        time.sleep(2)
        
        # Asegurar que no hay grabación activa
        self.obs_manager.asegurar_grabacion_detenida()
        
        # Salir de pantalla completa
        self.browser_manager.salir_pantalla_completa()
        
        # Cerrar pestaña actual
        logging.info("Cerrando pestaña actual para preparar el siguiente video...")
        self.browser_manager.cerrar_pestaña_actual()

