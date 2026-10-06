import numpy as np, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
W,H=1280,670
rng=np.random.default_rng(7); random.seed(7)

# --- washi paper
base=np.zeros((H,W,3),float); base[:]=(238,229,209)
n=rng.normal(0,1,(H//8+1,W//8+1)); n=np.array(Image.fromarray(((n-n.min())/(n.max()-n.min())*255).astype('uint8')).resize((W,H),Image.BICUBIC),float)/255
base+= (n[...,None]-0.5)*26
fine=rng.normal(0,3.2,(H,W,1)); base+=fine
yy,xx=np.mgrid[0:H,0:W]; d=np.sqrt(((xx-W/2)/(W/2))**2+((yy-H/2)/(H/2))**2)
base-= (np.clip(d-0.55,0,1)**1.6)[...,None]*np.array([40,48,62])
paper=Image.fromarray(np.clip(base,0,255).astype('uint8')).convert('RGB')

def ink_layer(draw_fn, blur=0, opacity=1.0, color=(34,32,32)):
    m=Image.new('L',(W,H),0); draw_fn(ImageDraw.Draw(m))
    if blur: m=m.filter(ImageFilter.GaussianBlur(blur))
    m=m.point(lambda v:int(v*opacity))
    return m, color
img=paper.copy()
def paint(mask,color):
    global img
    img=Image.composite(Image.new('RGB',(W,H),color),img,mask)

# --- far mountains (pale)
def far(d):
    pts=[(0,470),(80,430),(160,455),(250,400),(340,445),(430,420),(520,470),(520,670),(0,670)]
    d.polygon(pts,fill=255)
paint(*ink_layer(far,blur=7,opacity=0.16,color=(70,70,74)))
def far2(d):
    pts=[(1280,430),(1200,380),(1130,420),(1060,370),(980,430),(900,470),(1280,500)]
    d.polygon(pts,fill=255)
paint(*ink_layer(far2,blur=6,opacity=0.18,color=(70,70,74)))

# --- Fuji
cx=930
def fuji(d):
    pts=[(cx-70,238)]
    for t in np.linspace(0,1,40):
        x=cx-70-(t**1.35)*430; y=238+t*330; pts.append((x,y))
    pts+= [(cx+420,568)]
    for t in np.linspace(1,0,40):
        x=cx+70+(t**1.35)*430; y=238+t*330; pts.append((x,y))
    d.polygon(pts,fill=255)
paint(*ink_layer(fuji,blur=2.2,opacity=0.55,color=(52,54,60)))
# shading right side darker
def fuji_shade(d):
    pts=[(cx+10,238),(cx+70,238)]
    for t in np.linspace(0,1,30):
        pts.append((cx+70+(t**1.35)*430,238+t*330))
    pts+= [(cx+120,568)]
    d.polygon(pts,fill=255)
paint(*ink_layer(fuji_shade,blur=14,opacity=0.35,color=(30,30,34)))
# snowcap (paper colour streaks)
def snow(d):
    pts=[(cx-72,240),(cx+72,240),(cx+135,300),(cx+95,285),(cx+70,320),(cx+40,290),(cx+5,335),(cx-30,292),(cx-65,330),(cx-95,285),(cx-135,300)]
    d.polygon(pts,fill=255)
paint(*ink_layer(snow,blur=2.5,opacity=0.9,color=(240,232,214)))
# mist
def mist(d):
    for (x,y,w,h) in [(930,430,640,70),(760,470,520,50),(1100,400,420,50),(300,520,700,60)]:
        d.ellipse((x-w/2,y-h/2,x+w/2,y+h/2),fill=255)
paint(*ink_layer(mist,blur=26,opacity=0.78,color=(240,232,214)))

# --- near foreground hill left & pines
def hill(d):
    pts=[(0,600),(120,575),(260,590),(420,610),(640,625),(640,670),(0,670)]
    d.polygon(pts,fill=255)
paint(*ink_layer(hill,blur=3,opacity=0.6,color=(36,36,38)))
def pine(x,y,s):
    def f(d):
        d.line((x,y,x+4*s,y-60*s),fill=255,width=int(5*s))
        for i in range(5):
            yy_=y-14*s-i*11*s; w=(34-i*5)*s
            d.ellipse((x+2*s-w,yy_-6*s,x+2*s+w,yy_+6*s),fill=255)
    return f
paint(*ink_layer(pine(1175,640,1.4),blur=1.2,opacity=0.75))
paint(*ink_layer(pine(1105,650,1.0),blur=1.2,opacity=0.7))

# --- candlestick chart in ink (rising)
red=(176,40,34); black=(30,28,28)
cl=Image.new('RGBA',(W,H),(0,0,0,0)); cd=ImageDraw.Draw(cl)
vals=[(560,545,520,585),(535,520,505,560),(555,525,495,575),(515,498,480,540),(530,505,470,545),
      (490,470,452,512),(505,478,430,520),(455,440,418,478),(470,452,395,495),(430,405,380,450),(420,400,372,438),(385,360,335,402)]
# each: open, close, high(top), low(bottom) in y; y smaller = higher
x0=70; dx=48
trend=[]
for i,(o,c,hi,lo) in enumerate(vals):
    x=x0+i*dx+random.uniform(-2,2)
    up= c<o
    col=red if up else black
    top=min(o,c); bot=max(o,c)
    cd.line((x,hi,x,lo),fill=col+(235,),width=3)
    cd.rounded_rectangle((x-13,top,x+13,bot),radius=2,fill=col+(225 if up else 230,))
    trend.append((x,(o+c)/2))
# brushy trend line
pts=[(x,y-6) for x,y in trend]
for k in range(len(pts)-1):
    cd.line((pts[k],pts[k+1]),fill=(176,40,34,150),width=5)
cl=cl.filter(ImageFilter.GaussianBlur(0.8))
img=img.convert('RGBA'); 
# ink bleed shadow
sh=cl.copy().filter(ImageFilter.GaussianBlur(4)); a=sh.split()[3].point(lambda v:int(v*0.35)); sh.putalpha(a)
img=Image.alpha_composite(img,sh); img=Image.alpha_composite(img,cl).convert('RGB')

# --- text
def font(path,size,var=None):
    f=ImageFont.truetype(path,size)
    if var:
        try: f.set_variation_by_axes([var])
        except Exception as e: pass
    return f
serif="C:/Windows/Fonts/NotoSerifJP-VF.ttf"
ft=font(serif,84,900); fs=font("C:/Windows/Fonts/YuGothB.ttc",27)
td=ImageDraw.Draw(img)
def shadowtext(xy,txt,f,fill,sw=0):
    x,y=xy
    # soft paper halo for legibility
    halo=Image.new('L',(W,H),0); ImageDraw.Draw(halo).text((x,y),txt,font=f,fill=255,stroke_width=sw+6)
    halo=halo.filter(ImageFilter.GaussianBlur(10)).point(lambda v:int(v*0.55))
    global img,td
    img=Image.composite(Image.new('RGB',(W,H),(240,232,214)),img,halo)
    td=ImageDraw.Draw(img)
    td.text((x,y),txt,font=f,fill=fill,stroke_width=sw,stroke_fill=fill)
shadowtext((64,46),"Claude Codeで",ft,(28,26,26),sw=1)
shadowtext((64,142),"日本株の株価を聞く",ft,(28,26,26),sw=1)
shadowtext((68,252),"tradingview-mcp-server を試してみた",fs,(70,64,60))
# hanko seal
seal=Image.new('RGBA',(104,104),(0,0,0,0)); sd=ImageDraw.Draw(seal)
sd.rounded_rectangle((2,2,101,101),radius=7,fill=(182,38,32,235))
sf=font(serif,70,900)
sd.text((52,52),"株",font=sf,fill=(244,230,214,255),anchor='mm')
seal=seal.rotate(6,expand=True,resample=Image.BICUBIC)
# rough edge
na=np.array(seal)[...,3].astype(float); na*= (0.85+0.15*rng.random(na.shape)); seal.putalpha(Image.fromarray(na.astype('uint8')))
img=img.convert('RGBA'); img.alpha_composite(seal,(1128,540)); img=img.convert('RGB')
img.save("見出し画像.jpg",quality=92)
print(img.size)
