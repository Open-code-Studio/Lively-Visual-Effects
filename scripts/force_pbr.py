#!/usr/bin/env python3
"""一次生成 4 种格式的 PBR 贴图，确保 Complementary 能识别"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

SRC = Path("../assets/minecraft/textures/block/")
OUT = SRC  # 直接覆盖

# 法线 + OldPBR 光滑度
def make_normals_and_spec(img_path, strength=10.0):
    img = Image.open(img_path).convert("RGBA")
    gray = np.array(img.convert("L"), dtype=np.float32) / 255.0
    
    # 强模糊去噪
    gray_pil = Image.fromarray((gray*255).astype(np.uint8))
    low = np.array(gray_pil.filter(ImageFilter.GaussianBlur(radius=1.2)), dtype=np.float32)/255.0
    mid = np.array(gray_pil.filter(ImageFilter.GaussianBlur(radius=0.5)), dtype=np.float32)/255.0
    high = gray - mid
    high = np.clip(high, -0.1, 0.1) * 0.5
    height = low * 0.5 + mid * 0.3 + high * 0.2
    
    # Sobel 梯度（强力）
    gx = ndimage.sobel(height, axis=1) * strength
    gy = ndimage.sobel(height, axis=0) * strength
    
    # OpenGL 法线 (Y+)
    nx_gl = -gx; ny_gl = -gy; nz = np.ones_like(height)
    l = np.sqrt(nx_gl**2 + ny_gl**2 + nz**2); l = np.maximum(l, 1e-8)
    nx_gl = (nx_gl/l*0.5+0.5)*255; ny_gl = (ny_gl/l*0.5+0.5)*255; nz = (nz/l*0.5+0.5)*255
    
    # DirectX 法线 (Y-)
    ny_dx = 255 - ny_gl
    
    # OldPBR: 法线 RGB + 光滑度 Alpha
    smoothness = np.clip(40 + (height - 0.5)*30, 0, 255).astype(np.uint8)
    
    normal_gl = np.stack([nx_gl, ny_gl, nz], axis=2).astype(np.uint8)
    normal_dx = np.stack([nx_gl, ny_dx, nz], axis=2).astype(np.uint8)
    normal_oldpbr = np.dstack([normal_gl, smoothness]).astype(np.uint8)
    
    return normal_gl, normal_dx, normal_oldpbr, smoothness

# 生成镜面贴图（双通道：R + G 都是光滑度）
def make_spec(smoothness_arr):
    s = np.zeros((*smoothness_arr.shape, 4), dtype=np.uint8)
    s[:,:,0] = smoothness_arr  # R
    s[:,:,1] = smoothness_arr  # G
    s[:,:,3] = 255
    return Image.fromarray(s)

# 处理所有贴图
pngs = sorted([f for f in SRC.glob("*.png") if not f.stem.endswith(("_n","_s","_e"))])
print(f"处理 {len(pngs)} 张贴图...")

for i, p in enumerate(pngs):
    try:
        n_gl, n_dx, n_oldpbr, smooth = make_normals_and_spec(p)
        
        # 保存 OpenGL 法线
        Image.fromarray(n_gl).save(OUT / f"{p.stem}_n.png")
        
        # 保存 DirectX 法线  
        Image.fromarray(n_dx).save(OUT / f"{p.stem}_n_dx.png")
        
        # 保存 OldPBR 法线（Alpha=光滑度）
        Image.fromarray(n_oldpbr).save(OUT / f"{p.stem}_n_old.png")
        
        # 保存镜面贴图（R + G = 光滑度）
        make_spec(smooth).save(OUT / f"{p.stem}_s.png")
        
    except Exception as e:
        print(f"  ✗ {p.name}: {e}")
    
    if (i+1) % 200 == 0:
        print(f"  {i+1}/{len(pngs)}")

print(f"完成! {len(pngs)} 组")

# 打印关键统计
for name in ['stone_n','stone_s','bricks_n','bricks_s','oak_planks_n']:
    try:
        arr = np.array(Image.open(OUT / f"{name}.png"))
        r,g,b = arr[:,:,0].mean(),arr[:,:,1].mean(),arr[:,:,2].mean()
        rg = arr[:,:,0].max()-arr[:,:,0].min()
        gg = arr[:,:,1].max()-arr[:,:,1].min()
        print(f"  {name}: Rmean={r:.0f} Gmean={g:.0f} Bmean={b:.0f}  R幅={rg:.0f} G幅={gg:.0f}")
    except: pass
