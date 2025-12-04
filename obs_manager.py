"""
Módulo para gestionar OBS Studio y las grabaciones de video.

Este módulo se encarga de:
- Conectar con OBS Studio a través del WebSocket
- Iniciar y detener grabaciones
- Configurar directorios de salida
- Verificar el estado de las grabaciones
- Manejar errores de conexión y grabación
"""

import time
import logging
from pathlib import Path
from typing import Optional
import obsws_python as obs
from obsws_python.error import OBSSDKError
import config


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
        logging.info("=" * 70)
        logging.info("VERIFICACIÓN: Conectando con OBS Studio...")
        logging.info("=" * 70)
        
        try:
            password_info = "con contraseña" if config.OBS_PASSWORD else "sin contraseña"
            logging.info(f"Conectando a OBS en {config.OBS_HOST}:{config.OBS_PORT} ({password_info})...")
            
            self.cliente_obs = obs.ReqClient(
                host=config.OBS_HOST,
                port=config.OBS_PORT,
                password=config.OBS_PASSWORD,
                timeout=10
            )
            
            # Verificar la conexión obteniendo la versión
            version = self.cliente_obs.get_version()
            logging.info(f"✓ Conexión con OBS exitosa")
            logging.info(f"  - Versión de OBS: {version.obs_version}")
            logging.info(f"  - Versión del plugin WebSocket: {version.obs_web_socket_version}")
            logging.info("=" * 70)
            
            self.conectado = True
            return True
        
        except ConnectionRefusedError:
            logging.error("=" * 70)
            logging.error("ERROR: No se pudo conectar a OBS Studio")
            logging.error("=" * 70)
            logging.error("")
            logging.error("VERIFICA QUE:")
            logging.error("  1. OBS Studio esté abierto")
            logging.error("  2. El plugin 'obs-websocket' esté instalado y activado")
            logging.error("     Ve a: Herramientas > Configuración del servidor WebSocket")
            logging.error("     Asegúrate de que el servidor esté habilitado")
            if config.OBS_PASSWORD:
                logging.error(f"  3. La contraseña en config.py sea correcta (actualmente configurada)")
            else:
                logging.error("  3. Si configuraste una contraseña en OBS, agrega 'OBS_PASSWORD' en config.py")
            logging.error("=" * 70)
            return False
        
        except OBSSDKError as e:
            logging.error("=" * 70)
            logging.error(f"ERROR: Error del SDK de OBS: {e}")
            logging.error("=" * 70)
            logging.error("")
            logging.error("Posibles causas:")
            logging.error("  - Contraseña incorrecta")
            logging.error("  - Plugin obs-websocket no instalado")
            logging.error("  - Versión incompatible de OBS o del plugin")
            logging.error("=" * 70)
            return False
        
        except Exception as e:
            logging.error("=" * 70)
            logging.error(f"ERROR inesperado al conectar con OBS: {e}")
            logging.error("=" * 70)
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def verificar_conexion(self) -> bool:
        """
        Verifica que la conexión con OBS esté activa.
        
        Returns:
            bool: True si está conectado, False en caso contrario.
        """
        if not self.conectado or not self.cliente_obs:
            return False
        
        try:
            self.cliente_obs.get_version()
            return True
        except:
            self.conectado = False
            return False
    
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
        
        try:
            logging.info("")
            logging.info("=" * 70)
            logging.info("VERIFICACIÓN: Iniciando grabación en OBS...")
            logging.info("=" * 70)
            
            # Verificar que no hay grabación activa antes de iniciar
            try:
                estado_antes = self.cliente_obs.get_record_status()
                if estado_antes.output_active:
                    logging.warning("Hay una grabación activa. Deteniéndola antes de iniciar nueva...")
                    self.detener_grabacion()
                    time.sleep(2)
            except:
                pass
            
            # Iniciar la grabación
            logging.info("Ejecutando cliente_obs.start_record()...")
            try:
                resultado_start = self.cliente_obs.start_record()
                if resultado_start:
                    logging.info(f"Resultado de start_record(): {resultado_start}")
                logging.info("Comando start_record() ejecutado. Esperando a que OBS inicie la grabación...")
            except Exception as e_start:
                logging.error(f"Error al ejecutar start_record(): {e_start}")
                logging.warning("Intentando continuar de todas formas...")
            
            time.sleep(3)  # Esperar a que la grabación inicie completamente
            
            # Verificar que la grabación se inició correctamente
            intentos_verificacion = 0
            grabacion_iniciada = False
            estado_grabacion_final = None
            
            while intentos_verificacion < 10:
                try:
                    estado_grabacion = self.cliente_obs.get_record_status()
                    estado_grabacion_final = estado_grabacion
                    
                    if hasattr(estado_grabacion, 'output_active') and estado_grabacion.output_active:
                        grabacion_iniciada = True
                        logging.info("✓ Grabación iniciada correctamente en OBS")
                        logging.info(f"  - Estado output_active: {estado_grabacion.output_active}")
                        
                        if hasattr(estado_grabacion, 'output_paused'):
                            logging.info(f"  - Estado output_paused: {estado_grabacion.output_paused}")
                        if hasattr(estado_grabacion, 'output_timecode'):
                            logging.info(f"  - Tiempo de grabación: {estado_grabacion.output_timecode}")
                        
                        logging.info("=" * 70)
                        return True
                    else:
                        logging.info(f"Intento {intentos_verificacion + 1}/10: Verificando estado de grabación...")
                        intentos_verificacion += 1
                        time.sleep(0.5)
                
                except Exception as e:
                    logging.warning(f"Error al verificar estado (intento {intentos_verificacion + 1}): {e}")
                    intentos_verificacion += 1
                    time.sleep(0.5)
            
            if not grabacion_iniciada:
                logging.warning("ADVERTENCIA: No se pudo verificar que la grabación se inició correctamente")
                logging.warning("Continuando de todas formas - la grabación puede estar activa aunque no se detecte")
                
                if estado_grabacion_final:
                    logging.info(f"Estado final detectado: {estado_grabacion_final}")
                
                logging.warning("Si la grabación no funciona, verifica:")
                logging.warning("  1. OBS debe tener al menos una fuente configurada en la escena")
                logging.warning("  2. El formato de salida debe estar configurado en OBS")
                logging.warning("  3. Verifica los logs de OBS para más detalles")
                logging.info("=" * 70)
            
            return True
        
        except Exception as e:
            logging.error(f"ERROR CRÍTICO al iniciar grabación: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def detener_grabacion(self) -> Optional[Path]:
        """
        Detiene la grabación activa en OBS Studio.
        
        Returns:
            Path: Ruta al archivo grabado si se obtuvo correctamente, None en caso contrario.
        """
        if not self.verificar_conexion():
            logging.error("ERROR: No hay conexión con OBS para detener grabación")
            return None
        
        try:
            logging.info("")
            logging.info("=" * 70)
            logging.info("VERIFICACIÓN: Verificando estado de grabación antes de detener...")
            logging.info("=" * 70)
            
            ruta_original = None
            grabacion_estaba_activa = False
            
            # Verificar si hay una grabación activa antes de intentar detenerla
            try:
                estado_antes_detener = self.cliente_obs.get_record_status()
                
                if hasattr(estado_antes_detener, 'output_active') and estado_antes_detener.output_active:
                    grabacion_estaba_activa = True
                    logging.info("✓ Hay una grabación activa. Deteniéndola...")
                    
                    try:
                        info_grabacion = self.cliente_obs.stop_record()
                        time.sleep(2)  # Esperar a que se detenga completamente
                        
                        # Verificar que la grabación se detuvo
                        estado_despues = self.cliente_obs.get_record_status()
                        if hasattr(estado_despues, 'output_active') and estado_despues.output_active:
                            logging.warning("ADVERTENCIA: La grabación aún está activa. Forzando detención...")
                            self.cliente_obs.stop_record()
                            time.sleep(2)
                        else:
                            logging.info("✓ Grabación detenida correctamente")
                        
                        # Obtener la ruta del archivo
                        if hasattr(info_grabacion, 'output_path') and info_grabacion.output_path:
                            ruta_original = Path(info_grabacion.output_path)
                            logging.info(f"✓ Archivo guardado temporalmente en: {ruta_original}")
                        else:
                            logging.warning("No se pudo obtener la ruta del archivo desde stop_record()")
                            # Intentar obtener desde el estado
                            try:
                                estado_actual = self.cliente_obs.get_record_status()
                                if hasattr(estado_actual, 'output_path') and estado_actual.output_path:
                                    ruta_original = Path(estado_actual.output_path)
                                    logging.info(f"✓ Ruta obtenida desde estado: {ruta_original}")
                            except:
                                pass
                    
                    except Exception as e:
                        logging.error(f"Error al detener grabación: {e}")
                        # Intentar obtener el archivo de todas formas
                        try:
                            estado_grabacion = self.cliente_obs.get_record_status()
                            if hasattr(estado_grabacion, 'output_path') and estado_grabacion.output_path:
                                ruta_original = Path(estado_grabacion.output_path)
                                logging.info(f"✓ Ruta obtenida desde estado después del error: {ruta_original}")
                        except:
                            logging.warning("No se pudo obtener la ruta del archivo después del error")
                
                else:
                    logging.warning("ADVERTENCIA: No hay grabación activa para detener")
                    logging.warning("Esto puede significar que la grabación nunca se inició correctamente")
            
            except Exception as e:
                logging.error(f"Error al verificar estado antes de detener: {e}")
                logging.warning("Continuando sin detener grabación...")
            
            # Si no se obtuvo la ruta, intentar una vez más
            if not ruta_original:
                try:
                    estado_final = self.cliente_obs.get_record_status()
                    if hasattr(estado_final, 'output_path') and estado_final.output_path:
                        ruta_original = Path(estado_final.output_path)
                        logging.info(f"✓ Ruta obtenida en verificación final: {ruta_original}")
                except:
                    pass
            
            logging.info("=" * 70)
            
            return ruta_original
        
        except Exception as e:
            logging.error(f"ERROR al detener grabación: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def verificar_grabacion_activa(self) -> bool:
        """
        Verifica si hay una grabación activa en OBS.
        
        Returns:
            bool: True si hay grabación activa, False en caso contrario.
        """
        if not self.verificar_conexion():
            return False
        
        try:
            estado_grabacion = self.cliente_obs.get_record_status()
            return hasattr(estado_grabacion, 'output_active') and estado_grabacion.output_active
        except:
            return False
    
    def asegurar_grabacion_detenida(self) -> None:
        """
        Asegura que no haya ninguna grabación activa.
        
        Si hay una grabación activa, la detiene.
        """
        if not self.verificar_conexion():
            return
        
        try:
            estado_grabacion = self.cliente_obs.get_record_status()
            if hasattr(estado_grabacion, 'output_active') and estado_grabacion.output_active:
                logging.warning("Aún hay grabación activa. Forzando detención...")
                self.cliente_obs.stop_record()
                time.sleep(2)
        except:
            pass
    
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
    
    def desconectar(self) -> None:
        """Cierra la conexión con OBS Studio."""
        if self.cliente_obs:
            # Asegurar que no hay grabación activa
            self.asegurar_grabacion_detenida()
            self.cliente_obs = None
            self.conectado = False
            logging.info("✓ Desconectado de OBS Studio")

