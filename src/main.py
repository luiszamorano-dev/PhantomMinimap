import argparse
import configparser
import sys
import time
import logging
from src.minimap_capture import MinimapCapture
from src.fake_map_generator import FakeMapGenerator
from src.obs_integration import OBSIntegration
from src.champion_detector import ChampionDetector

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("minimapa_fantasmal.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Main")

def main():
    parser = argparse.ArgumentParser(description='Minimapa Fantasmal - Protección contra stream snipers')
    parser.add_argument('--obs', action='store_true', help='Usar integración con OBS')
    parser.add_argument('--overwolf', action='store_true', help='Usar integración con Overwolf (próximamente)')
    parser.add_argument('--debug', action='store_true', help='Modo depuración con visualización')
    args = parser.parse_args()
    
    # Cargar configuración
    config = configparser.ConfigParser()
    config.read('config/config.ini')
    
    # Inicializar componentes
    logger.info("Inicializando componentes...")
    capture = MinimapCapture()
    generator = FakeMapGenerator()
    detector = ChampionDetector()
    
    # Configurar capturador
    capture.set_auto_detect(config.getboolean('Minimap', 'auto_detect', fallback=True))
    if not capture.auto_detect:
        width = config.getint('Minimap', 'custom_width', fallback=320)
        height = config.getint('Minimap', 'custom_height', fallback=320)
        capture.set_custom_size(width, height)
    
    # Configurar generador
    fakeness = config.getint('Behavior', 'fakeness_level', fallback=7)
    generator.config['fakeness_level'] = fakeness
    
    # Intentar detectar composición de equipos
    try:
        logger.info("Detectando composición de equipos...")
        screenshot = capture.capture_full_screen()
        if screenshot is not None:
            composition = detector.detect_champions_loading_screen(screenshot)
            if composition:
                generator.set_team_composition(composition)
                logger.info(f"Composición detectada: Aliados={composition['aliados']}, Enemigos={composition['enemigos']}")
    except Exception as e:
        logger.error(f"Error detectando composición: {e}")
    
    # Modo OBS
    if args.obs:
        obs_host = config.get('OBS', 'host', fallback='localhost')
        obs_port = config.getint('OBS', 'port', fallback=4444)
        obs_password = config.get('OBS', 'password', fallback='')
        
        obs_integration = OBSIntegration(obs_host, obs_port, obs_password)
        if not obs_integration.start_streaming_fake_minimap(capture, generator):
            logger.error("No se pudo iniciar la transmisión a OBS")
            sys.exit(1)
        
        logger.info("Transmisión a OBS iniciada correctamente")
    
    # Modo Overwolf (próximamente)
    elif args.overwolf:
        logger.info("Soporte para Overwolf en desarrollo")
        # Implementación futura
    
    # Modo depuración
    if args.debug:
        import cv2
        logger.info("Iniciando modo depuración...")
        
        try:
            while True:
                # Capturar minimapa
                minimap_frame = capture.capture_minimap()
                if minimap_frame is None:
                    time.sleep(1)
                    continue
                
                # Detectar posiciones (simulado)
                real_allies, real_enemies = capture.detect_icons(minimap_frame)
                
                # Generar overlay falso
                fake_overlay = generator.generate_fake_map(minimap_frame, real_allies, real_enemies)
                
                # Convertir para visualización
                minimap_display = cv2.cvtColor(minimap_frame, cv2.COLOR_RGB2BGR)
                overlay_display = cv2.cvtColor(np.array(fake_overlay.convert('RGB')), cv2.COLOR_RGB2BGR)
                
                # Mostrar resultados
                cv2.imshow('Minimapa Real', minimap_display)
                cv2.imshow('Overlay Falso', overlay_display)
                
                # Salir con 'q'
                if cv2.waitKey(500) & 0xFF == ord('q'):
                    break
        finally:
            cv2.destroyAllWindows()
    
    # Mantener el programa en ejecución
    try:
        if args.obs:
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Deteniendo por interrupción de usuario")
    finally:
        if args.obs:
            obs_integration.stop()
        logger.info("Aplicación finalizada")

if __name__ == "__main__":
    main()