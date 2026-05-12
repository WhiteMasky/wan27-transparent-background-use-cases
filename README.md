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
