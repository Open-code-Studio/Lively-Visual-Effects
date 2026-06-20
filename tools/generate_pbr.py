# ============================================================
# 灵动:视效 - PBR Texture Generator
# Lively Visual Effects | Procedural PBR Map Generation
# 
# This tool generates PBR texture maps from base color textures.
# Inspired by 零雾构想 (Fogg05 ZeroPBR) philosophy:
#   - Faithful vanilla aesthetics enhancement
#   - Consistent material properties
#   - Multi-resolution support (64x, 128x, 256x)
# ============================================================

import os
import sys
import json
import argparse
import numpy as np
from PIL import Image, ImageFilter, ImageOps

# ============================================================
# Material Property Definitions
# Following 零雾老师's classification system:
# Each block type has specific roughness/metallic values
# ============================================================

MATERIAL_PRESETS = {
    # 石质材料 - Stone materials
    "stone":             {"roughness": 0.7, "metallic": 0.0, "height_strength": 0.3, "category": "stone"},
    "cobblestone":       {"roughness": 0.8, "metallic": 0.0, "height_strength": 0.5, "category": "stone"},
    "stone_bricks":      {"roughness": 0.55, "metallic": 0.0, "height_strength": 0.25, "category": "stone"},
    "mossy_cobblestone": {"roughness": 0.85, "metallic": 0.0, "height_strength": 0.5, "category": "stone"},
    "granite":           {"roughness": 0.65, "metallic": 0.05, "height_strength": 0.2, "category": "stone"},
    "diorite":           {"roughness": 0.5, "metallic": 0.1,  "height_strength": 0.15, "category": "stone"},
    "andesite":          {"roughness": 0.6, "metallic": 0.05, "height_strength": 0.2, "category": "stone"},
    "obsidian":          {"roughness": 0.3, "metallic": 0.2,  "height_strength": 0.1, "category": "stone"},
    "bedrock":           {"roughness": 0.9, "metallic": 0.0,  "height_strength": 0.6, "category": "stone"},
    "netherrack":        {"roughness": 0.85, "metallic": 0.0,  "height_strength": 0.4, "category": "stone"},
    "end_stone":         {"roughness": 0.6, "metallic": 0.0,  "height_strength": 0.2, "category": "stone"},
    "deepslate":         {"roughness": 0.75, "metallic": 0.05, "height_strength": 0.35, "category": "stone"},
    "tuff":              {"roughness": 0.8, "metallic": 0.0,  "height_strength": 0.3, "category": "stone"},
    "calcite":           {"roughness": 0.4, "metallic": 0.15, "height_strength": 0.1, "category": "stone"},
    
    # 木质材料 - Wood materials
    "oak_planks":       {"roughness": 0.65, "metallic": 0.0, "height_strength": 0.15, "category": "wood"},
    "spruce_planks":    {"roughness": 0.7,  "metallic": 0.0, "height_strength": 0.2,  "category": "wood"},
    "birch_planks":     {"roughness": 0.6,  "metallic": 0.0, "height_strength": 0.12, "category": "wood"},
    "jungle_planks":    {"roughness": 0.65, "metallic": 0.0, "height_strength": 0.15, "category": "wood"},
    "acacia_planks":    {"roughness": 0.6,  "metallic": 0.0, "height_strength": 0.1,  "category": "wood"},
    "dark_oak_planks":  {"roughness": 0.7,  "metallic": 0.0, "height_strength": 0.2,  "category": "wood"},
    "oak_log":          {"roughness": 0.75, "metallic": 0.0, "height_strength": 0.3,  "category": "wood"},
    "oak_log_top":      {"roughness": 0.6,  "metallic": 0.0, "height_strength": 0.2,  "category": "wood"},
    
    # 泥土/沙子 - Earth materials
    "dirt":             {"roughness": 0.9,  "metallic": 0.0, "height_strength": 0.2,  "category": "earth"},
    "grass_block_top":  {"roughness": 0.85, "metallic": 0.0, "height_strength": 0.15, "category": "earth"},
    "grass_block_side": {"roughness": 0.85, "metallic": 0.0, "height_strength": 0.25, "category": "earth"},
    "sand":             {"roughness": 0.95, "metallic": 0.0, "height_strength": 0.1,  "category": "earth"},
    "gravel":           {"roughness": 0.95, "metallic": 0.0, "height_strength": 0.3,  "category": "earth"},
    "clay":             {"roughness": 0.7,  "metallic": 0.0, "height_strength": 0.05, "category": "earth"},
    "soul_sand":        {"roughness": 0.95, "metallic": 0.0, "height_strength": 0.15, "category": "earth"},
    "soul_soil":        {"roughness": 0.9,  "metallic": 0.0, "height_strength": 0.1,  "category": "earth"},
    "mud":              {"roughness": 0.85, "metallic": 0.0, "height_strength": 0.05, "category": "earth"},
    
    # 砖块 - Brick materials
    "bricks":           {"roughness": 0.55, "metallic": 0.0, "height_strength": 0.2, "category": "brick"},
    "nether_bricks":    {"roughness": 0.6,  "metallic": 0.0, "height_strength": 0.2, "category": "brick"},
    
    # 金属 - Metal materials
    "iron_block":       {"roughness": 0.2,  "metallic": 1.0, "height_strength": 0.05, "category": "metal"},
    "gold_block":       {"roughness": 0.15, "metallic": 1.0, "height_strength": 0.03, "category": "metal"},
    "diamond_block":    {"roughness": 0.1,  "metallic": 0.8, "height_strength": 0.03, "category": "metal"},
    "emerald_block":    {"roughness": 0.12, "metallic": 0.7, "height_strength": 0.03, "category": "metal"},
    "copper_block":     {"roughness": 0.25, "metallic": 1.0, "height_strength": 0.05, "category": "metal"},
    "netherite_block":  {"roughness": 0.15, "metallic": 1.0, "height_strength": 0.04, "category": "metal"},
    
    # 特殊材料 - Special
    "glass":            {"roughness": 0.05, "metallic": 0.0, "height_strength": 0.0,  "category": "glass"},
    "glowstone":        {"roughness": 0.5,  "metallic": 0.0, "height_strength": 0.2,  "category": "glow",  "emissive": True},
    "redstone_block":   {"roughness": 0.3,  "metallic": 0.6, "height_strength": 0.05, "category": "glow",  "emissive": True},
    "sea_lantern":      {"roughness": 0.2,  "metallic": 0.0, "height_strength": 0.1,  "category": "glow",  "emissive": True},
    "shroomlight":      {"roughness": 0.6,  "metallic": 0.0, "height_strength": 0.15, "category": "glow",  "emissive": True},
}


