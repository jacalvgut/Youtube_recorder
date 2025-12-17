"""
Orquestador principal del sistema de grabación de videos.

Este módulo coordina todos los componentes del sistema:
- Procesador de URLs
- Gestor del navegador
- Gestor de OBS
- Procesador de videos
- Gestor de archivos

Es el punto de entrada principal del sistema.
"""

import time
import logging
from pathlib import Path
from typing import Dict, List
import config
from utils import configurar_logging
from url_processor import URLProcessor
from browser_manager import BrowserManager
from obs_manager import OBSManager
from video_processor import VideoProcessor
from file_manager import FileManager
from orchestrator_setup import mostrar_info_modo_prueba, mostrar_instrucciones_configuracion
from orchestrator_summary import mostrar_resumen_final


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
        self.file_manager = FileManager(self.estadisticas)
        self.video_processor = VideoProcessor(
            self.browser_manager,
            self.obs_manager,
            self.file_manager
        )
    
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
            mostrar_info_modo_prueba()
            
            # 1. Procesar archivo de URLs
            modulos = self._procesar_urls()
            if not modulos:
                return False
            
            # 2. Crear estructura de carpetas
            carpetas_creadas = self._crear_estructura_carpetas()
            if not carpetas_creadas:
                return False
            
            # 3. Conectar con OBS
            if not self._conectar_obs():
                return False
            
            # 4. Inicializar navegador
            if not self._inicializar_navegador():
                self.obs_manager.desconectar()
                return False
            
            # 5. Procesar cada módulo y video
            modulos_procesados = list(modulos.keys())
            try:
                self._procesar_modulos(modulos, carpetas_creadas)
            finally:
                # 6. Limpieza final y resumen
                mostrar_resumen_final(self.estadisticas, modulos_procesados)
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
    
    def _procesar_urls(self) -> Dict[str, List[str]]:
        """Procesa el archivo de URLs y aplica filtros."""
        logging.info("")
        logging.info("=" * 70)
        logging.info("PASO 1: PROCESANDO ARCHIVO DE URLs")
        logging.info("=" * 70)
        
        modulos = self.url_processor.parsear_archivo_urls()
        if not modulos:
            logging.error("ERROR CRÍTICO: No se pudieron procesar las URLs")
            return {}
        
        # Aplicar filtros
        self.url_processor.aplicar_modulo_inicio()
        self.url_processor.aplicar_limites_prueba()
        indices_inicio = self.url_processor.aplicar_inicio_video()
        modulos = self.url_processor.obtener_todos_los_modulos()
        
        # Guardar índices de inicio para uso posterior
        self.indices_inicio = indices_inicio
        
        # Mostrar resumen
        total_videos = sum(len(urls) for urls in modulos.values())
        logging.info("")
        logging.info("=" * 60)
        logging.info(f"RESUMEN: Se procesarán {len(modulos)} módulo(s) con {total_videos} video(s) en total")
        logging.info("=" * 60)
        logging.info("")
        
        return modulos
    
    def _crear_estructura_carpetas(self) -> Dict[str, Path]:
        """Crea la estructura de carpetas para los módulos."""
        logging.info("")
        logging.info("=" * 70)
        logging.info("PASO 2: CREANDO ESTRUCTURA DE CARPETAS")
        logging.info("=" * 70)
        
        directorio_base = Path.cwd()
        carpetas_creadas = self.url_processor.crear_estructura_carpetas(directorio_base)
        
        if not carpetas_creadas:
            logging.error("ERROR CRÍTICO: No se pudieron crear las carpetas")
        
        return carpetas_creadas
    
    def _conectar_obs(self) -> bool:
        """Conecta con OBS Studio."""
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
        mostrar_instrucciones_configuracion()
        
        return True
    
    def _inicializar_navegador(self) -> bool:
        """Inicializa el navegador."""
        logging.info("")
        logging.info("=" * 70)
        logging.info("PASO 4: INICIALIZANDO NAVEGADOR")
        logging.info("=" * 70)
        
        if not self.browser_manager.inicializar_navegador():
            logging.error("ERROR CRÍTICO: No se pudo inicializar el navegador")
            return False
        
        # Asegurar que la ventana esté visible
        time.sleep(2)
        return True
    
    def _procesar_modulos(
        self,
        modulos: Dict[str, List[str]],
        carpetas: Dict[str, Path]
    ) -> None:
        """
        Procesa todos los módulos y sus videos.
        
        Args:
            modulos: Diccionario con módulos y sus URLs.
            carpetas: Diccionario con módulos y sus rutas de carpetas.
        """
        logging.info("")
        logging.info("=" * 70)
        logging.info("PASO 5: PROCESANDO VIDEOS")
        logging.info("=" * 70)
        
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
                
                # Preparar módulo
                self._preparar_modulo(ruta_modulo, nombre_modulo)
                
                # Obtener índice de inicio para este módulo
                indice_inicio = self.indices_inicio.get(nombre_modulo, 1)
                
                # Procesar cada video del módulo
                self._procesar_videos_modulo(urls, ruta_modulo, nombre_modulo, indice_inicio)
            
            except Exception as e:
                logging.error(f"ERROR al procesar módulo '{nombre_modulo}': {e}")
                import traceback
                logging.error(f"Traceback: {traceback.format_exc()}")
                continue
    
    def _preparar_modulo(self, ruta_modulo: Path, nombre_modulo: str) -> None:
        """Prepara el módulo antes de procesar videos."""
        # Asegurar que no hay grabación activa
        self.obs_manager.asegurar_grabacion_detenida()
        
        # Esperar tiempo adicional antes de cambiar el directorio
        logging.info("Esperando para asegurar que el archivo del módulo anterior se haya guardado completamente...")
        time.sleep(2)
        
        # Configurar directorio de grabación en OBS
        if not self.obs_manager.configurar_directorio_grabacion(ruta_modulo):
            logging.error(f"ERROR CRÍTICO: No se pudo configurar directorio en OBS para '{nombre_modulo}'")
            raise Exception(f"No se pudo configurar directorio para {nombre_modulo}")
    
    def _procesar_videos_modulo(
        self,
        urls: List[str],
        ruta_modulo: Path,
        nombre_modulo: str,
        indice_inicio: int
    ) -> None:
        """
        Procesa todos los videos de un módulo.
        
        Args:
            urls: Lista de URLs a procesar.
            ruta_modulo: Ruta de la carpeta del módulo.
            nombre_modulo: Nombre del módulo.
            indice_inicio: Índice desde el cual empezar la numeración de archivos.
        """
        for i, url in enumerate(urls, 1):
            # Calcular el número real del video para el nombre del archivo
            numero_video = indice_inicio + i - 1
            
            # Procesar video usando VideoProcessor
            self.video_processor.procesar_video(
                url=url,
                ruta_modulo=ruta_modulo,
                nombre_modulo=nombre_modulo,
                numero_video=numero_video,
                indice_lista=i,
                total_videos=len(urls)
            )
            
            # Si es el último video del módulo, esperar adicional
            if i == len(urls):
                logging.info("Esperando tiempo adicional para asegurar que el archivo se haya guardado completamente...")
                time.sleep(3)
    
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
