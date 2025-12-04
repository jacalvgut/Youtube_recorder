"""
Orquestador principal del sistema de grabación de videos.

Este módulo coordina todos los componentes del sistema:
- Procesador de URLs
- Gestor del navegador
- Gestor de OBS

Es el punto de entrada principal del sistema.
"""

import time
import logging
from pathlib import Path
from typing import Dict, List, Optional
from selenium.common.exceptions import TimeoutException

# Importar configuración y utilidades
import config
from utils import (
    configurar_logging,
    sanitizar_nombre_archivo,
    formatear_tiempo,
    formatear_tamaño,
    parsear_duracion_a_segundos
)

# Importar módulos del sistema
from url_processor import URLProcessor
from browser_manager import BrowserManager
from obs_manager import OBSManager


class Orchestrator:
    """
    Clase orquestadora que coordina todos los componentes del sistema.
    
    Esta clase maneja el flujo completo del proceso de grabación:
    1. Procesa el archivo de URLs
    2. Crea la estructura de carpetas
    3. Inicializa el navegador y OBS
    4. Procesa cada módulo y video
    5. Gestiona las grabaciones
    """
    
    def __init__(self):
        """Inicializa el orquestador."""
        self.url_processor = URLProcessor()
        self.browser_manager = BrowserManager()
        self.obs_manager = OBSManager()
        self.estadisticas = {
            'videos_grabados': 0,
            'duracion_total_segundos': 0,
            'tamaño_total_bytes': 0,
            'archivos_grabados': []
        }
    
    def ejecutar(self) -> bool:
        """
        Ejecuta el proceso completo de grabación.
        
        Returns:
            bool: True si el proceso se completó exitosamente, False en caso contrario.
        """
        try:
            # Configurar logging
            configurar_logging()
            
            # Mostrar información del modo de prueba
            self._mostrar_info_modo_prueba()
            
            # 1. Procesar archivo de URLs
            logging.info("")
            logging.info("=" * 70)
            logging.info("PASO 1: PROCESANDO ARCHIVO DE URLs")
            logging.info("=" * 70)
            
            modulos = self.url_processor.parsear_archivo_urls()
            if not modulos:
                logging.error("ERROR CRÍTICO: No se pudieron procesar las URLs")
                return False
            
            # Aplicar límites de modo prueba
            self.url_processor.aplicar_limites_prueba()
            modulos = self.url_processor.obtener_todos_los_modulos()
            
            # Mostrar resumen de lo que se procesará
            total_videos = sum(len(urls) for urls in modulos.values())
            logging.info("")
            logging.info("=" * 60)
            logging.info(f"RESUMEN: Se procesarán {len(modulos)} módulo(s) con {total_videos} video(s) en total")
            logging.info("=" * 60)
            logging.info("")
            
            # 2. Crear estructura de carpetas
            logging.info("")
            logging.info("=" * 70)
            logging.info("PASO 2: CREANDO ESTRUCTURA DE CARPETAS")
            logging.info("=" * 70)
            
            directorio_base = Path.cwd()
            carpetas_creadas = self.url_processor.crear_estructura_carpetas(directorio_base)
            
            if not carpetas_creadas:
                logging.error("ERROR CRÍTICO: No se pudieron crear las carpetas")
                return False
            
            # 3. Conectar con OBS
            logging.info("")
            logging.info("=" * 70)
            logging.info("PASO 3: CONECTANDO CON OBS STUDIO")
            logging.info("=" * 70)
            
            if not self.obs_manager.conectar():
                logging.error("ERROR CRÍTICO: No se pudo conectar con OBS Studio")
                return False
            
            # Mostrar información de escenas
            self.obs_manager.mostrar_informacion_escenas()
            
            # Mostrar instrucciones de configuración
            self._mostrar_instrucciones_configuracion()
            
            # 4. Inicializar navegador
            logging.info("")
            logging.info("=" * 70)
            logging.info("PASO 4: INICIALIZANDO NAVEGADOR")
            logging.info("=" * 70)
            
            if not self.browser_manager.inicializar_navegador():
                logging.error("ERROR CRÍTICO: No se pudo inicializar el navegador")
                self.obs_manager.desconectar()
                return False
            
            # Asegurar que la ventana esté visible
            time.sleep(2)
            
            # 5. Procesar cada módulo y video
            logging.info("")
            logging.info("=" * 70)
            logging.info("PASO 5: PROCESANDO VIDEOS")
            logging.info("=" * 70)
            
            modulos_procesados = list(modulos.keys())
            
            try:
                self._procesar_modulos(modulos, carpetas_creadas)
            finally:
                # 6. Limpieza final y resumen
                self._mostrar_resumen_final(modulos_procesados)
                self._limpiar_recursos()
            
            return True
        
        except KeyboardInterrupt:
            logging.warning("")
            logging.warning("=" * 70)
            logging.warning("INTERRUPCIÓN DEL USUARIO")
            logging.warning("=" * 70)
            logging.warning("El proceso ha sido interrumpido por el usuario")
            self._limpiar_recursos()
            return False
        
        except Exception as e:
            logging.error("")
            logging.error("=" * 70)
            logging.error("ERROR CRÍTICO INESPERADO")
            logging.error("=" * 70)
            logging.error(f"Error: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            self._limpiar_recursos()
            return False
    
    def _mostrar_info_modo_prueba(self) -> None:
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
            time.sleep(3)  # Pausa para que el usuario vea el mensaje
    
    def _mostrar_instrucciones_configuracion(self) -> None:
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
    
    def _procesar_modulos(self, modulos: Dict[str, List[str]], carpetas: Dict[str, Path]) -> None:
        """
        Procesa todos los módulos y sus videos.
        
        Args:
            modulos: Diccionario con módulos y sus URLs.
            carpetas: Diccionario con módulos y sus rutas de carpetas.
        """
        directorio_base = Path.cwd()
        
        for nombre_modulo, urls in modulos.items():
            try:
                logging.info("")
                logging.info("=" * 70)
                logging.info(f"VERIFICACIÓN: Procesando Módulo: {nombre_modulo}")
                logging.info("=" * 70)
                
                ruta_modulo = carpetas.get(nombre_modulo)
                if not ruta_modulo:
                    logging.error(f"ERROR: No se encontró la carpeta para el módulo '{nombre_modulo}'")
                    continue
                
                # Configurar directorio de grabación en OBS
                if not self.obs_manager.configurar_directorio_grabacion(ruta_modulo):
                    logging.error(f"ERROR CRÍTICO: No se pudo configurar directorio en OBS para '{nombre_modulo}'")
                    continue
                
                # Procesar cada video del módulo
                self._procesar_videos_modulo(urls, ruta_modulo, nombre_modulo)
            
            except Exception as e:
                logging.error(f"ERROR al procesar módulo '{nombre_modulo}': {e}")
                import traceback
                logging.error(f"Traceback: {traceback.format_exc()}")
                continue
    
    def _procesar_videos_modulo(self, urls: List[str], ruta_modulo: Path, nombre_modulo: str) -> None:
        """
        Procesa todos los videos de un módulo.
        
        Args:
            urls: Lista de URLs a procesar.
            ruta_modulo: Ruta de la carpeta del módulo.
            nombre_modulo: Nombre del módulo.
        """
        for i, url in enumerate(urls, 1):
            try:
                logging.info("")
                logging.info("=" * 70)
                logging.info(f"Procesando video {i}/{len(urls)}: {url}")
                logging.info("=" * 70)
                
                # PASO 1: INICIAR GRABACIÓN PRIMERO (antes de hacer nada más)
                logging.info("")
                logging.info("=" * 70)
                logging.info("PASO 1: INICIANDO GRABACIÓN EN OBS")
                logging.info("=" * 70)
                if not self.obs_manager.iniciar_grabacion():
                    logging.error("ERROR: No se pudo iniciar la grabación. Saltando video...")
                    continue
                
                # PASO 2: ESPERAR MARGEN INICIAL mientras ya está grabando
                logging.info("")
                logging.info("=" * 70)
                logging.info("PASO 2: ESPERANDO MARGEN INICIAL (grabación activa)")
                logging.info("=" * 70)
                margen_inicial = config.MARGEN_INICIAL_PRUEBA if config.MODO_PRUEBA else config.MARGEN_INICIAL
                if margen_inicial > 0:
                    logging.info(f"Esperando {margen_inicial} segundos de margen inicial (ya está grabando)...")
                    time.sleep(margen_inicial)
                
                # PASO 3: CARGAR URL en el navegador DESPUÉS de iniciar grabación
                logging.info("")
                logging.info("=" * 70)
                logging.info("PASO 3: CARGANDO VIDEO EN NAVEGADOR")
                logging.info("=" * 70)
                if not self.browser_manager.cargar_url(url):
                    logging.error(f"ERROR: No se pudo cargar la URL. Deteniendo grabación y saltando video...")
                    self.obs_manager.detener_grabacion()
                    continue
                
                # PASO 4: Reproducir el video primero (para que el reproductor esté listo)
                logging.info("")
                logging.info("=" * 70)
                logging.info("PASO 4: REPRODUCIENDO VIDEO")
                logging.info("=" * 70)
                if not self.browser_manager.reproducir_video():
                    logging.warning("No se pudo reproducir el video. Continuando de todas formas...")
                
                # PASO 5: Configurar pantalla completa (después de que el reproductor esté listo)
                logging.info("")
                logging.info("=" * 70)
                logging.info("PASO 5: CONFIGURANDO PANTALLA COMPLETA")
                logging.info("=" * 70)
                # Esperar un momento para que el reproductor esté completamente cargado
                time.sleep(1)
                if not self.browser_manager.configurar_pantalla_completa():
                    logging.warning("No se pudo configurar pantalla completa. Continuando de todas formas...")
                
                # PASO 6: Obtener información del video MIENTRAS ya está grabando
                # La obtención de duración será continua hasta que se detecte
                logging.info("")
                logging.info("=" * 70)
                logging.info("PASO 6: OBTENIENDO INFORMACIÓN DEL VIDEO (grabación activa)")
                logging.info("=" * 70)
                titulo_video = None
                duracion_segundos = None
                
                # Obtener título (esto debería ser rápido)
                titulo_video = self.browser_manager.obtener_titulo_video()
                if not titulo_video:
                    logging.warning("No se pudo obtener el título. Usando nombre por defecto...")
                    titulo_video = f"video_{i}"
                
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
                
                # PASO 7: Monitorear reproducción durante la duración restante
                logging.info("")
                logging.info("=" * 70)
                logging.info("PASO 7: MONITOREANDO REPRODUCCIÓN")
                logging.info("=" * 70)
                logging.info(f"Grabando video durante {duracion_segundos} segundos (duración del contenido)...")
                self.browser_manager.monitorear_reproduccion(duracion_segundos)
                
                # PASO 8: Aplicar margen final
                margen_final = config.MARGEN_FINAL_PRUEBA if config.MODO_PRUEBA else config.MARGEN_FINAL
                if margen_final > 0:
                    logging.info("")
                    logging.info("=" * 70)
                    logging.info("PASO 8: ESPERANDO MARGEN FINAL")
                    logging.info("=" * 70)
                    logging.info(f"Esperando {margen_final} segundos de margen final antes de detener la grabación...")
                    time.sleep(margen_final)
                
                # PASO 9: Detener grabación
                logging.info("")
                logging.info("=" * 70)
                logging.info("PASO 9: DETENIENDO GRABACIÓN")
                logging.info("=" * 70)
                ruta_original = self.obs_manager.detener_grabacion()
                
                # Renombrar y mover archivo
                if ruta_original:
                    self._gestionar_archivo_grabado(
                        ruta_original,
                        ruta_modulo,
                        titulo_video,
                        i,
                        duracion_segundos
                    )
                else:
                    logging.warning("No se pudo obtener la ruta del archivo grabado")
                
                # Pausa entre videos
                logging.info("Esperando antes del siguiente video...")
                time.sleep(2)
                
                # Asegurar que no hay grabación activa
                self.obs_manager.asegurar_grabacion_detenida()
                
                # Salir de pantalla completa antes de cerrar la pestaña
                self.browser_manager.salir_pantalla_completa()
                
                # Cerrar pestaña actual si no es la última
                if i < len(urls):
                    self.browser_manager.cerrar_pestaña_actual()
                
                logging.info("=" * 70)
                logging.info(f"✓ Video {i}/{len(urls)} completado")
                logging.info("=" * 70)
                logging.info("")
            
            except TimeoutException as e:
                logging.error(f"Tiempo de espera agotado al cargar el video {url}")
                logging.error(f"Puede ser un video privado, eliminado o la conexión es lenta.")
                logging.error(f"Error: {e}")
                self.obs_manager.asegurar_grabacion_detenida()
            
            except Exception as e:
                logging.error(f"Ocurrió un error inesperado al procesar {url}: {e}")
                logging.error(f"Tipo de error: {type(e).__name__}")
                import traceback
                logging.error(f"Traceback completo:\n{traceback.format_exc()}")
                self.obs_manager.asegurar_grabacion_detenida()
    
    def _gestionar_archivo_grabado(
        self,
        ruta_original: Path,
        ruta_modulo: Path,
        titulo_video: str,
        numero_video: int,
        duracion_segundos: int
    ) -> None:
        """
        Gestiona el archivo grabado: lo renombra y lo mueve a la ubicación correcta.
        
        Args:
            ruta_original: Ruta original del archivo grabado.
            ruta_modulo: Carpeta del módulo donde guardar el archivo.
            titulo_video: Título del video.
            numero_video: Número del video en el módulo.
            duracion_segundos: Duración del video en segundos.
        """
        logging.info("")
        logging.info("=" * 70)
        logging.info("VERIFICACIÓN: Guardando archivo grabado...")
        logging.info("=" * 70)
        
        time.sleep(2)  # Pausa para que OBS libere el archivo
        
        # Verificar que el archivo existe
        if not ruta_original.exists():
            logging.warning(f"El archivo {ruta_original} no existe. Esperando más tiempo...")
            for espera in range(5):
                time.sleep(2)
                if ruta_original.exists():
                    break
                logging.info(f"Esperando archivo... ({espera + 1}/5)")
        
        if not ruta_original.exists():
            logging.error(f"ERROR: El archivo no se encontró después de esperar: {ruta_original}")
            return
        
        try:
            logging.info(f"✓ Archivo encontrado: {ruta_original}")
            
            extension = ruta_original.suffix
            nombre_archivo_saneado = sanitizar_nombre_archivo(titulo_video)
            
            # Agregar sufijo en modo prueba
            sufijo_prueba = "_PRUEBA" if config.MODO_PRUEBA else ""
            nuevo_nombre = f"{numero_video:02d}_{nombre_archivo_saneado}{sufijo_prueba}{extension}"
            nueva_ruta = ruta_modulo / nuevo_nombre
            
            # Sobreescribir si el archivo ya existe
            if nueva_ruta.exists():
                logging.info(f"ADVERTENCIA: El archivo '{nuevo_nombre}' ya existe. Sobreescribiendo...")
                try:
                    nueva_ruta.unlink()
                    logging.info("✓ Archivo existente eliminado")
                except Exception as e:
                    logging.warning(f"No se pudo eliminar archivo existente: {e}")
            
            # Renombrar y mover el archivo
            try:
                ruta_original.rename(nueva_ruta)
                logging.info(f"✓ Archivo renombrado y guardado: {nueva_ruta.name}")
                
                # Verificar que el archivo se guardó correctamente
                if nueva_ruta.exists():
                    tamaño_archivo = nueva_ruta.stat().st_size
                    logging.info(f"✓ Archivo verificado: {formatear_tamaño(tamaño_archivo)}")
                    
                    # Actualizar estadísticas
                    self.estadisticas['videos_grabados'] += 1
                    self.estadisticas['duracion_total_segundos'] += duracion_segundos
                    self.estadisticas['tamaño_total_bytes'] += tamaño_archivo
                    self.estadisticas['archivos_grabados'].append(nueva_ruta)
                else:
                    logging.error("ERROR CRÍTICO: El archivo no existe después de renombrar")
            
            except Exception as e:
                logging.error(f"ERROR CRÍTICO al renombrar archivo: {e}")
                import traceback
                logging.error(f"Traceback: {traceback.format_exc()}")
        
        except Exception as e:
            logging.error(f"ERROR al gestionar archivo: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
        
        logging.info("=" * 70)
    
    def _mostrar_resumen_final(self, modulos_procesados: List[str]) -> None:
        """
        Muestra el resumen final de la ejecución.
        
        Args:
            modulos_procesados: Lista de nombres de módulos procesados.
        """
        logging.info("")
        logging.info("=" * 70)
        logging.info("RESUMEN FINAL DE EJECUCIÓN")
        logging.info("=" * 70)
        
        # Calcular tamaño total de archivos en las carpetas de módulos procesados
        directorio_base = Path.cwd()
        tamaño_total_calculado = 0
        archivos_encontrados = 0
        
        try:
            for nombre_modulo in modulos_procesados:
                ruta_modulo = directorio_base / nombre_modulo
                if ruta_modulo.exists() and ruta_modulo.is_dir():
                    for archivo in ruta_modulo.iterdir():
                        if archivo.is_file():
                            tamaño_total_calculado += archivo.stat().st_size
                            archivos_encontrados += 1
        except Exception as e:
            logging.warning(f"Error al calcular tamaño total: {e}")
        
        # Usar el tamaño calculado si es mayor
        if tamaño_total_calculado > self.estadisticas['tamaño_total_bytes']:
            self.estadisticas['tamaño_total_bytes'] = tamaño_total_calculado
        
        # Mostrar estadísticas
        logging.info(f"  ✓ Videos grabados exitosamente: {self.estadisticas['videos_grabados']}")
        
        if self.estadisticas['duracion_total_segundos'] > 0:
            tiempo_formateado = formatear_tiempo(self.estadisticas['duracion_total_segundos'])
            logging.info(f"  ✓ Duración total grabada: {tiempo_formateado}")
            horas_totales = self.estadisticas['duracion_total_segundos'] / 3600
            if horas_totales >= 1:
                logging.info(f"    ({horas_totales:.2f} horas)")
        else:
            logging.info(f"  ✓ Duración total grabada: 0 segundos")
        
        if self.estadisticas['tamaño_total_bytes'] > 0:
            tamaño_formateado = formatear_tamaño(self.estadisticas['tamaño_total_bytes'])
            logging.info(f"  ✓ Tamaño total de archivos: {tamaño_formateado}")
        else:
            logging.info(f"  ✓ Tamaño total de archivos: 0 bytes")
        
        logging.info("=" * 70)
        logging.info("")
    
    def _limpiar_recursos(self) -> None:
        """Limpia todos los recursos utilizados (navegador, OBS, etc.)."""
        logging.info("Limpiando recursos...")
        
        # Asegurar que no hay grabación activa
        try:
            self.obs_manager.asegurar_grabacion_detenida()
        except:
            pass
        
        # Desconectar de OBS
        try:
            self.obs_manager.desconectar()
        except:
            pass
        
        # Cerrar navegador
        try:
            self.browser_manager.cerrar_navegador()
        except:
            pass
        
        logging.info("✓ Recursos limpiados")


def main():
    """
    Función principal del sistema.
    
    Punto de entrada cuando se ejecuta el script directamente.
    """
    orchestrator = Orchestrator()
    success = orchestrator.ejecutar()
    
    if success:
        logging.info("")
        logging.info("=" * 70)
        logging.info("PROCESO COMPLETADO EXITOSAMENTE")
        logging.info("=" * 70)
        logging.info("")
    else:
        logging.error("")
        logging.error("=" * 70)
        logging.error("PROCESO FINALIZADO CON ERRORES")
        logging.error("=" * 70)
        logging.error("")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())

