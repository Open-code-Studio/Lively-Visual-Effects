# 项目: 灵动:视效 (Lively Visual Effects)

## 项目类型
Minecraft Java 版 PBR 材质包（资源包），面向 Iris Shaders 优化。

## PBR 格式标准
- **labPBR 1.3**
- 法线贴图: OpenGL 格式（切线空间，Y+ 向上）
- _s.png 通道: R=光滑度(Smoothness), G=金属度(Metalness), B=自发光(Emission)

## 技术栈
- Python 脚本工具: Pillow + numpy + scipy

## 关键文件
- `pack.mcmeta` — 资源包元数据
- `scripts/create_all_textures.py` — 全方块 3D 纹理生成器 (216种)
- `scripts/generate_pbr.py` — PBR 贴图批量生成
- 最终方案: 从原版 jar 提取 1111 个纹理，仅生成 _n + _s PBR 层，纹理外观保持原版
- 已生成 1111×3=3333 个 PBR 贴图文件
- `docs/PBR_GUIDE.md` — 格式规范文档
- `assets/minecraft/textures/block/` — 贴图存放