def load_texture(path):
    """Load a texture image as RGBA numpy array."""
    if not os.path.exists(path):
        return None
    img = Image.open(path).convert("RGBA")
    return np.array(img, dtype=np.float32) / 255.0


def save_texture(arr, path):
    """Save a numpy array as PNG texture."""
    arr = np.clip(arr, 0.0, 1.0)
    img = Image.fromarray((arr * 255).astype(np.uint8))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def generate_normal_map(base_color, strength=0.5):
    """
    Generate a normal map from the base color/albedo texture.
    Uses Sobel edge detection on luminance to derive surface normals.
    零雾老师风格: subtle, natural-looking normals that enhance but don't overpower.
    """
    h, w = base_color.shape[:2]
    
    # Convert to grayscale (luminance)
    lum = 0.299 * base_color[:,:,0] + 0.587 * base_color[:,:,1] + 0.114 * base_color[:,:,2]
    
    # Compute gradients using Sobel operator
    from scipy import ndimage
    if 'ndimage' not in sys.modules:
        # Fallback: simple gradient
        gy = np.zeros_like(lum)
        gx = np.zeros_like(lum)
        gy[1:-1, :] = lum[2:, :] - lum[:-2, :]
        gx[:, 1:-1] = lum[:, 2:] - lum[:, :-2]
    else:
        gx = ndimage.sobel(lum, axis=1) / 8.0
        gy = ndimage.sobel(lum, axis=0) / 8.0
    
    # Construct normal vectors
    strength = strength * 2.0
    normal = np.zeros((h, w, 3), dtype=np.float32)
    normal[:,:,0] = -gx * strength  # X (tangent)
    normal[:,:,1] = -gy * strength  # Y (bitangent)
    normal[:,:,2] = 1.0              # Z (normal)
    
    # Normalize
    length = np.sqrt(np.sum(normal ** 2, axis=2, keepdims=True))
    length = np.maximum(length, 0.001)
    normal = normal / length
    
    # Convert to [0,1] range for texture storage
    normal = normal * 0.5 + 0.5
    
    return normal


