import pyMeow as pm
import math

proc = pm.open_process("hl2.exe")

class Modules:
    base = pm.get_module(proc,"hl2.exe")["base"]
    server = pm.get_module(proc,"server.dll")["base"]
    engine = pm.get_module(proc,"engine.dll")["base"]
    client = pm.get_module(proc,"client.dll")["base"]
    inputsystem = pm.get_module(proc,"inputsystem.dll")["base"]

class Addresses:
    ent_count = Modules.server+0x94C014
    direction = Modules.server + 0xA1C754
    screen_resolution = Modules.client + 0x7C9B1C
    xfov = Modules.client+0x7C9C08
    cam_pos = Modules.client + 0x6FE1C8
    cam_orientation = Modules.engine+0x50584C
    shooting = Modules.inputsystem+0x26600

class Pointers:
    ent_list = Modules.server + 0x94C008
    player_base = Modules.server + 0xA2A014

class Offsets:
    health = 0xE0
    ent_dist = 0x4
    name = 0x438
    position = 0x28

class Entity:
    def __init__(self,base):
        self.base = base
        self.h = self.base+Offsets.health
        self.pos = self.base+Offsets.position
        self.n = self.base+Offsets.name
    def health(self):
        return pm.r_int(proc,self.h)
    def position(self):
        return pm.r_floats(proc,self.pos,3)
    def name(self):
        return pm.r_string(proc,self.n,30)
    
def entities():
    ncount = pm.r_int(proc,Addresses.ent_count)
    ent_list = pm.r_int(proc,Pointers.ent_list)
    if ncount ==0:
        return []
    ents = pm.r_uints(proc,ent_list,ncount)
    return [Entity(i) for i in ents]

def wts(worldpos,x_fov,y_fov,cam_pos):
    camPitch,camYaw = [math.radians(i) for i in pm.r_floats(proc,Addresses.cam_orientation,2)]
    camPitch *= -1
    camToObj = [worldpos[i]-cam_pos[i] for i in range(3)]
    distToObj = math.sqrt(sum([camToObj[i]**2 for i in range(3)]))
    if distToObj == 0:
        distToObj = 0.0001
    camToObj = [i/distToObj for i in camToObj]
    objYaw = math.atan2(camToObj[1],camToObj[0])
    relYaw = camYaw-objYaw
    objPitch = math.asin(camToObj[2])
    relPitch = camPitch-objPitch

    x = relYaw/(0.5*x_fov)
    y = relPitch/(0.5*y_fov)
    x = (x+1)/2
    y = (y+1)/2
    return x*screen_width,y*screen_height,distToObj,[-math.degrees(objPitch),math.degrees(objYaw)]

def calculated_overlay(ents,cam_pos):
    x_fov = math.radians(pm.r_float(proc,Addresses.xfov))
    y_fov = x_fov/screen_width * screen_height
    pos = ents[0].position()
    x,y,dist,aimto = wts(pos,x_fov,y_fov,cam_pos)        
    pm.draw_text(ents[0].name(),x,y,20/dist,Colors.cyan)
    mindist = dist
    ment = ents[0]
    for i in ents[1:]:
        pos = i.position()
        x,y,dist,aimed = wts(pos,x_fov,y_fov,cam_pos)   
        if dist < mindist:
            mindist = dist
            ment = i     
            aimto=aimed
        pm.draw_text(i.name(),x,y,20/dist,Colors.cyan)
    return ment.position(),aimto

def is_shooting():
    return pm.r_int(proc,Addresses.shooting) == 2048

class Colors:
    cyan = pm.get_color("cyan")
    red = pm.get_color("red")
    green = pm.get_color("lime")

def calculate_angles(cam_pos, target_pos):
    dir_vector = [target_pos[0] - cam_pos[0], target_pos[1] - cam_pos[1], target_pos[2] - cam_pos[2]]
    yaw = math.atan2(dir_vector[1], dir_vector[0]) * (180 / math.pi)
    yaw = yaw if yaw >= 0 else yaw + 360  
    hyp = math.sqrt(dir_vector[0] ** 2 + dir_vector[1] ** 2)
    pitch = math.atan2(-dir_vector[2], hyp) * (180 / math.pi)
    return [pitch, yaw]

pm.overlay_init(target="Garry's Mod", fps=144, trackTarget=True)
screen_width,screen_height = pm.r_ints(proc,Addresses.screen_resolution,2)
ply = pm.r_int(proc,Pointers.player_base)

while pm.overlay_loop():
    ents = entities()
    cam_pos = pm.r_floats(proc,Addresses.cam_pos,3)
    pm.begin_drawing()
    if len(ents)>0:
        closest,aimto = calculated_overlay(ents,cam_pos)
    if is_shooting() and len(ents)>0:
        pm.w_floats(proc,Addresses.cam_orientation,aimto)

    

    pm.end_drawing()



