import ctypes as C,sys,json,time,os
from pathlib import Path
from PIL import Image
ROOT=Path(os.environ['SRW_TEST_ROOT']).resolve()
CORE=Path(os.environ['SRW_CORE'])
core=C.CDLL(str(CORE))
class Variable(C.Structure):_fields_=[('key',C.c_char_p),('value',C.c_char_p)]
class Game(C.Structure):_fields_=[('path',C.c_char_p),('data',C.c_void_p),('size',C.c_size_t),('meta',C.c_char_p)]
class SystemInfo(C.Structure):_fields_=[('name',C.c_char_p),('version',C.c_char_p),('extensions',C.c_char_p),('need_fullpath',C.c_bool),('block_extract',C.c_bool)]
ENV=C.CFUNCTYPE(C.c_bool,C.c_uint,C.c_void_p);VIDEO=C.CFUNCTYPE(None,C.c_void_p,C.c_uint,C.c_uint,C.c_size_t);AUDIO=C.CFUNCTYPE(None,C.c_int16,C.c_int16);BATCH=C.CFUNCTYPE(C.c_size_t,C.c_void_p,C.c_size_t);POLL=C.CFUNCTYPE(None);INPUT=C.CFUNCTYPE(C.c_int16,C.c_uint,C.c_uint,C.c_uint,C.c_uint)
settings={};retained=[];fmt=1;last=None;frame=0;render_frames=None;buttons=set();system=str(ROOT/'system').encode();savedir=str(ROOT/'saves').encode();Path(savedir.decode()).mkdir(exist_ok=True)
@ENV
def environment(cmd,data):
 global fmt
 if cmd in [9,30,31]:C.cast(data,C.POINTER(C.c_char_p))[0]=savedir if cmd==31 else system;return True
 if cmd==10:fmt=C.cast(data,C.POINTER(C.c_int))[0];return fmt in [0,1,2]
 if cmd==16:
  vars=C.cast(data,C.POINTER(Variable));i=0
  while vars[i].key:
   key=vars[i].key;value=vars[i].value.split(b';',1)[1].strip().split(b'|')[0];settings[key]=value;retained.extend([key,value]);i+=1
  return True
 if cmd==15:
  v=C.cast(data,C.POINTER(Variable));key=v[0].key
  if key not in settings:return False
  v[0].value=settings[key];return True
 if cmd==17:C.cast(data,C.POINTER(C.c_bool))[0]=False;return True
 if cmd==52:C.cast(data,C.POINTER(C.c_uint))[0]=0;return True
 if cmd==3:C.cast(data,C.POINTER(C.c_bool))[0]=False;return True
 if cmd==18:C.cast(data,C.POINTER(C.c_bool))[0]=True;return True
 if cmd==39:C.cast(data,C.POINTER(C.c_uint))[0]=3;return True
 if cmd==47:C.cast(data,C.POINTER(C.c_int))[0]=0;return True
 if cmd in [11,12,13,21,35,36,37,44,45,48,53,56,62,65536+51]:return True
 return False