def generate_height_map(base_color, strength=0.3):
    """
    Generate height/displacement map from albedo.
    Lighter areas = higher elevation.
    Uses luminance approximation.
    """
    lum = 0.299 * base_color[:,:,0] + 0.587 * base_color[:,:,1] + 0.114 * base_color[:,:,2]
    
    # Normalize and adjust contrast
    lum_min, lum_max = lum.min(), lum.max()
    if lum_max > lum_min:
        height = (lum - lum_min) / (lum_max - lum_min)
    else:
        height = lum
    
    # Apply contrast curve for better POM results
    height = np.power(height, 0.8)
    
    # Mix in detail
    height = height * strength + (1.0 - strength) * 0.5
    
    return np.stack([height, height, height], axis=2)


def generate_mer_map(base_color, roughness=0.5, metallic=0.0, emissive=False):
    """
    Generate MER (Metallic, Emissive, Roughness) PBR map.
    R = Metallic
    G = Emissive  
    B = Roughness
    
    零雾老师风格: Consistent material classification.
    """
    h, w = base_color.shape[:2]
    
    mer = np.zeros((h, w, 3), dtype=np.float32)
    
    # R: Metallic - uniform for the material
    mer[:,:,0] = metallic
    
    # G: Emissive - bright areas of emissive blocks glow
    if emissive:
        lum = 0.299 * base_color[:,:,0] + 0.587 * base_color[:,:,1] + 0.114 * base_color[:,:,2]
        mer[:,:,1] = np.clip(lum * 0.7, 0.0, 1.0)
    else:
        mer[:,:,1] = 0.0
    
    # B: Roughness
    # Add micro-variation based on texture detail
    lum = 0.299 * base_color[:,:,0] + 0.587 * base_color[:,:,1] + 0.114 * base_color[:,:,2]
    microVar = (lum - 0.5) * 0.1  # Small variation
    mer[:,:,2] = np.clip(roughness + microVar, 0.02, 0.98)
    
    return mer


def generate_specular_map(base_color, roughness=0.5):
    """
    Generate specular/smoothness map for LabPBR format.
    Alpha channel = smoothness (1 - roughness).
    RGB = specular color (F0).
    """
    h, w = base_color.shape[:2]
    
    spec = np.zeros((h, w, 4), dtype=np.float32)
    
    # RGB: Specular color (F0) - default 0.04 for dielectrics
    spec[:,:,:3] = 0.04
    
    # Alpha: Smoothness = 1 - roughness
    spec[:,:,3] = 1.0 - roughness
    
    return spec


