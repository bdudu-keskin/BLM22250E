import pygame

class Item:
    def __init__ (self, name, desc, sprite):
        self.name = name
        self.desc = desc
        self.sprite = sprite
    
    def render(self, surf, pos):
        surf.blit(
            self.sprite.img(),
            pos
        )

    def render_desc(self, surf, pos):
        big_font = pygame.font.Font(pygame.font.get_default_font(), 12)
            
        text = big_font.render(self.name, True, (0, 0, 0), (255, 255, 255))

        addY = text.get_size()[1]

        font = pygame.font.Font(pygame.font.get_default_font(), 10)
        
        desc = font.render(self.desc, True, (0, 0, 0), (255, 255, 255))
        
        surf.blit(
            text,
            pos
        )
        surf.blit(
            desc,
            (pos[0], pos[1] + addY)
        ) 


class Collectible(Item):
    def __init__(self, name, desc, sprite):
        super().__init__(name, desc, sprite)
        pass



class PowerUp(Item):
    def __init__(self, name, desc, sprite):
        super().__init__(name, desc, sprite)
        pass