# EchoPet DALL-E 3 (gpt-image) 提示词指南 (方案B)

本指南用于生成 EchoPet 方案B（**宝可梦精灵风 / Pokémon Creature Style**）的 UI 设计图和角色资产。

> **角色设计核心**：方案B的桌宠是一个**圆润可爱的小精灵**，类似于宝可梦 / 洛克王国的风格——软糯的圆形身体、大而明亮的眼睛、小巧的耳朵、戴着耳机。整体感觉是温暖治愈的，而不是恐怖的。

---

## 1. UI 界面设计图生成提示词 (UI Mockups)

**【生图尺寸建议】**
- 生成 UI 面板建议选择 **`1024x1536` (竖屏)** 或 **`1024x1024` (默认方形)**。

### 1.1 主输入与音乐推荐面板 (Input & Music Response Panel)

> **目标**：生成一个复古唱片机 / 宝可梦精灵主题的温暖配色 UI 面板。

**Prompt:**
```text
A UI mockup for an emotional music AI desktop app named "EchoPet". The UI window has a warm, cozy retro aesthetic, reminiscent of a vintage record player or a Pokemon Center. The background is a soft, creamy off-white (#F4F1EA). The design features rounded corners, soft shadows, and warm wood textures.

The window is vertically divided. 
Top section (Input): A cute paper note-style text input area with a subtle lined paper texture. Next to it, a prominent glowing red circular microphone button, pulsing softly. The button has a slightly 3D, tactile look.
Bottom section (Music Card): A beautifully designed music recommendation card. A square album cover on the left with a warm vintage filter. On the right side: bold song title text, smaller artist text in warm grey, and small pill-shaped emotion tags like "[lofi]" and "[calm]" in warm pastel colors. Below the track info, three friendly round buttons with soft icons: a thumbs up, a skip icon, and a lightning bolt.

Overall style: Warm, cozy, Pokemon-game-UI aesthetic, nostalgic yet modern, highly detailed, Dribbble quality.
```

### 1.2 桌面右键菜单栏 (Desktop Context Menu)

> **目标**：生成一个宝可梦精灵风可爱的右键菜单。

**Prompt:**
```text
A highly polished UI design of a desktop context menu for a cute music app. The menu has a warm, creamy off-white background with extra-thick rounded corners and a soft, warm drop shadow. The overall vibe is like a friendly Pokemon game interface.

Top area (Status Header): A mini status card with a very subtle gradient background. On the left, a tiny cute circular avatar of a small fluffy music精灵 (fairy creature) wearing headphones. On the right, stacked neatly in clean typography: "🎧 Searching for music..." (in warm orange), "▶️ Playing", and "🎵 Midnight Rain".
Bottom area (Actions): Friendly, rounded menu items. The first item "Open EchoPet" is slightly larger with a small music note icon. Below it, subtle grey items like "Debug Tools" and "Exit".

Style: Warm, Pokemon-game-inspired, soft and friendly, clean typography, cozy vibes.
```

---

## 2. 角色美术资产生成提示词 (Character Sprite Sheets)

**【极度重要：DyberPet 序列帧规范与后期处理】**
1. **生成**：使用宽屏尺寸 `1536x1024` 生成白底的横向序列图。
2. **去底**：使用抠图工具一键去除纯白背景，保留透明通道。
3. **切分**：将宽图横向等分为 4 份或 6 份独立的 PNG。
4. **缩放**：根据 `pet_conf.json` 里的要求（如缩小到 128x128 左右）。对于像素画，缩放时请务必使用**"邻近 (Nearest Neighbor)"**插值算法，以保持像素边缘硬朗。
5. **命名**：放入 `action/` 文件夹，并严格命名为 `动作名_0.png`, `动作名_1.png` 等。

### 2.1 角色基础待机 (Idle / Default State)

> **目标**：生成一个宝可梦风格小精灵的待机呼吸序列帧。切图后作为 `pet_conf.json` 中的 `default` (如 `stand_0.png` ~ `stand_3.png`)。

**Prompt:**
```text
A 2D sprite sheet of an adorable, round, fluffy music fairy creature mascot — just like a cute Pokemon character. The creature has a perfectly round, marshmallow-soft body, big sparkly round eyes, tiny round ears on top of its head, and it is wearing a pair of oversized cute headphones.

Content: A horizontal sequence of 4 to 6 frames showing a gentle "idle breathing" animation. The creature floats up and down softly. Its eyes are half-closed in a content, peaceful expression. Small musical notes or tiny sparkles float and gently sway above its head across the frames.
Color palette: Warm cream white, soft peach pink, and gentle music-note yellow accents.
Style: Cute Pokemon / 洛克王国 style, smooth vector art, kawaii, big expressive eyes, soft rounded shapes. Arranged in a neat horizontal row on a SOLID WHITE background.
```