def generate_pbr_textures(input_path, output_dir, material_name=None, resolution=None):
    """
    Generate complete PBR texture set from a base color texture.
    
    Args:
        input_path: Path to base color texture (PNG)
        output_dir: Output directory for PBR textures
        material_name: Material preset name (e.g., "stone", "cobblestone")
        resolution: Target resolution (64, 128, 256) or None for original
    """
    # Load base texture
    base_color = load_texture(input_path)
    if base_color is None:
        print(f"  [SKIP] Input not found: {input_path}")
        return False
    
    original_h, original_w = base_color.shape[:2]
    
    # Resize if needed
    if resolution:
        img = Image.fromarray((base_color * 255).astype(np.uint8))
        img = img.resize((resolution, resolution), Image.LANCZOS)
        base_color = np.array(img, dtype=np.float32) / 255.0
    
    # Get material properties
    if material_name and material_name in MATERIAL_PRESETS:
        preset = MATERIAL_PRESETS[material_name]
        roughness = preset["roughness"]
        metallic = preset["metallic"]
        height_strength = preset["height_strength"]
        emissive = preset.get("emissive", False)
    else:
        # Auto-detect: analyze texture for material hints
        roughness, metallic, height_strength, emissive = auto_detect_material(base_color)
    
    # Get base name
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    
    # Remove _n or _mer suffixes if present in input
    for suffix in ['_n', '_mer', '_s', '_heightmap', '_normal']:
        if base_name.endswith(suffix):
            base_name = base_name[:-len(suffix)]
            break
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate maps
    print(f"  Generating PBR maps for: {base_name} (category: {material_name or 'auto'})")
    print(f"    roughness={roughness:.2f}, metallic={metallic:.2f}, height={height_strength:.2f}")
    
    # Normal map
    normal = generate_normal_map(base_color, height_strength)
    save_texture(normal, os.path.join(output_dir, f"{base_name}_n.png"))
    
    # Height map
    height = generate_height_map(base_color, height_strength)
    save_texture(height, os.path.join(output_dir, f"{base_name}_heightmap.png"))
    
    # MER map (Bedrock RTX format)
    mer = generate_mer_map(base_color, roughness, metallic, emissive)
    save_texture(mer, os.path.join(output_dir, f"{base_name}_mer.png"))
    
    # Specular map (LabPBR / Java format)
    spec = generate_specular_map(base_color, roughness)
    save_texture(spec, os.path.join(output_dir, f"{base_name}_s.png"))
    
    # Copy original albedo
    save_texture(base_color, os.path.join(output_dir, f"{base_name}.png"))
    
    print(f"  ✓ Generated: {base_name}.png, {base_name}_n.png, {base_name}_s.png, {base_name}_mer.png, {base_name}_heightmap.png")
    return True


def auto_detect_material(base_color):
    """
    Automatically detect material properties from the texture.
    Analyzes color distribution to guess material type.
    """
    lum = 0.299 * base_color[:,:,0] + 0.587 * base_color[:,:,1] + 0.114 * base_color[:,:,2]
    avg_lum = np.mean(lum)
    std_lum = np.std(lum)
    
    # Check for metal-like (high contrast, specific color ranges)
    avg_color = np.mean(base_color[:,:,:3], axis=(0,1))
    
    # High brightness + low saturation = possible metal
    saturation = np.std(base_color[:,:,:3], axis=2)
    avg_sat = np.mean(saturation)
    
    if avg_sat < 0.05 and avg_lum > 0.3:
        # Likely metal/smooth surface
        return 0.2, 0.8, 0.05, False
    
    if avg_sat > 0.3:
        # Rough/detailed texture (stone, dirt, etc.)
        if avg_lum > 0.5:
            return 0.65, 0.0, 0.2, False
        else:
            return 0.75, 0.0, 0.3, False
    
    # Default: medium roughness dielectric
    return 0.5, 0.0, 0.2, False


