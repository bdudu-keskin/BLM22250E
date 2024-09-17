import sys
import pygame
import random
import math
import os

from scripts.entities import PhysicsEntity, Player, Enemy, WorldItem
from scripts.utils import load_image, load_images, Animation
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particle import Particle
from scripts.spark import Spark



class Game:
  def __init__(self):
    pygame.init()
    pygame.display.set_caption('AAAAAAAAAA')

    self.screen = pygame.display.set_mode((640, 480))
    self.display = pygame.Surface((320,240),pygame.SRCALPHA)
    self.display_2= pygame.Surface((320,240))

    self.clock = pygame.time.Clock()

    self.movement= [False, False]
    self.last_inventory= []



    self.assets={
      'decor': load_images('tiles/decor'),
      'grass': load_images('tiles/grass'),
      'large_decor': load_images('tiles/large_decor'),
      'stone': load_images('tiles/stone'),
      'player': load_image('entities/player.png'),
      'background': load_image('background.png'), 
      'clouds': load_images('clouds'),

      'enemy/idle': Animation(self.transform_player_sprite(load_images('entities/enemy/idle')), img_dur=6),
      'enemy/run': Animation(self.transform_player_sprite(load_images('entities/enemy/run')), img_dur=4),
      'player/idle': Animation(self.transform_player_sprite(load_images('entities/player/idle')), img_dur=6),
      'player/run': Animation(self.transform_player_sprite(load_images('entities/player/_run')), img_dur=4),
      'player/jump': Animation(self.transform_player_sprite(load_images('entities/player/_jump'))),
      'player/slide': Animation(load_images('entities/player/slide')),
      'player/wall_slide': Animation(self.transform_player_sprite(load_images('entities/player/_wallslide'))),
      'player/dash_attack': Animation(self.transform_player_sprite(load_images('entities/player/dashattack')), img_dur=10),
      'particle/leaf': Animation(load_images('particles/leaf'), img_dur = 20, loop = False),
      'particle/particle': Animation(load_images('particles/particle'), img_dur = 6, loop = False),
      'gun': load_image('gun.png'),
      'projectile': load_image('Projectile.png'),
      'items/testItem': Animation([load_image('entities/items/testItem.png')]),
      'items/bigLeap': Animation([load_image('entities/items/bigLeap.png')]),
      'items/dashBounce': Animation([load_image('entities/items/dashBounce.png')]),
      'items/downDash': Animation([load_image('entities/items/downDash.png')]),
      'items/coin': Animation(load_images('entities/items/coin')),
    }



    self.clouds = Clouds(self.assets['clouds'], count = 16)
    self.player = Player(self, (50,50), (8,15))
    self.tilemap = Tilemap(self, tile_size = 16)
    self.level = 1
    self.load_level(self.level)
    self.screenshake = 0
    


  def transform_player_sprite(self, surfaceList): 
    temp = [pygame.transform.scale(x, (43, 43))
            .subsurface(14, 14, 20, 20)
            for x in surfaceList]
    
    return temp 



  def load_level(self, map_id):
    self.tilemap.load('rs/data/maps/' + str(map_id) + '.json')
    #self.tilemap.load('rs/data/maps/7.json')
    self.last_inventory = [x for x in self.player.inventory]

    self.leaf_spawners = []
    for tree in self.tilemap.extract([('large_decor', 2)], keep = True):
      self.leaf_spawners.append(pygame.Rect(4 + tree['pos'][0], 4 + tree['pos'][1], 23, 13)) 

    self.items = []
    self.enemies = []
    extracted = self.tilemap.extract([('spawners', x) for x in range(0, 100)])
    for spawner in extracted:
      variant = spawner['variant']      
      if variant == 0:
        self.player.pos = spawner['pos']
        self.player.air_time = 0

      elif variant == 1:
        self.enemies.append(Enemy(self, spawner['pos'], (8, 15)))

      else:
        self.items.append(WorldItem(self, spawner['pos'], WorldItem.item_types[variant - 2]))

    self.projectile = []
    self.particles = []
    self.sparks = []
    self.scroll = [0,0]
    self.dead = 0
    self.transition = -30



  def run(self):
    while True:
      self.display.fill((0, 0, 0, 0))
      self.display_2.blit(self.assets['background'], (0, 0))
      self.screenshake = max(0,self.screenshake - 1)

      if not len(self.items ) and not len(self.enemies):
        self.transition +=1
        if self.transition > 30:
          self.level = min(self.level + 1, len(os.listdir('rs/data/maps/')))
          self.player.inventory = []
          self.load_level(self.level)

      if self.transition < 0:
        self.transition +=1

      if self.dead:
        self.dead += 1
        if self.dead >= 10:
          self.transition = min(30, self.transition+1)
        if self.dead > 40:
          self.player.inventory = self.last_inventory
          self.load_level(self.level)

      self.scroll[0] += (self.player.rect().centerx - self.display.get_width()/2 - self.scroll[0]) / 30
      self.scroll[1] += (self.player.rect().centery - self.display.get_height()/2 - self.scroll[1]) / 30

      render_scroll= (int(self.scroll[0]), int(self.scroll[1]))

      for rect in self.leaf_spawners:
        if random.random() * 49999 < rect.width* rect.height:
          pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
          self.particles.append(Particle(self, 'particle', pos, velocity = [-0.1, 0.3], frame = random.randint(0, 20)))

      self.clouds.update()
      self.clouds.render(self.display_2, offset = render_scroll)

      self.tilemap.render(self.display, offset = self.scroll)

      for enemy in self.enemies.copy():
        kill = enemy.update(self.tilemap, (0, 0))
        enemy.render(self.display, offset = render_scroll)
        if kill:
          self.enemies.remove(enemy)

      for item in self.items.copy():
        collected = item.update(self.tilemap, (0, 0))
        item.render(self.display, offset = render_scroll)
        if collected:
          self.items.remove(item)

      if not self.dead:
        self.player.update(self.tilemap, (self.movement[1] - self.movement[0],0))
        self.player.render(self.display, offset=render_scroll)

      for projectile in self.projectile.copy():
        projectile[0][0] += projectile[1]
        projectile[2] += 1
        img = self.assets['projectile']

        self.display.blit(
          pygame.transform.flip(img,
                                projectile[1] < 0,
                                False), 
                                (projectile[0][0] - img.get_width() / 2 - render_scroll[0],
                                 projectile[0][1] - img.get_height() / 2 - render_scroll[1]))
        
        if self.tilemap.solid_check(projectile[0]):
          self.projectile.remove(projectile)

          for i in range (4):
            self.sparks.append(Spark(projectile[0],
                                     random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0),
                                     2 + random.random()))

        elif projectile[2] > 360: 
          self.projectile.remove(projectile)

        elif abs(self.player.dashing) < 50:
          if self.player.rect().collidepoint(projectile[0]):
            self.projectile.remove(projectile)
            self.dead += 1
            self.screenshake = max(16, self.screenshake)
            for i in range(30):
              angle = random.random() * math.pi * 2
              speed = random.random() * 5
              self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random()))
              self.particles.append(Particle(self, 'particle', self.player.rect().center,
                                             velocity = [math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5],
                                             frame = random.randint(0, 7)))

      for spark in self.sparks.copy():
        kill = spark.update()
        spark.render(self.display, offset = render_scroll)
        if kill:
          self.sparks.remove(spark)
      
      display_mask =pygame.mask.from_surface(self.display)
      display_sillhouette= display_mask.to_surface(setcolor=(0,0,0,180),
                                                   unsetcolor=(0,0,0,0))
      
      for offset in [(-1,0), (1,0), (0,-1),(0,1)]:
        self.display_2.blit(display_sillhouette, offset)

      for particle in self.particles.copy():
        kill = particle.update()
        particle.render(self.display, offset = render_scroll)
        if particle.type == 'leaf':
          particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
        if kill:
          self.particles.remove(particle)



      if self.player.inventory_open:
        pygame.draw.rect(self.display, 
                         (70,70,70), 
                         pygame.Rect(20, 10, 254, 100))
        
        pygame.draw.rect(self.display,
                         (100,100,100), 
                         pygame.Rect(25, 15, 244, 90))

        selected_item = None
        mouse_pos = tuple(x * self.display.get_size()[0]/self.screen.get_size()[0] 
                          for x in pygame.mouse.get_pos())
        item_size = (16, 16)
        item_per_row = 12

        for index, item in enumerate(self.player.inventory):
          item_pos = (30 + (item_size[0] + 4)*(index % item_per_row),
                      20 + (item_size[1] + 4)*math.floor(index / item_per_row))
          
          item.render(self.display,item_pos)

          if(item_pos[0] < mouse_pos[0] < item_pos[0] + item_size[0] 
            and item_pos[1] < mouse_pos[1] < item_pos[1] + item_size[1]):
            selected_item = item

        if(selected_item != None):
          selected_item.render_desc(self.display,mouse_pos)

      for event in pygame.event.get():

        if event.type == pygame.QUIT:
          pygame.quit()
          sys.exit()

        if event.type == pygame.KEYDOWN:
          if event.key == pygame.K_a:
            self.movement[0]= True
          if event.key == pygame.K_d:
            self.movement[1]= True
          if event.key == pygame.K_w:
            self.player.jump()
          if event.key == pygame.K_SPACE:
            self.player.dash(False)
          if event.key == pygame.K_s:
            if self.player.has_in_inventory('Down Dash'):
              self.player.dash(True)
          if event.key == pygame.K_e:
            self.player.inventory_open = not self.player.inventory_open

        if event.type == pygame.KEYUP:
          if event.key == pygame.K_a:
            self.movement[0]= False
          if event.key == pygame.K_d:
            self.movement[1]= False
      
      if self.transition:
        transition_surf = pygame.Surface(self.display.get_size())
        pygame.draw.circle(transition_surf,
                           (255,255,255),
                           (self.display.get_width()//2, self.display.get_height()//2),
                           (30-abs(self.transition))*8)
        transition_surf.set_colorkey((255,255,255))
        self.display.blit(transition_surf, (0,0))
      
      self.display_2.blit(self.display,(0,0))
      screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2,
                            random.random() * self.screenshake - self.screenshake / 2 )
      self.screen.blit (pygame.transform.scale(self.display_2, self.screen.get_size()),screenshake_offset)
      pygame.display.update()
      self.clock.tick(60)

Game().run()