### 2.2 状态变体：专注 (Focus State)

> **目标**：生成角色专注心流状态的序列帧。切图后对应 `focus_0.png` ~ `focus_3.png`。

**Prompt:**
```text
A 2D sprite sheet of an adorable, round, fluffy music fairy creature mascot — just like a cute Pokemon character. The creature has a perfectly round, marshmallow-soft body, big sparkly round eyes, tiny round ears on top of its head, and it is wearing a pair of oversized cute headphones.

Content: A horizontal sequence of 4 to 6 frames showing a "focused and hard at work" animation. Its eyes are wide open and determined, looking at something exciting. Tiny sparkles of excitement or a small music bar icon pulses above its head. Its ears perk up energetically across the frames.
Color palette: Warm cream white, energetic yellow, and focused lavender purple accents.
Style: Cute Pokemon / 洛克王国 style, smooth vector art, kawaii, big expressive eyes, soft rounded shapes. Arranged in a neat horizontal row on a SOLID WHITE background.
```

### 2.3 状态变体：疲惫 (Tired State)

> **目标**：生成角色疲惫状态的序列帧。切图后对应 `tired_0.png` ~ `tired_3.png`。

**Prompt:**
```text
A 2D sprite sheet of an adorable, round, fluffy music fairy creature mascot — just like a cute Pokemon character. The creature has a perfectly round, marshmallow-soft body, big sparkly round eyes, tiny round ears on top of its head, and it is wearing oversized cute headphones that have slipped down around its neck.

Content: A horizontal sequence of 4 to 6 frames showing a "tired and sleepy" animation. Its big round eyes are half-closed and droopy. It yawns slowly, and its tiny ears droop down tiredly. Small "Zzz" bubbles slowly float up above its head. The creature's whole body slowly sways as if about to fall asleep.
Color palette: Warm cream white, sleepy lavender grey, and dim soft blue accents.
Style: Cute Pokemon / 洛克王国 style, smooth vector art, kawaii, big expressive eyes, soft rounded shapes. Arranged in a neat horizontal row on a SOLID WHITE background.
```

### 2.4 状态变体：烦躁 (Frustrated State)

> **目标**：生成角色烦躁/Debug崩溃状态的序列帧。切图后对应 `frustrated_0.png` ~ `frustrated_3.png`。

**Prompt:**
```text
A 2D sprite sheet of an adorable, round, fluffy music fairy creature mascot — just like a cute Pokemon character. The creature has a perfectly round, marshmallow-soft body, big sparkly round eyes, tiny round ears on top of its head, and it is wearing oversized cute headphones.

Content: A horizontal sequence of 4 to 6 frames showing a "frustrated and angry" animation. Its big eyes are squinted shut tight, its tiny mouth is pouting into a small frown. Its ears are flat down. Tiny angry spark symbols (！) shake above its head. Its whole body bounces up and down slightly in frustration.
Color palette: Warm cream white with flushed warm red cheeks and passionate orange accents.
Style: Cute Pokemon / 洛克王国 style, smooth vector art, kawaii, big expressive eyes, soft rounded shapes. Arranged in a neat horizontal row on a SOLID WHITE background.
```

### 2.5 状态变体：低落 (Sad State)

> **目标**：生成角色情绪低落状态的序列帧。切图后对应 `sad_0.png` ~ `sad_3.png`。

**Prompt:**
```text
A 2D sprite sheet of an adorable, round, fluffy music fairy creature mascot — just like a cute Pokemon character. The creature has a perfectly round, marshmallow-soft body, big sparkly round eyes, tiny round ears on top of its head, and it is wearing oversized cute headphones.

Content: A horizontal sequence of 4 to 6 frames showing a "sad and crying" animation. The creature is curled up slightly, looking down. Its big eyes are full of large, glimmering teardrops. Its ears are drooped down sadly. A few tiny blue teardrops fall slowly from its eyes. Small music notes around it look wilted and droopy.
Color palette: Dimmed cool blue-grey tones, cold cyan, and melancholy deep blue accents.
Style: Cute Pokemon / 洛克王国 style, smooth vector art, kawaii, big expressive eyes, soft rounded shapes. Arranged in a neat horizontal row on a SOLID WHITE background.
```