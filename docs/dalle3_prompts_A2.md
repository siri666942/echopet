# EchoPet DALL-E 3 (gpt-image) 提示词指南 (方案A-备选角色：音乐光球小星星)

本指南包含用于生成 EchoPet **方案A备选角色**（**音乐光球小星星 / Music Light Orb Star Sprite**）的 DALL-E 3 提示词。

> **角色设计核心**：方案A的备选角色是一个**发光的音乐光球小星星**——类似于《星之卡比》里的妖精或《空洞骑士》里的小精灵，但更加软萌治愈。一个小小的发光球体，周围有柔和的光晕，头上长着 tiny 的小星星角，戴着迷你耳机。整体感觉是**科技感+梦幻感**，软萌治愈的。

---

## 1. UI 界面设计图生成提示词 (UI Mockups)

**【生图尺寸建议】**
- 生成 UI 面板建议选择 **`1024x1536` (竖屏)** 或 **`1024x1024` (默认方形)**。因为桌面悬浮面板和菜单通常是纵向延伸的布局。

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

Top area (Live Status HUD): A mini-dashboard integrated into the top of the menu. On the left, a small, highly detailed holographic avatar of a glowing light-orb fairy inside a circular glowing border. Next to it, a tiny real-time line chart showing "Vibe Fluctuation". Below the chart, crisp technical text reading "SYS.STATUS: FINDING TRACK..." and "NOW_PLAYING: MIDNIGHT RAIN".
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

> **目标**：生成一个发光音乐光球小星星的待机呼吸序列帧。切图后作为 `pet_conf.json` 中的 `default` (如 `stand_0.png` ~ `stand_3.png`)。

**Prompt:**
```text
A 2D sprite sheet of an adorable, tiny glowing light-orb fairy mascot — just like a cute Hollow Knight fairy or a magical Kirby character, but softer and more cuddly. The character is a small, perfect glowing sphere with a soft, warm light aura surrounding it. On top of its head are two tiny, cute star-shaped horns. It is wearing a pair of adorable miniature headphones that look slightly oversized on its tiny body.

Content: A horizontal sequence of 4 to 6 frames showing a gentle "idle floating and glowing" animation. The small glowing orb gently pulses brighter and dimmer, like a breathing light. It slowly floats up and down in a dreamy motion. Tiny sparkles or stardust particles gently float around it. Its tiny star horns wobble cutely.
Color palette: Warm golden-white glow, soft light blue aura, and tiny starlight sparkles.
Style: Cute magical fairy, soft glowing aesthetic, dreamy and ethereal, like a gentle will-o-wisp or forest spirit, non-threatening and very huggable. Arranged in a neat horizontal row on a SOLID WHITE background.
```

### 2.2 状态变体：专注 (Focus State)

> **目标**：生成角色专注心流状态的序列帧。切图后对应 `focus_0.png` ~ `focus_3.png`。

**Prompt:**
```text
A 2D sprite sheet of an adorable, tiny glowing light-orb fairy mascot — just like a cute Hollow Knight fairy or a magical Kirby character, but softer and more cuddly. The character is a small, perfect glowing sphere with a soft, warm light aura surrounding it. On top of its head are two tiny, cute star-shaped horns. It is wearing a pair of adorable miniature headphones that look slightly oversized on its tiny body.

Content: A horizontal sequence of 4 to 6 frames showing a "focused and excited" animation. The glowing orb shines brighter with excitement. Its tiny star horns perk up straight and alert. Small music notes or soundwave symbols appear and pulse above its head. The whole orb bounces slightly with energy, like it's vibing to the music.
Color palette: Bright golden-white glow, energetic purple-blue aura, and vibrant music note sparkles.
Style: Cute magical fairy, energetic glowing aesthetic, excited but still adorable and huggable. Arranged in a neat horizontal row on a SOLID WHITE background.
```

### 2.3 状态变体：疲惫 (Tired State)

> **目标**：生成角色疲惫状态的序列帧。切图后对应 `tired_0.png` ~ `tired_3.png`。

**Prompt:**
```text
A 2D sprite sheet of an adorable, tiny glowing light-orb fairy mascot — just like a cute Hollow Knight fairy or a magical Kirby character, but softer and more cuddly. The character is a small, perfect glowing sphere with a soft, warm light aura surrounding it. On top of its head are two tiny, cute star-shaped horns. It is wearing a pair of adorable miniature headphones that have slipped down around its body.

Content: A horizontal sequence of 4 to 6 frames showing a "tired and sleepy" animation. The glowing orb dims significantly, becoming much less bright. Its tiny star horns droop down tiredly. Small "Zzz" bubbles float up and expand above it. The whole orb sways gently like it's about to drift off to sleep.
Color palette: Dimmed soft blue-grey glow, sleepy muted lavender aura, and faint starlight.
Style: Cute magical fairy, sleepy dimmed aesthetic, vulnerable but still adorable. Arranged in a neat horizontal row on a SOLID WHITE background.
```

### 2.4 状态变体：烦躁 (Frustrated State)

> **目标**：生成角色烦躁/Debug崩溃状态的序列帧。切图后对应 `frustrated_0.png` ~ `frustrated_3.png`。

**Prompt:**
```text
A 2D sprite sheet of an adorable, tiny glowing light-orb fairy mascot — just like a cute Hollow Knight fairy or a magical Kirby character, but softer and more cuddly. The character is a small, perfect glowing sphere with a soft, warm light aura surrounding it. On top of its head are two tiny, cute star-shaped horns. It is wearing a pair of adorable miniature headphones.

Content: A horizontal sequence of 4 to 6 frames showing a "frustrated but still adorable" animation. The glowing orb pulses erratically in brightness, flickering on and off. Its tiny star horns shake and wobble back and forth. Small puff clouds or spark symbols pop and dissipate above it. The whole orb bounces up and down slightly as if vibrating with frustration.
Color palette: Warm golden-white base with flushed warm pink pulses and energetic spark accents.
Style: Cute magical fairy, frustrated but still adorable and non-threatening, like a grumpy but cute little sprite. Arranged in a neat horizontal row on a SOLID WHITE background.
```

### 2.5 状态变体：低落 (Sad State)

> **目标**：生成角色情绪低落状态的序列帧。切图后对应 `sad_0.png` ~ `sad_3.png`。

**Prompt:**
```text
A 2D sprite sheet of an adorable, tiny glowing light-orb fairy mascot — just like a cute Hollow Knight fairy or a magical Kirby character, but softer and more cuddly. The character is a small, perfect glowing sphere with a soft, warm light aura surrounding it. On top of its head are two tiny, cute star-shaped horns. It is wearing a pair of adorable miniature headphones.

Content: A horizontal sequence of 4 to 6 frames showing a "sad and crying" animation. The glowing orb dims significantly, becoming much darker and bluer in tone. Its tiny star horns droop down completely. Large, glimmering teardrops form and fall from the orb. Small rain drops or wilted sparkles fall around it. The whole orb curls slightly inward as if hugging itself.
Color palette: Dimmed cool blue-grey glow, melancholy deep blue aura, and sad teardrop sparkles.
Style: Cute magical fairy, sad and vulnerable but still adorable and huggable, like a lonely little star sprite. Arranged in a neat horizontal row on a SOLID WHITE background.
```