def generate_all_blocks(texture_dir, output_base_dir, resolutions=[64, 128, 256]):
    """Generate PBR textures for all blocks in the texture directory."""
    print("=" * 60)
    print("  灵动:视效 - PBR Texture Generator")
    print("  Lively Visual Effects | v1.0")
    print("=" * 60)
    
    if not os.path.exists(texture_dir):
        print(f"[ERROR] Texture directory not found: {texture_dir}")
        return
    
    # Find all PNG textures
    textures = [f for f in os.listdir(texture_dir) if f.endswith('.png') and not any(
        suffix in f for suffix in ['_n.', '_mer.', '_s.', '_heightmap.', '_normal.', '_specular.']
    )]
    
    if not textures:
        print(f"[ERROR] No textures found in: {texture_dir}")
        return
    
    print(f"\nFound {len(textures)} base textures")
    print(f"Material presets available: {len(MATERIAL_PRESETS)}")
    print()
    
    success_count = 0
    skip_count = 0
    
    for tex_file in sorted(textures):
        base_name = os.path.splitext(tex_file)[0]
        input_path = os.path.join(texture_dir, tex_file)
        
        # Try to find matching material preset
        material_name = None
        for preset_name in MATERIAL_PRESETS:
            if preset_name in base_name.lower():
                material_name = preset_name
                break
        
        if material_name is None:
            # Try fuzzy match
            base_simplified = base_name.lower().replace('_', '')
            for preset_name in MATERIAL_PRESETS:
                if preset_name.replace('_', '') in base_simplified:
                    material_name = preset_name
                    break
        
        # Generate for each resolution
        for res in resolutions:
            output_dir = os.path.join(output_base_dir, str(res), "textures", "blocks")
            result = generate_pbr_textures(input_path, output_dir, material_name, res)
            if result:
                success_count += 1
            else:
                skip_count += 1
    
    print(f"\n{'=' * 60}")
    print(f"  Complete! Generated: {success_count} | Skipped: {skip_count}")
    print(f"{'=' * 60}")


