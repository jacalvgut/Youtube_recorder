"""
Módulo para gestionar la conexión con OBS Studio.

Este módulo se encarga de:
- Conectar con OBS Studio vía WebSocket
- Verificar conexión
- Manejar errores de conexión
"""

import logging
from typing import Optional
import obsws_python as obs
from obsws_python.error import OBSSDKError
import config


def conectar_obs() -> Optional[obs.ReqClient]:
    """
    Conecta con OBS Studio a través del WebSocket.
    
    Returns:
        obs.ReqClient si la conexión fue exitosa, None en caso contrario.
    """
    logging.info("=" * 70)
    logging.info("VERIFICACIÓN: Conectando con OBS Studio...")
    logging.info("=" * 70)
    
    try:
        password_info = "con contraseña" if config.OBS_PASSWORD else "sin contraseña"
        logging.info(f"Conectando a OBS en {config.OBS_HOST}:{config.OBS_PORT} ({password_info})...")
        
        cliente_obs = obs.ReqClient(
            host=config.OBS_HOST,
            port=config.OBS_PORT,
            password=config.OBS_PASSWORD,
            timeout=10
        )
        
        # Verificar la conexión obteniendo la versión
        version = cliente_obs.get_version()
        logging.info(f"✓ Conexión con OBS exitosa")
        logging.info(f"  - Versión de OBS: {version.obs_version}")
        logging.info(f"  - Versión del plugin WebSocket: {version.obs_web_socket_version}")
        logging.info("=" * 70)
        
        return cliente_obs
    
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
        return None
    
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
        return None
    
    except Exception as e:
        logging.error("=" * 70)
        logging.error(f"ERROR inesperado al conectar con OBS: {e}")
        logging.error("=" * 70)
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        return None


def verificar_conexion_obs(cliente_obs: Optional[obs.ReqClient]) -> bool:
    """
    Verifica que la conexión con OBS esté activa.
    
    Args:
        cliente_obs: Cliente de OBS a verificar.
    
    Returns:
        bool: True si está conectado, False en caso contrario.
    """
    if not cliente_obs:
        return False
    
    try:
        cliente_obs.get_version()
        return True
    except:
        return False

