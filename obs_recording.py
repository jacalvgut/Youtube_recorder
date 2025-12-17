"""
Módulo para gestionar grabaciones en OBS Studio.

Este módulo se encarga de:
- Iniciar grabaciones
- Detener grabaciones
- Verificar estado de grabaciones
- Obtener rutas de archivos grabados
"""

import time
import logging
from pathlib import Path
from typing import Optional
import obsws_python as obs


def iniciar_grabacion_obs(cliente_obs: obs.ReqClient) -> bool:
    """
    Inicia una grabación en OBS Studio.
    
    Args:
        cliente_obs: Cliente de OBS conectado.
    
    Returns:
        bool: True si la grabación se inició correctamente, False en caso contrario.
    """
    try:
        logging.info("")
        logging.info("=" * 70)
        logging.info("VERIFICACIÓN: Iniciando grabación en OBS...")
        logging.info("=" * 70)
        
        # Verificar que no hay grabación activa antes de iniciar
        try:
            estado_antes = cliente_obs.get_record_status()
            if estado_antes.output_active:
                logging.warning("Hay una grabación activa. Deteniéndola antes de iniciar nueva...")
                detener_grabacion_obs(cliente_obs)
                time.sleep(2)
        except:
            pass
        
        # Iniciar la grabación
        logging.info("Ejecutando cliente_obs.start_record()...")
        try:
            resultado_start = cliente_obs.start_record()
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
        
        while intentos_verificacion < 10:
            try:
                estado_grabacion = cliente_obs.get_record_status()
                
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


def detener_grabacion_obs(cliente_obs: obs.ReqClient) -> Optional[Path]:
    """
    Detiene la grabación activa en OBS Studio.
    
    Args:
        cliente_obs: Cliente de OBS conectado.
    
    Returns:
        Path: Ruta al archivo grabado si se obtuvo correctamente, None en caso contrario.
    """
    try:
        logging.info("")
        logging.info("=" * 70)
        logging.info("VERIFICACIÓN: Verificando estado de grabación antes de detener...")
        logging.info("=" * 70)
        
        ruta_original = None
        
        # Verificar si hay una grabación activa antes de intentar detenerla
        try:
            estado_antes_detener = cliente_obs.get_record_status()
            
            if hasattr(estado_antes_detener, 'output_active') and estado_antes_detener.output_active:
                logging.info("✓ Hay una grabación activa. Deteniéndola...")
                
                try:
                    info_grabacion = cliente_obs.stop_record()
                    time.sleep(2)  # Esperar a que se detenga completamente
                    
                    # Verificar que la grabación se detuvo
                    estado_despues = cliente_obs.get_record_status()
                    if hasattr(estado_despues, 'output_active') and estado_despues.output_active:
                        logging.warning("ADVERTENCIA: La grabación aún está activa. Forzando detención...")
                        cliente_obs.stop_record()
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
                            estado_actual = cliente_obs.get_record_status()
                            if hasattr(estado_actual, 'output_path') and estado_actual.output_path:
                                ruta_original = Path(estado_actual.output_path)
                                logging.info(f"✓ Ruta obtenida desde estado: {ruta_original}")
                        except:
                            pass
                
                except Exception as e:
                    logging.error(f"Error al detener grabación: {e}")
                    # Intentar obtener el archivo de todas formas
                    try:
                        estado_grabacion = cliente_obs.get_record_status()
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
                estado_final = cliente_obs.get_record_status()
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


def verificar_grabacion_activa(cliente_obs: obs.ReqClient) -> bool:
    """
    Verifica si hay una grabación activa en OBS.
    
    Args:
        cliente_obs: Cliente de OBS conectado.
    
    Returns:
        bool: True si hay grabación activa, False en caso contrario.
    """
    try:
        estado_grabacion = cliente_obs.get_record_status()
        return hasattr(estado_grabacion, 'output_active') and estado_grabacion.output_active
    except:
        return False


def asegurar_grabacion_detenida(cliente_obs: obs.ReqClient) -> None:
    """
    Asegura que no haya ninguna grabación activa.
    
    Args:
        cliente_obs: Cliente de OBS conectado.
    """
    try:
        estado_grabacion = cliente_obs.get_record_status()
        if hasattr(estado_grabacion, 'output_active') and estado_grabacion.output_active:
            logging.warning("Aún hay grabación activa. Forzando detención...")
            cliente_obs.stop_record()
            time.sleep(2)
    except:
        pass