@VIDEO
def video(data,w,h,pitch):
 global last
 if render_frames is not None and frame+1 not in render_frames:return
 if not data or data==C.c_void_p(-1).value:return
 raw=C.string_at(data,pitch*h)
 if fmt==1:im=Image.frombytes('RGB',(w,h),raw,'raw','BGRX',pitch)
 else:
  pixels=bytearray(w*h*3);bit5=fmt==2
  for y in range(h):
   for x in range(w):
    p=y*pitch+x*2;v=raw[p]|raw[p+1]<<8;i=(y*w+x)*3
    if bit5:pixels[i:i+3]=bytes([((v>>11)&31)*255//31,((v>>5)&63)*255//63,(v&31)*255//31])
    else:pixels[i:i+3]=bytes([((v>>10)&31)*255//31,((v>>5)&31)*255//31,(v&31)*255//31])
  im=Image.frombytes('RGB',(w,h),bytes(pixels))
 last=im
@AUDIO
def audio(l,r):pass
@BATCH
def batch(data,frames):return frames
@POLL
def poll():pass
@INPUT
def input_state(port,device,index,id):
 if port!=0:return 0
 if id==256:return sum(1<<k for k in buttons)
 return int(id in buttons)
for name,cb in [('environment',environment),('video_refresh',video),('audio_sample',audio),('audio_sample_batch',batch),('input_poll',poll),('input_state',input_state)]:
 f=getattr(core,'retro_set_'+name);f.argtypes=[type(cb)];f(cb)
core.retro_init()
core.retro_load_game.argtypes=[C.POINTER(Game)];core.retro_load_game.restype=C.c_bool
cue=Path(sys.argv[1]).resolve();path=str(cue).encode()
info=SystemInfo();core.retro_get_system_info.argtypes=[C.POINTER(SystemInfo)];core.retro_get_system_info(C.byref(info))
rom_data=None if info.need_fullpath else C.create_string_buffer(cue.read_bytes())
g=Game(path,None if rom_data is None else C.cast(rom_data,C.c_void_p),0 if rom_data is None else len(rom_data)-1,None)
assert core.retro_load_game(C.byref(g)),'load failed'
core.retro_set_controller_port_device.argtypes=[C.c_uint,C.c_uint];core.retro_set_controller_port_device(0,1)
core.retro_serialize_size.restype=C.c_size_t;core.retro_serialize.argtypes=[C.c_void_p,C.c_size_t];core.retro_serialize.restype=C.c_bool;core.retro_unserialize.argtypes=[C.c_void_p,C.c_size_t];core.retro_unserialize.restype=C.c_bool
core.retro_get_memory_data.argtypes=[C.c_uint];core.retro_get_memory_data.restype=C.c_void_p;core.retro_get_memory_size.argtypes=[C.c_uint];core.retro_get_memory_size.restype=C.c_size_t
config=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'));out=ROOT/config['output'];out.mkdir(exist_ok=True)
if config.get('capture_only'):
 render_frames=set(config.get('captures',[]))|set(config.get('dumps',[]))|{config['frames']}|{p['frame'] for p in config.get('pixel_checks',[])}
def dump(label):
 size=core.retro_serialize_size();buf=C.create_string_buffer(size);assert core.retro_serialize(buf,size);(out/f'{label}.state').write_bytes(buf.raw)
 for id,name in [(2,'ram'),(3,'vram')]:
  p=core.retro_get_memory_data(id);size=core.retro_get_memory_size(id)
  if p and size:(out/f'{label}.{name}').write_bytes(C.string_at(p,size))
 if last is not None:last.save(out/f'{label}.png')
def edits(ops):
 p=core.retro_get_memory_data(2);size=core.retro_get_memory_size(2)
 for op in ops:
  at=int(op['address'],0)&0x1fffff;data=bytes.fromhex(op['hex'])
  assert at+len(data)<=size
  if 'before' in op:assert C.string_at(p+at,len(data)).hex()==op['before'].lower()
  C.memmove(p+at,data,len(data))
if config.get('load_state'):
 state=Path(config['load_state']).read_bytes();buf=C.create_string_buffer(state);assert core.retro_unserialize(buf,len(state))
edits(config.get('initial_edits',[]))
checks={p['frame']:p for p in config.get('pixel_checks',[])};check_results=[]
font_check=None
if checks:
 from PIL import ImageDraw,ImageFont
 font_check=ImageFont.truetype(config['reference_font'],12)
def check_pixels(spec):
 # Independent screen oracle: render the requested Unicode directly with PIL,
 # without decoding the target bytes or consulting the runtime slot mapping.
 assert last is not None
 mismatches=0
 for n,ch in enumerate(spec['text']):
  ref=Image.new('1',(16,16));draw=ImageDraw.Draw(ref);draw.fontmode='1';draw.text((0,0),ch,font=font_check,fill=1)
  for y in range(16):
   for x in range(12):
    actual=last.getpixel((spec['x']+n*12+x,spec['y']+y))==tuple(spec['color'])
    mismatches+=actual!=bool(ref.getpixel((x,y)))
 outside=0
 if spec.get('reference_screen'):
  baseline=Image.open(spec['reference_screen']).convert('RGB');assert baseline.size==last.size
  x0,y0=spec['x'],spec['y'];x1=x0+len(spec['text'])*12;y1=y0+16
  for yy in range(last.height):
   for xx in range(last.width):
    if not(x0<=xx<x1 and y0<=yy<y1):outside+=baseline.getpixel((xx,yy))!=last.getpixel((xx,yy))
 result=dict(frame=frame+1,text=spec['text'],mismatches=mismatches,outside_mismatches=outside)
 check_results.append(result)
 if mismatches:last.save(out/f'failed_{frame+1:06}.png')
 assert mismatches==0 and outside==0,result
start=time.time()
for frame in range(config['frames']):
 if frame in config.get('reset_state_frames',[]):
  state=Path(config['load_state']).read_bytes();buf=C.create_string_buffer(state);assert core.retro_unserialize(buf,len(state))
 buttons=set()
 for lo,hi,keys in config.get('inputs',[]):
  if lo<=frame<hi:buttons.update(keys)
 core.retro_run()
 for action in config.get('edits',[]):
  if action['frame']==frame+1:edits(action['writes'])
 if frame+1 in checks:check_pixels(checks[frame+1])
 if frame+1 in config.get('dumps',[]):dump(f'f{frame+1:06}')
 if (frame+1) in config.get('captures',[]) and last is not None:last.save(out/f'frame_{frame+1:06}.png')
 if (frame+1)%600==0:print('frames',frame+1,'seconds',round(time.time()-start,1),flush=True)
if last is not None:last.save(out/'last.png')
size=core.retro_serialize_size();buf=C.create_string_buffer(size);assert core.retro_serialize(buf,size);(out/'state.bin').write_bytes(buf.raw)
for id,name in [(2,'ram.bin'),(0,'save_ram.bin'),(3,'vram.bin')]:
 p=core.retro_get_memory_data(id);size=core.retro_get_memory_size(id)
 if p and size:(out/name).write_bytes(C.string_at(p,size))
(out/'run.json').write_text(json.dumps({'frames':config['frames'],'seconds':time.time()-start,'pixel_checks':check_results,'options':{k.decode():v.decode() for k,v in settings.items()}},indent=2));core.retro_unload_game();core.retro_deinit();print('complete',str(out),flush=True)
