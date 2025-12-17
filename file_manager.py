"""
Módulo para gestionar archivos grabados.

Este módulo se encarga de:
- Renombrar archivos grabados
- Mover archivos a las carpetas correctas
- Verificar integridad de archivos
- Actualizar estadísticas
"""

import time
import logging
from pathlib import Path
from typing import Dict, Optional
import config
from utils import sanitizar_nombre_archivo, formatear_tamaño


class FileManager:
    """
    Clase encargada de gestionar archivos grabados.
    
    Maneja el renombrado, movimiento y verificación de archivos de video.
    """
    
    def __init__(self, estadisticas: Dict):
        """
        Inicializa el gestor de archivos.
        
        Args:
            estadisticas: Diccionario compartido para almacenar estadísticas.
        """
        self.estadisticas = estadisticas
    
    def gestionar_archivo_grabado(
        self,
        ruta_original: Path,
        ruta_modulo: Path,
        titulo_video: str,
        numero_video: int,
        duracion_segundos: int
    ) -> bool:
        """
        Gestiona el archivo grabado: lo renombra y lo mueve a la ubicación correcta.
        
        Args:
            ruta_original: Ruta original del archivo grabado.
            ruta_modulo: Carpeta del módulo donde guardar el archivo.
            titulo_video: Título del video.
            numero_video: Número del video en el módulo.
            duracion_segundos: Duración del video en segundos.
        
        Returns:
            bool: True si se gestionó correctamente, False en caso contrario.
        """
        logging.info("")
        logging.info("=" * 70)
        logging.info("VERIFICACIÓN: Guardando archivo grabado...")
        logging.info("=" * 70)
        
        time.sleep(2)  # Pausa para que OBS libere el archivo
        
        # Verificar que el archivo existe
        if not self._esperar_archivo(ruta_original):
            logging.error(f"ERROR: El archivo no se encontró después de esperar: {ruta_original}")
            return False
        
        try:
            logging.info(f"✓ Archivo encontrado: {ruta_original}")
            
            # Generar nuevo nombre y ruta
            nueva_ruta = self._generar_ruta_archivo(
                ruta_original, ruta_modulo, titulo_video, numero_video
            )
            
            # Sobreescribir si el archivo ya existe
            if nueva_ruta.exists():
                self._eliminar_archivo_existente(nueva_ruta)
            
            # Renombrar y mover el archivo
            if self._renombrar_archivo(ruta_original, nueva_ruta, duracion_segundos):
                logging.info("=" * 70)
                return True
            else:
                return False
        
        except Exception as e:
            logging.error(f"ERROR al gestionar archivo: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def _esperar_archivo(self, ruta: Path, max_intentos: int = 5) -> bool:
        """
        Espera a que un archivo exista.
        
        Args:
            ruta: Ruta del archivo a esperar.
            max_intentos: Número máximo de intentos.
        
        Returns:
            bool: True si el archivo existe, False en caso contrario.
        """
        if ruta.exists():
            return True
        
        logging.warning(f"El archivo {ruta} no existe. Esperando más tiempo...")
        for espera in range(max_intentos):
            time.sleep(2)
            if ruta.exists():
                return True
            logging.info(f"Esperando archivo... ({espera + 1}/{max_intentos})")
        
        return False
    
    def _generar_ruta_archivo(
        self,
        ruta_original: Path,
        ruta_modulo: Path,
        titulo_video: str,
        numero_video: int
    ) -> Path:
        """
        Genera la ruta completa del archivo renombrado.
        
        Args:
            ruta_original: Ruta original del archivo.
            ruta_modulo: Carpeta del módulo.
            titulo_video: Título del video.
            numero_video: Número del video.
        
        Returns:
            Path: Ruta completa del archivo renombrado.
        """
        extension = ruta_original.suffix
        nombre_archivo_saneado = sanitizar_nombre_archivo(titulo_video)
        
        # Agregar sufijo en modo prueba
        sufijo_prueba = "_PRUEBA" if config.MODO_PRUEBA else ""
        nuevo_nombre = f"{numero_video:02d}_{nombre_archivo_saneado}{sufijo_prueba}{extension}"
        
        return ruta_modulo / nuevo_nombre
    
    def _eliminar_archivo_existente(self, ruta: Path) -> None:
        """
        Elimina un archivo existente si es necesario.
        
        Args:
            ruta: Ruta del archivo a eliminar.
        """
        try:
            logging.info(f"ADVERTENCIA: El archivo '{ruta.name}' ya existe. Sobreescribiendo...")
            ruta.unlink()
            logging.info("✓ Archivo existente eliminado")
        except Exception as e:
            logging.warning(f"No se pudo eliminar archivo existente: {e}")
    
    def _renombrar_archivo(
        self,
        ruta_original: Path,
        nueva_ruta: Path,
        duracion_segundos: int
    ) -> bool:
        """
        Renombra y mueve el archivo a la nueva ubicación.
        
        Args:
            ruta_original: Ruta original del archivo.
            nueva_ruta: Nueva ruta del archivo.
            duracion_segundos: Duración del video en segundos.
        
        Returns:
            bool: True si se renombró correctamente, False en caso contrario.
        """
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
                
                return True
            else:
                logging.error("ERROR CRÍTICO: El archivo no existe después de renombrar")
                return False
        
        except Exception as e:
            logging.error(f"ERROR CRÍTICO al renombrar archivo: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def buscar_archivo_reciente(self, directorio: Path) -> Optional[Path]:
        """
        Busca el archivo más reciente en un directorio.
        
        Args:
            directorio: Directorio donde buscar.
        
        Returns:
            Path del archivo más reciente, o None si no se encuentra.
        """
        try:
            extensiones_video = {'.mp4', '.mkv', '.mov', '.avi', '.flv', '.webm'}
            archivos_video = [
                f for f in directorio.glob("*.*")
                if f.is_file() and f.suffix.lower() in extensiones_video
            ]
            
            if not archivos_video:
                return None
            
            # Ordenar por tiempo de modificación (más reciente primero)
            archivos_video.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            
            # Buscar archivo que no tenga formato renombrado (no empieza con número)
            for archivo in archivos_video:
                nombre_archivo = archivo.name
                if len(nombre_archivo) < 2 or not (nombre_archivo[0:2].isdigit() and nombre_archivo[2] == '_'):
                    return archivo
            
            # Si todos están renombrados, usar el más reciente
            return archivos_video[0]
        
        except Exception as e:
            logging.warning(f"Error al buscar archivo reciente: {e}")
            return None