def create_sample_texture(name, size=64, color=None):
    """Create a procedural sample texture for development/testing."""
    h, w = size, size
    arr = np.zeros((h, w, 4), dtype=np.float32)
    
    # Generate noise-based pattern
    np.random.seed(hash(name) % 2**32)
    noise = np.random.rand(h, w) * 0.3
    
    if color is None:
        # Default gray-brown
        base = np.array([0.5, 0.45, 0.4])
    else:
        base = np.array(color)
    
    # Add pattern based on name
    for y in range(h):
        for x in range(w):
            pattern = 0.0
            if "brick" in name:
                # Brick pattern
                bx, by = x % 16, y % 16
                if by < 1 or by > 14:
                    pattern = 0.1
                elif (x // 16) % 2 == 0 and (bx < 1 or bx > 14):
                    pattern = 0.05
            elif "plank" in name or "log" in name:
                # Wood grain
                pattern = np.sin(y * 0.5 + np.sin(x * 0.3) * 2.0) * 0.1
            elif "stone" in name or "cobble" in name:
                # Stone noise
                pattern = noise[y, x] * 0.2
            elif "dirt" in name:
                pattern = noise[y, x] * 0.25
            elif "sand" in name:
                pattern = noise[y, x] * 0.15
            elif "grass" in name:
                pattern = np.sin(x * 0.3) * np.sin(y * 0.3) * 0.1
            
            arr[y, x, :3] = np.clip(base + pattern, 0.0, 1.0)
            arr[y, x, 3] = 1.0
    
    return arr


def generate_pack_icon(size=256):
    """Generate the pack icon for 灵动:视效."""
    arr = np.zeros((size, size, 4), dtype=np.float32)
    
    # Gradient background (deep blue to purple)
    for y in range(size):
        t = y / size
        top_color = np.array([0.1, 0.2, 0.5])  # Deep blue
        bottom_color = np.array([0.3, 0.1, 0.5])  # Purple
        color = top_color * (1 - t) + bottom_color * t
        arr[y, :, :3] = color
        arr[y, :, 3] = 1.0
    
    # Center glow
    cx, cy = size // 2, size // 2
    for y in range(size):
        for x in range(size):
            dx, dy = (x - cx) / (size * 0.3), (y - cy) / (size * 0.3)
            dist = np.sqrt(dx**2 + dy**2)
            glow = np.exp(-dist**2) * 0.4
            arr[y, x, :3] += np.array([0.3, 0.5, 1.0]) * glow
    
    # Diamond/Crystal shape
    for y in range(size):
        for x in range(size):
            dx, dy = abs(x - cx) / (size * 0.25), abs(y - cy) / (size * 0.35)
            if dx + dy < 1.0:
                alpha = 1.0 - (dx + dy)
                arr[y, x, :3] = arr[y, x, :3] * (1 - alpha * 0.5) + np.array([0.8, 0.9, 1.0]) * alpha * 0.5
                arr[y, x, 3] = 1.0
    
    return arr


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="灵动:视效 PBR Texture Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate PBR textures from vanilla textures
  python generate_pbr.py --input textures/blocks --output output/
  
  # Generate a single texture
  python generate_pbr.py --single textures/blocks/stone.png --material stone
  
  # Generate sample textures for development
  python generate_pbr.py --samples
  
  # Generate pack icon
  python generate_pbr.py --icon
        """
    )
    parser.add_argument("--input", help="Directory containing base color textures")
    parser.add_argument("--output", default="../texture_pack", help="Output base directory")
    parser.add_argument("--single", help="Process a single texture file")
    parser.add_argument("--material", help="Material preset name for single texture")
    parser.add_argument("--resolutions", nargs="+", type=int, default=[64, 128, 256],
                       help="Output resolutions (default: 64 128 256)")
    parser.add_argument("--samples", action="store_true", help="Generate sample textures for testing")
    parser.add_argument("--icon", action="store_true", help="Generate pack icon only")
    
    args = parser.parse_args()
    
    if args.icon:
        print("Generating pack icon...")
        icon = generate_pack_icon(256)
        output_path = os.path.join(args.output, "pack_icon.png")
        save_texture(icon, output_path)
        print(f"  ✓ Pack icon saved: {output_path}")
    elif args.samples:
        print("Generating sample PBR textures for development...")
        samples_dir = os.path.join(args.output, "samples")
        
        # Generate sample textures for key materials
        sample_blocks = {
            "stone": [0.5, 0.48, 0.45],
            "cobblestone": [0.45, 0.43, 0.4],
            "dirt": [0.55, 0.4, 0.25],
            "oak_planks": [0.65, 0.5, 0.3],
            "bricks": [0.6, 0.3, 0.2],
            "sand": [0.85, 0.8, 0.6],
            "gravel": [0.4, 0.38, 0.35],
            "obsidian": [0.1, 0.08, 0.15],
            "iron_block": [0.85, 0.85, 0.85],
            "gold_block": [0.95, 0.85, 0.2],
        }
        
        for name, color in sample_blocks.items():
            sample = create_sample_texture(name, 64, color)
            sample_path = os.path.join(samples_dir, f"{name}.png")
            save_texture(sample, sample_path)
            print(f"  Created sample: {name}.png")
        
        # Generate PBR maps for samples
        for res in args.resolutions:
            output_dir = os.path.join(args.output, "subpacks", f"{res}x", "textures", "blocks")
            for name, color in sample_blocks.items():
                sample = create_sample_texture(name, res, color)
                generate_pbr_textures(
                    os.path.join(samples_dir, f"{name}.png"),
                    output_dir,
                    name, res
                )
    elif args.single:
        output_dir = os.path.join(args.output, "textures", "blocks")
        generate_pbr_textures(args.single, output_dir, args.material)
    elif args.input:
        generate_all_blocks(args.input, args.output, args.resolutions)
    else:
        parser.print_help()
        print("\nTip: Use --samples to generate sample textures and see how it works!")
