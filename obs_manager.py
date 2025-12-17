"""
Módulo para gestionar OBS Studio y las grabaciones de video.

Este módulo se encarga de:
- Conectar con OBS Studio a través del WebSocket
- Iniciar y detener grabaciones
- Configurar directorios de salida
- Verificar el estado de las grabaciones
"""

import logging
from pathlib import Path
from typing import Optional
import obsws_python as obs
import config
from obs_connection import conectar_obs, verificar_conexion_obs
from obs_recording import iniciar_grabacion_obs, detener_grabacion_obs, verificar_grabacion_activa, asegurar_grabacion_detenida


class OBSManager:
    """
    Clase encargada de gestionar OBS Studio y las grabaciones de video.
    
    Esta clase maneja toda la lógica relacionada con:
    - Conexión a OBS
    - Control de grabaciones
    - Configuración de rutas de salida
    """
    
    def __init__(self):
        """Inicializa el gestor de OBS."""
        self.cliente_obs: Optional[obs.ReqClient] = None
        self.conectado = False
    
    def conectar(self) -> bool:
        """
        Conecta con OBS Studio a través del WebSocket.
        
        Returns:
            bool: True si la conexión fue exitosa, False en caso contrario.
        """
        self.cliente_obs = conectar_obs()
        
        if not self.cliente_obs:
            return False
        
        self.conectado = True
        
        # Verificar configuración de audio después de conectar
        self.verificar_configuracion_audio()
        
        return True
    
    def verificar_conexion(self) -> bool:
        """
        Verifica que la conexión con OBS esté activa.
        
        Returns:
            bool: True si está conectado, False en caso contrario.
        """
        if not self.conectado or not self.cliente_obs:
            return False
        
        conexion_activa = verificar_conexion_obs(self.cliente_obs)
        if not conexion_activa:
            self.conectado = False
        
        return conexion_activa
    
    def configurar_directorio_grabacion(self, directorio: Path) -> bool:
        """
        Configura el directorio donde OBS guardará las grabaciones.
        
        Args:
            directorio: Ruta al directorio donde se guardarán las grabaciones.
        
        Returns:
            bool: True si se configuró correctamente, False en caso contrario.
        """
        if not self.verificar_conexion():
            logging.error("ERROR: No hay conexión con OBS para configurar directorio")
            return False
        
        try:
            directorio_str = str(directorio.resolve())
            self.cliente_obs.set_record_directory(directorio_str)
            logging.info(f"✓ Directorio de grabación OBS configurado: {directorio}")
            return True
        
        except Exception as e:
            logging.error(f"ERROR al configurar directorio en OBS: {e}")
            logging.error(f"Directorio intentado: {directorio}")
            return False
    
    def iniciar_grabacion(self) -> bool:
        """
        Inicia una grabación en OBS Studio.
        
        Returns:
            bool: True si la grabación se inició correctamente, False en caso contrario.
        """
        if not self.verificar_conexion():
            logging.error("ERROR: No hay conexión con OBS para iniciar grabación")
            return False
        
        return iniciar_grabacion_obs(self.cliente_obs)
    
    def detener_grabacion(self) -> Optional[Path]:
        """
        Detiene la grabación activa en OBS Studio.
        
        Returns:
            Path: Ruta al archivo grabado si se obtuvo correctamente, None en caso contrario.
        """
        if not self.verificar_conexion():
            logging.error("ERROR: No hay conexión con OBS para detener grabación")
            return None
        
        return detener_grabacion_obs(self.cliente_obs)
    
    def verificar_grabacion_activa(self) -> bool:
        """
        Verifica si hay una grabación activa en OBS.
        
        Returns:
            bool: True si hay grabación activa, False en caso contrario.
        """
        if not self.verificar_conexion():
            return False
        
        return verificar_grabacion_activa(self.cliente_obs)
    
    def asegurar_grabacion_detenida(self) -> None:
        """
        Asegura que no haya ninguna grabación activa.
        
        Si hay una grabación activa, la detiene.
        """
        if not self.verificar_conexion():
            return
        
        asegurar_grabacion_detenida(self.cliente_obs)
    
    def mostrar_informacion_escenas(self) -> None:
        """
        Muestra información sobre las escenas disponibles en OBS.
        
        Útil para depuración y verificación de configuración.
        """
        if not self.verificar_conexion():
            logging.warning("No hay conexión con OBS para obtener información de escenas")
            return
        
        try:
            escenas = self.cliente_obs.get_scene_list()
            if not escenas.scenes:
                logging.warning("No se encontraron escenas en OBS.")
                logging.warning("IMPORTANTE: Crea una escena en OBS antes de continuar.")
            else:
                escena_actual = escenas.scenes[0].get('sceneName', escenas.scenes[0].get('name', 'Scene'))
                logging.info(f"Escena activa en OBS: {escena_actual}")
        except Exception as e:
            logging.warning(f"Error al obtener información de escenas: {e}")
    
    def verificar_configuracion_audio(self) -> None:
        """
        Verifica y muestra información sobre la configuración de audio en OBS.
        
        Muestra las fuentes de audio activas para que el usuario pueda verificarlas.
        """
        if not self.verificar_conexion():
            logging.warning("No hay conexión con OBS para verificar audio")
            return
        
        try:
            logging.info("")
            logging.info("=" * 70)
            logging.info("VERIFICACIÓN: Configuración de Audio en OBS")
            logging.info("=" * 70)
            logging.info("")
            logging.info("IMPORTANTE: Para que solo se grabe el audio del navegador:")
            logging.info("")
            logging.info("1. En OBS, ve a: Configuración > Audio")
            logging.info("")
            logging.info("2. Desactiva las siguientes fuentes de audio:")
            logging.info("   - Desactivar dispositivo de captura de escritorio (Desktop Audio)")
            logging.info("   - Desactivar dispositivo auxiliar de audio 1/2/3")
            logging.info("   - Desactivar cualquier micrófono (Mic/Aux)")
            logging.info("")
            logging.info("3. En la escena activa, verifica que solo tengas:")
            logging.info("   - La fuente de captura de ventana del navegador")
            logging.info("   - NO agregues fuentes de audio adicionales")
            logging.info("")
            logging.info("4. El audio del navegador se capturará automáticamente")
            logging.info("   desde la captura de ventana si está configurado correctamente")
            logging.info("")
            logging.info("=" * 70)
            logging.info("")
        
        except Exception as e:
            logging.warning(f"Error al verificar configuración de audio: {e}")
    
    def desconectar(self) -> None:
        """Cierra la conexión con OBS Studio."""
        if self.cliente_obs:
            # Asegurar que no hay grabación activa
            self.asegurar_grabacion_detenida()
            self.cliente_obs = None
            self.conectado = False
            logging.info("✓ Desconectado de OBS Studio")
