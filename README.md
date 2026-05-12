# Wan2.7 Transparent Background Use Cases

这个仓库整理了 `wan2.7-image-pro` 在透明背景场景下的实测案例，包括：

- 文本生成透明 PNG：20 个 use case
- 参考图编辑并保持或重建透明背景：8 个 use case
- 每条案例的图片、参考图、成功/失败、透明像素比例、提示词
- 一套可复用的透明背景生成与编辑提示词模板

静态网页入口在 [`docs/index.html`](docs/index.html)。如果启用 GitHub Pages，可以直接把发布目录设置为 `main / docs`。

## 实测结论

| 类型 | 成功 | 总数 | 成功率 |
|---|---:|---:|---:|
| 透明背景生成 | 18 | 20 | 90% |
| 透明背景编辑 | 6 | 8 | 75% |
| 总计 | 24 | 28 | 85.7% |

## 透明背景生成提示词模板

```text
Create a production-ready isolated asset as a real PNG with transparent background.
The background must be fully transparent using the PNG alpha channel.
Do not draw a checkerboard pattern, white canvas, gray canvas, colored backdrop, shadow box, scene, floor, wall, table, border, frame, or poster rectangle.
Subject only, centered, clean cutout edges, natural antialiasing on edge pixels.
Asset brief: [你的主体描述]
```

## 透明背景编辑提示词模板

```text
Edit Image 1: [具体编辑目标].
Return a real PNG with transparent background using the PNG alpha channel.
If the input already has transparency, preserve the exact existing alpha mask outside the edited subject.
If the input has an opaque background, remove it completely.
Output only the edited subject, centered, clean antialiased cutout edges.
No checkerboard, no white canvas, no gray canvas, no colored backdrop, no wall, no floor, no table, no scene, no frame, no poster rectangle, no decorative background.
```

## 提示词工程技巧

1. 把透明背景写成输出格式，而不是风格描述：一定要出现 `real PNG` 和 `PNG alpha channel`。
2. 不要只写 `transparent background`，这很容易被模型理解成“看起来像透明”的棋盘格或白底。
3. 生成商品、人物、服饰、食物时，加入 `isolated asset`、`subject only`、`catalog cutout`。
4. 编辑已有透明图时，加入 `preserve the exact existing alpha mask outside the edited subject`。
5. 编辑不透明参考图时，加入 `remove the original background completely`。
6. 多图拼接不要写 `poster background`，改成 `transparent poster asset cluster` 或 `floating decorative elements`。
7. 明确禁止背景补全：`checkerboard`、`white canvas`、`gray canvas`、`colored backdrop`、`wall`、`floor`、`table`、`scene`、`frame`、`poster rectangle`。
8. 换色或变形时锁住主体结构：`keep the same silhouette, geometry, lighting, texture, and object layout`。
9. 海报素材类要额外禁止 `rays`、`texture background`、`decorative background`，否则模型容易生成完整海报底图。
10. 验收必须做像素级 alpha 检查：PNG/RGBA 且存在真实透明像素，不能只看肉眼预览。

## 失败经验与优化方向

在“把提示词工程要点直接塞进 prompt”的批量测试中，50 张文本生图透明背景成功率为 `42/50 = 84%`，50 张参考图编辑透明背景成功率为 `34/50 = 68%`。失败样本的主要问题不是没有 alpha 通道，而是 **文件是 RGBA，但透明像素为 0%**。这意味着模型理解了 PNG/RGBA 格式，却仍然给整张画布填了不透明底。

### 容易失败的类型

- Logo / 徽章类：模型容易生成圆形底、方形底、app icon 容器、贴纸底或白色画布。
- 海报标题 / 字体素材：只要出现 `title asset`、`readable text`、`chrome ribbon`、`equalizer bars`，模型容易补成完整标题牌或海报块。
- 商品组合：`bundle`、`box`、`polishing cloth`、`floating arrangement` 会诱导模型生成展示台面或陈列背景。
- 反光硬表面商品：轮毂、头盔、金属商品容易生成摄影棚反射、地面反光或环境光板。
- 真人动作道具：人物加器械或动态姿势时，模型容易补健身房、地面、阴影和背景灯。

### 强化版透明背景生成模板

