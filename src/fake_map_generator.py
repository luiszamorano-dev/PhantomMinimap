import cv2
import numpy as np
from PIL import Image, ImageDraw
import json
import os
import random
from .champion_db import ChampionDatabase

class FakeMapGenerator:
    def __init__(self, config_path='config/config.ini'):
        self.champion_db = ChampionDatabase()
        self.minimap_size = (320, 320)  # Tamaño por defecto
        self.team_composition = {"aliados": [], "enemigos": []}
        self.icon_cache = {}
        self.config = {
            'fakeness_level': 7,
            'icon_size': 12,
            'icon_path': 'assets/icons/'
        }
        self.load_icons()
    
    def load_icons(self):
        """Carga los iconos de campeones desde el directorio"""
        icon_path = self.config['icon_path']
        if os.path.exists(icon_path):
            for champ_file in os.listdir(icon_path):
                if champ_file.endswith('.png'):
                    champ_name = os.path.splitext(champ_file)[0]
                    self.icon_cache[champ_name] = Image.open(os.path.join(icon_path, champ_file))
    
    def set_minimap_size(self, width, height):
        """Actualiza el tamaño del minimapa"""
        self.minimap_size = (width, height)
    
    def set_team_composition(self, composition):
        """Establece la composición de equipos"""
        self.team_composition = composition
        print(f"Composición de equipos actualizada: {composition}")
    
    def generate_fake_positions(self, real_positions, team):
        """
        Genera posiciones falsas para un equipo
        :param real_positions: Lista de posiciones reales (x, y)
        :param team: 'ally' o 'enemy'
        :return: Lista de posiciones falsas (x, y)
        """
        fake_positions = []
        map_zones = self.get_map_zones(team)
        
        for real_pos in real_positions:
            # Seleccionar una zona válida basada en la posición real
            if team == 'ally' and self.is_in_base(real_pos, 'ally'):
                zone = 'jungle'  # Mover aliados de base a jungla
            elif team == 'enemy' and self.is_in_base(real_pos, 'enemy'):
                zone = 'jungle'  # Mover enemigos de base a jungla
            else:
                # Mantener en la misma zona o mover a adyacente
                current_zone = self.get_position_zone(real_pos)
                adjacent_zones = self.get_adjacent_zones(current_zone)
                zone = random.choice(adjacent_zones)
            
            # Generar posición aleatoria en la zona seleccionada
            x_min, y_min, x_max, y_max = map_zones[zone]
            new_x = random.randint(x_min, x_max)
            new_y = random.randint(y_min, y_max)
            
            fake_positions.append((new_x, new_y))
        
        return fake_positions
    
    def get_map_zones(self, team):
        """Define las zonas del mapa con coordenadas relativas"""
        # Coordenadas basadas en un minimapa de 320x320
        scale_x = self.minimap_size[0] / 320
        scale_y = self.minimap_size[1] / 320
        
        zones = {
            'ally_base': (10, 10, 80, 80),
            'enemy_base': (240, 240, 310, 310),
            'top_lane': (100, 30, 220, 80),
            'mid_lane': (130, 130, 190, 190),
            'bot_lane': (100, 240, 220, 290),
            'river': (110, 110, 210, 210),
            'ally_jungle_top': (50, 80, 110, 140),
            'ally_jungle_bot': (50, 180, 110, 240),
            'enemy_jungle_top': (210, 80, 270, 140),
            'enemy_jungle_bot': (210, 180, 270, 240)
        }
        
        # Escalar zonas según el tamaño real del minimapa
        scaled_zones = {}
        for zone, coords in zones.items():
            scaled_zones[zone] = (
                int(coords[0] * scale_x),
                int(coords[1] * scale_y),
                int(coords[2] * scale_x),
                int(coords[3] * scale_y)
            )
        
        return scaled_zones
    
    def is_in_base(self, position, team):
        """Determina si una posición está en la base del equipo"""
        x, y = position
        base_zones = self.get_map_zones(team)
        base = base_zones['ally_base'] if team == 'ally' else base_zones['enemy_base']
        return base[0] <= x <= base[2] and base[1] <= y <= base[3]
    
    def get_position_zone(self, position):
        """Determina en qué zona está una posición"""
        x, y = position
        zones = self.get_map_zones('ally')  # Las zonas son las mismas para ambos equipos
        
        for zone, coords in zones.items():
            if coords[0] <= x <= coords[2] and coords[1] <= y <= coords[3]:
                return zone
        
        return 'river'  # Zona por defecto
    
    def get_adjacent_zones(self, current_zone):
        """Devuelve zonas adyacentes válidas"""
        adjacency_map = {
            'ally_base': ['ally_jungle_top', 'ally_jungle_bot', 'top_lane', 'bot_lane'],
            'enemy_base': ['enemy_jungle_top', 'enemy_jungle_bot', 'top_lane', 'bot_lane'],
            'top_lane': ['ally_base', 'enemy_base', 'ally_jungle_top', 'enemy_jungle_top', 'river'],
            'mid_lane': ['river', 'ally_jungle_top', 'ally_jungle_bot', 'enemy_jungle_top', 'enemy_jungle_bot'],
            'bot_lane': ['ally_base', 'enemy_base', 'ally_jungle_bot', 'enemy_jungle_bot', 'river'],
            'river': ['top_lane', 'mid_lane', 'bot_lane', 'ally_jungle_top', 'ally_jungle_bot', 
                     'enemy_jungle_top', 'enemy_jungle_bot'],
            'ally_jungle_top': ['ally_base', 'top_lane', 'mid_lane', 'river'],
            'ally_jungle_bot': ['ally_base', 'bot_lane', 'mid_lane', 'river'],
            'enemy_jungle_top': ['enemy_base', 'top_lane', 'mid_lane', 'river'],
            'enemy_jungle_bot': ['enemy_base', 'bot_lane', 'mid_lane', 'river']
        }
        
        return adjacency_map.get(current_zone, ['river'])
    
    def generate_fake_map(self, minimap_frame, real_ally_positions, real_enemy_positions):
        """
        Genera un overlay con posiciones falsas
        :param minimap_frame: Frame del minimapa real
        :param real_ally_positions: Lista de posiciones de aliados [(x,y), ...]
        :param real_enemy_positions: Lista de posiciones de enemigos [(x,y), ...]
        :return: Imagen RGBA (PNG) con el overlay falso
        """
        # Crear imagen transparente del mismo tamaño que el minimapa
        overlay = Image.new('RGBA', (minimap_frame.shape[1], minimap_frame.shape[0]), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Generar posiciones falsas
        fake_ally_positions = self.generate_fake_positions(real_ally_positions, 'ally')
        fake_enemy_positions = self.generate_fake_positions(real_enemy_positions, 'enemy')
        
        # Dibujar aliados
        for i, pos in enumerate(fake_ally_positions):
            champ_name = self.team_composition['aliados'][i] if i < len(self.team_composition['aliados']) else 'default'
            self.draw_champion_icon(overlay, pos, champ_name, 'ally')
        
        # Dibujar enemigos
        for i, pos in enumerate(fake_enemy_positions):
            champ_name = self.team_composition['enemigos'][i] if i < len(self.team_composition['enemigos']) else 'default'
            self.draw_champion_icon(overlay, pos, champ_name, 'enemy')
        
        return overlay
    
    def draw_champion_icon(self, overlay, position, champion_name, team):
        """Dibuja el icono de un campeón en la posición especificada"""
        x, y = position
        icon_size = self.config['icon_size']
        
        # Obtener icono del campeón
        icon = self.icon_cache.get(champion_name.lower(), None)
        
        if icon:
            # Redimensionar icono
            icon = icon.resize((icon_size, icon_size))
            # Calcular posición para centrar
            pos_x = x - icon_size // 2
            pos_y = y - icon_size // 2
            # Pegar icono en el overlay
            overlay.paste(icon, (pos_x, pos_y), icon)
        else:
            # Dibujar círculo de color si no hay icono
            color = (0, 0, 255, 180) if team == 'ally' else (255, 0, 0, 180)
            draw = ImageDraw.Draw(overlay)
            draw.ellipse([(x-5, y-5), (x+5, y+5)], fill=color)

if __name__ == "__main__":
    # Prueba básica
    generator = FakeMapGenerator()
    
    # Establecer composición de equipo de ejemplo
    generator.set_team_composition({
        "aliados": ["Ashe", "Jinx", "Garen"],
        "enemigos": ["Zed", "Yasuo", "Darius"]
    })
    
    # Posiciones de ejemplo
    real_allies = [(50, 50), (60, 60), (70, 70)]
    real_enemies = [(250, 250), (240, 240), (230, 230)]
    
    # Generar overlay falso
    fake_overlay = generator.generate_fake_map(
        np.zeros((320, 320, 3), dtype=np.uint8),  # Minimapa vacío de prueba
        real_allies,
        real_enemies
    )
    
    # Guardar resultado
    fake_overlay.save("test_overlay.png")