# 项目记忆 - 灵动:视效 (Lively Visual Effects)

## 项目概述
Minecraft PBR材质包 + 专属光影系统，学习零雾老师的设计理念。

## 项目结构
- `texture_pack/` - PBR材质包（双版本兼容）
- `shader_pack/` - 专属光影（GLSL着色器）
- `tools/generate_pbr.py` - PBR贴图自动生成器

## 关键设计决策
- **设计哲学**: 零雾老师风格——忠实原版画风，增强PBR质感而非魔改
- **PBR标准**: LabPBR 1.3 (Java) + Bedrock RTX MER格式
- **渲染管线**: Cook-Torrance BRDF + GGX NDF + Deferred Shading
- **材质分类**: 30+种预设，分石质/木质/泥土/砖块/金属/玻璃/发光
- **多分辨率**: 64x/128x/256x 三档
- **兼容性**: Java(Iris/Optifine/Oculus) + Bedrock RTX

## 开发约定
- GLSL版本: 150 compatibility
- 着色器通道命名: gbuffers_*, composite*, shadow.*, final.*
- PBR贴图命名: name.png / name_n.png / name_s.png / name_mer.png / name_heightmap.png
- Python纹理生成使用 numpy + Pillow + scipy