```text
Create a production-ready isolated cutout asset as a real PNG with transparent background.
The canvas outside the visible subject must be 100% transparent alpha, not white, gray, black, colored, or checkerboard.
At least 40% of the image area should be fully transparent alpha.
Only the subject pixels should be opaque or translucent.
Do not create any backing shape, badge base, sticker sheet, label plate, poster rectangle, paper, card, platform, tabletop, floor, wall, studio backdrop, cast shadow, reflection surface, frame, border, glow panel, or texture background.
Keep shadows and glow only inside the subject silhouette or immediately attached to the object, never on a background.
Subject only, centered, complete, clean antialiased cutout edges.
Asset brief: [你的主体描述]
```

### 按场景追加的约束

Logo 类：

```text
Logo mark only. No badge background, no circle base, no square tile, no app icon container, no paper, no mockup, no sticker backing. Transparent pixels must surround every outside edge of the logo.
```

海报素材 / 标题字：

```text
Create floating typography and decorative elements only, not a poster. No rectangular poster, no title card, no background rays, no panel, no banner block. Each decorative element floats on transparent alpha.
```

商品组合：

```text
Floating product bundle only. No display surface, no box base unless the box is an actual product item, no tabletop, no studio floor, no contact shadow. Leave transparent empty space between and around objects.
```

反光商品：

```text
Reflections must appear only on the object material itself. Do not create reflected floors, horizon lines, studio panels, or environment reflections outside the product silhouette.
```

真人人物：

```text
Full-body/person cutout only. No gym, no room, no floor contact shadow, no background lighting panel. The empty area around limbs and props must be transparent alpha.
```

## 图片编辑失败经验与优化方向

50 张参考图编辑测试中，透明背景成功率为 `34/50 = 68%`。失败样本同样大多是 RGBA 文件，但透明像素为 `0%` 或接近 `0%`。编辑任务比纯生成更难，因为模型容易把“原图画布”或“输入图的背景状态”当作需要保留的组成部分。

### 编辑失败的主要模式

- 透明图标改风格：火箭、灯泡、星星、T 恤图标在 3D 化、金属化、贴纸化时，模型会生成一块浅色贴纸底、纹理底或隐形全画布。
- Logo / badge 质感化：`enamel badge`、`metallic gold`、`raised bevel` 很容易触发徽章底板或完整图标容器。
- 透明商品二次编辑：对已经透明的模特、化妆品、鞋等做换装/换包装时，模型有时会重绘整张图并丢掉原 alpha。
- 多图合成：把 logo 印到衣服、把符号放到表盘、给餐饮图加 badge 时，模型容易输出一个合成后的方形画布。
- 促销标签 / 文字：`label`、`badge`、`IDEA`、`FRESH` 等词会诱导模型生成贴纸底或文本牌。

### 强化版透明背景编辑模板

```text
Edit Image 1: [具体编辑目标].
Return a real PNG with transparent background using the PNG alpha channel.
Do not flatten the image onto any canvas.
Do not rasterize the transparent background into white, gray, black, checkerboard, paper, texture, or a low-opacity full-frame layer.
If the input already has transparency, preserve the exact existing alpha mask everywhere outside the edited pixels.
Only modify the requested subject pixels; untouched transparent pixels must remain fully transparent alpha = 0.
If the input has an opaque background, remove the original background completely and leave at least 40% of the canvas fully transparent alpha.
Output only the edited subject or edited asset cluster.
No background plate, no badge base, no sticker backing, no app icon tile, no poster card, no square canvas, no display surface, no wall, no floor, no tabletop, no contact shadow.
```

### 透明输入的专用追加句

```text
The source image already contains transparency. Treat transparent pixels as locked and immutable. Do not repaint, fill, soften, haze, texture, or replace transparent areas. Preserve alpha = 0 outside the original subject mask.
```

### 不透明输入抠图的专用追加句

```text
Remove the original photo background first, then perform the edit. The final image must contain only the edited subject, with fully transparent empty space around all outside edges and interior gaps.
```

### 多图合成的专用追加句

```text
Use the extra images only as object or style references. Compose the objects as floating cutout elements on transparent alpha, not inside a poster, card, label plate, app icon tile, product mockup, or scene.
```

### Logo / 图标编辑的专用追加句

```text
Keep the logo/icon silhouette only. No badge base, no circular disk, no square tile, no app icon container, no sticker backing, no bevel plate, no paper texture. Transparent pixels must surround every outside edge of the logo/icon.
```

### 文字 / 标签编辑的专用追加句

```text
The text is part of the floating cutout asset only. Do not place the text on a rectangle, ribbon panel, poster card, label plate, or sticker backing unless explicitly requested.
```

## 文件结构

```text
docs/
  index.html
  styles.css
  app.js
  data.js
  assets/
```

`build_site.py` 会从本地测试结果 JSON 重新生成 `docs/` 数据和资源。
