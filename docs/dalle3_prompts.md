# EchoPet DALL-E 3 (gpt-image) 提示词指南 (方案A)

本指南包含用于生成 EchoPet 方案A（**赛博棉花糖小精灵 / Cyber-Warmth Soft Mascot**）的 UI 设计图和角色资产。

> **角色设计核心**：方案A的桌宠是一个**圆润软糯的棉花糖小精灵**——类似于 Discord Wumpus / 宝可梦风格的可爱团子。软软的圆形身体、超大号闪亮眼睛、戴着耳机。整体感觉是科技感、软萌治愈的，而**不是恐怖的**。

---

## 1. UI 界面设计图生成提示词 (UI Mockups)

**【生图尺寸建议】**
- 生成 UI 面板建议选择 **`1024x1536` (竖屏)** 或 **`1024x1024` (默认方形)**。

### 1.1 主输入与音乐推荐面板 (Input & Music Response Panel)

> **目标**：生成一个深色模式、具有丰富层次感和数据可视化元素的专业级 UI 面板，消除廉价的"AI生成毛玻璃"感，打造类似 Figma 上的高级 Dashboard 质感。

**Prompt:**
```text
A highly detailed, professional UI/UX design mockup for an advanced emotional music AI desktop application named "EchoPet". The interface is a sophisticated dark mode dashboard floating on a desktop, designed with complex visual hierarchy and data visualization elements.

The UI is enclosed in a sleek, dark titanium-grey frame with subtle glowing neon-blue edge highlights.
Top section (Voice Input & Analysis): A wide, complex input module. On the left, a detailed real-time audio waveform visualizer. In the center, a glowing circular voice-activation button with intricate concentric rings and micro-text reading "VOICE RECEPTOR ACTIVE". Above it, floating micro-data tags showing "Emotion: Frustrated [87%]" and "BPM Target: 85".
Bottom section (Dynamic Music Hub): A multi-layered music player card. On the left, high-resolution album art with a holographic overlay effect. In the middle, complex track information with glowing progress bars, EQ sliders, and technical typography (e.g., "TRACK: MIDNIGHT RAIN // GENRE: LOFI-SYNTH"). On the right, a vertical stack of sleek, glowing feedback buttons with crisp iconography (Like, Skip, Boost Intensity).

Overall style: Cyberpunk meets professional fintech dashboard, highly complex, rich in micro-details (grid lines, data points, subtle glowing gradients), Dribbble/Behance top-tier UI design, photorealistic rendering.
```

### 1.2 桌面右键菜单栏 (Desktop Context Menu)

> **目标**：生成一个带有高科技感、微型数据图表和复杂操作选项的精致右键菜单。

**Prompt:**
```text
A highly detailed, professional UI/UX design mockup of a complex desktop context menu for an advanced music AI. The menu floats on a dark background and features a dark titanium-grey metallic texture with sharp, precise edges and glowing neon-blue accents.

Top area (Live Status HUD): A mini-dashboard integrated into the top of the menu. On the left, a small, highly detailed holographic avatar of a fluffy cyber-mascot inside a circular glowing border. Next to it, a tiny real-time line chart showing "Vibe Fluctuation". Below the chart, crisp technical text reading "SYS.STATUS: FINDING TRACK..." and "NOW_PLAYING: MIDNIGHT RAIN".
Bottom area (Command Matrix): A list of complex, sleek menu items with detailed micro-icons. The items look like command console inputs: "> INITIATE ECHOPET", "> RUN DIAGNOSTICS", and "> TERMINATE PROCESS". Each item has a subtle glowing hover effect state shown.

Overall style: Advanced cyberpunk UI, complex data visualization, professional software interface, crisp typography, rich micro-details, Dribbble/Behance top-tier UI design.
```

---

## 2. 角色美术资产生成提示词 (Character Sprite Sheets)

**【极度重要：DyberPet 序列帧规范与后期处理】**
1. **生成**：使用宽屏尺寸 `1536x1024` 生成白底的横向序列图。
2. **去底**：使用抠图工具（如 PS 的魔棒、在线抠图工具）一键去除纯白背景，保留透明通道。
3. **切分**：将宽图横向等分为 4 份或 6 份独立的 PNG（例如在线使用 Sprite Sheet Cutter）。
4. **缩放**：根据 `pet_conf.json` 中的 `width` 和 `height` 限制（通常在 100x100 到 200x200 之间），缩小图片。
5. **命名**：放入 `action/` 文件夹，并严格命名为 `动作名_0.png`, `动作名_1.png` 等（如 `stand_0.png`, `stand_1.png`）。

### 2.1 角色基础待机 (Idle / Default State)

> **目标**：生成一个软糯棉花糖小精灵的待机呼吸序列帧。切图后作为 `pet_conf.json` 中的 `default` (如 `stand_0.png` ~ `stand_3.png`)。

**Prompt:**
```text
A 2D sprite sheet of an adorable, perfectly round, fluffy cotton-ball-like mascot — just like a cute Discord Wumpus or a soft Pokemon plushie. The character has an irresistibly soft round body, enormous sparkly round eyes, tiny stubby limbs, and it is wearing a pair of oversized cute headphones.

Content: A horizontal sequence of 4 to 6 frames showing a gentle "idle breathing and floating" animation. The fluffy round body gently bobs up and down. Its enormous eyes are half-closed in a peaceful, content smile. Tiny musical notes or sparkles gently float and sway above its head across the frames.
Color palette: Clean white, soft glowing blue, and gentle light purple accents.
Style: Cute mascot, soft plush-like feel, smooth round shapes, modern tech mascot aesthetic, safe and non-scary. Arranged in a neat horizontal row on a SOLID WHITE background.
```

### 2.2 状态变体：专注 (Focus State)

> **目标**：生成角色专注心流状态的序列帧。切图后对应 `focus_0.png` ~ `focus_3.png`。

**Prompt:**
```text
A 2D sprite sheet of an adorable, perfectly round, fluffy cotton-ball-like mascot — just like a cute Discord Wumpus or a soft Pokemon plushie. The character has an irresistibly soft round body, enormous sparkly round eyes, tiny stubby limbs, and it is wearing a pair of oversized cute headphones.

Content: A horizontal sequence of 4 to 6 frames showing a "focused and excited" animation. Its enormous eyes are wide open with excitement and focus. Its tiny ears perk straight up. A small glowing purple soundwave icon pulses above its head. Its whole round body bounces slightly with energy across the frames.
Color palette: Clean white with soft glowing lavender purple and gentle energetic yellow accents.
Style: Cute mascot, soft plush-like feel, smooth round shapes, modern tech mascot aesthetic, safe and non-scary. Arranged in a neat horizontal row on a SOLID WHITE background.
```

### 2.3 状态变体：疲惫 (Tired State)

> **目标**：生成角色疲惫状态的序列帧。切图后对应 `tired_0.png` ~ `tired_3.png`。

**Prompt:**
```text
A 2D sprite sheet of an adorable, perfectly round, fluffy cotton-ball-like mascot — just like a cute Discord Wumpus or a soft Pokemon plushie. The character has an irresistibly soft round body, enormous round eyes, tiny stubby limbs, and it is wearing oversized cute headphones that have slipped down around its neck.

Content: A horizontal sequence of 4 to 6 frames showing a "tired and sleepy" animation. Its enormous round eyes are half-closed and droopy, slowly blinking. Its tiny ears droop down. Small "Zzz" bubbles slowly float up above its head. Its whole fluffy body slowly sways, getting heavier with sleepiness.
Color palette: Clean white with dim, soft lavender-grey and sleepy muted blue accents.
Style: Cute mascot, soft plush-like feel, smooth round shapes, modern tech mascot aesthetic, safe and non-scary. Arranged in a neat horizontal row on a SOLID WHITE background.
```

### 2.4 状态变体：烦躁 (Frustrated State)

> **目标**：生成角色烦躁/Debug崩溃状态的序列帧。切图后对应 `frustrated_0.png` ~ `frustrated_3.png`。

**Prompt:**
```text
A 2D sprite sheet of an adorable, perfectly round, fluffy cotton-ball-like mascot — just like a cute Discord Wumpus or a soft Pokemon plushie. The character has an irresistibly soft round body, enormous round eyes, tiny stubby limbs, and it is wearing a pair of oversized cute headphones.

Content: A horizontal sequence of 4 to 6 frames showing a "frustrated but still adorable" animation. Its enormous eyes are squeezed shut tight in a squiggly frustrated expression. Its tiny mouth makes a small pouting shape. Its round body puffs up slightly and shakes. Small surprise mark symbols (!) or tiny steam puffs pop above its head. Note: Only use the face and body — do NOT add arms or hands.
Color palette: Clean white with warm flushed pink cheeks and soft passionate coral accents.
Style: Cute mascot, soft plush-like feel, smooth round shapes, modern tech mascot aesthetic, safe and non-scary. Arranged in a neat horizontal row on a SOLID WHITE background.
```

### 2.5 状态变体：低落 (Sad State)

> **目标**：生成角色情绪低落状态的序列帧。切图后对应 `sad_0.png` ~ `sad_3.png`。

**Prompt:**
```text
A 2D sprite sheet of an adorable, perfectly round, fluffy cotton-ball-like mascot — just like a cute Discord Wumpus or a soft Pokemon plushie. The character has an irresistibly soft round body, enormous round eyes, tiny stubby limbs, and it is wearing a pair of oversized cute headphones.

Content: A horizontal sequence of 4 to 6 frames showing a "sad and crying" animation. Its enormous round eyes are full of large glimmering teardrops. Its tiny ears droop down. It is curled slightly into itself. A few tiny blue teardrops slowly fall from its eyes. Note: Only use the face and body — do NOT add arms or hands.
Color palette: Dimmed cool blue-grey tones, cold soft cyan, and melancholy muted blue accents.
Style: Cute mascot, soft plush-like feel, smooth round shapes, modern tech mascot aesthetic, safe and non-scary. Arranged in a neat horizontal row on a SOLID WHITE background.
```