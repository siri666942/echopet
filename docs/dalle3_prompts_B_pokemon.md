# EchoPet DALL-E 3 (gpt-image) 提示词指南 (方案B-宝可梦风格角色：暖光鹿)

本指南包含用于生成 EchoPet **方案B宝可梦风格角色**（**暖光鹿 / Warm Light Deer**）的 DALL-E 3 提示词。

> **角色设计核心**：方案B的宝可梦风格桌宠是一只**复古温暖风格的暖光小鹿**——类似于宝可梦里的芽鹿或四季鹿，但更加软萌治愈。圆润的鹿身、分叉的可爱鹿角（像小树枝）、温暖的发光纹路、戴着复古风格的耳机。整体是**自然温暖+复古治愈**的风格，像是从森林童话里走出来的小伙伴。

---

## 1. UI 界面设计图生成提示词 (UI Mockups)

**【生图尺寸建议】**
- 生成 UI 面板建议选择 **`1024x1536` (竖屏)** 或 **`1024x1024` (默认方形)**。

### 1.1 主输入与音乐推荐面板 (Input & Music Response Panel)

> **目标**：生成一个复古随身听/宝可梦精灵主题的温暖配色 UI 面板。

**Prompt:**
```text
A UI mockup for an emotional music AI desktop app named "EchoPet". The UI window has a warm, cozy retro aesthetic, reminiscent of a vintage record player or a Pokemon Center. The background is a soft, creamy off-white (#F4F1EA). The design features rounded corners, soft shadows, and warm wood textures.

The window is vertically divided. 
Top section (Input): A cute paper note-style text input area with a subtle lined paper texture. Next to it, a prominent glowing red circular microphone button, pulsing softly. The button has a slightly 3D, tactile look.
Bottom section (Music Card): A beautifully designed music recommendation card. A square lo-fi album cover on the left with a warm vintage filter. On the right side: bold song title text, smaller artist text in warm grey, and small pill-shaped emotion tags like "[lofi]" and "[calm]" in warm pastel colors. Below the track info, three friendly round buttons with soft icons: a thumbs up, a skip icon, and a lightning bolt.

Overall style: Warm, cozy, Pokemon-game-UI aesthetic, nostalgic yet modern, highly detailed, Dribbble quality.
```

### 1.2 桌面右键菜单栏 (Desktop Context Menu)

> **目标**：生成一个与复古随身听/卡带机主界面风格完美匹配的右键菜单。它看起来应该像是一个小型的外接硬件模块或便携式设备的控制面板。

**Prompt:**
```text
A highly detailed UI mockup of a desktop context menu for a retro-style music app named "EchoPet". The design must strictly follow a skeuomorphic vintage electronics aesthetic, resembling a small external hardware module or a portable tape player's control panel.

The menu is a vertical rectangle with rounded corners, made of warm off-white industrial plastic with subtle wear and tiny screws in the corners. 
Top section (Status Monitor): A small, inset green LCD screen (like an old calculator or Walkman display). Inside the screen: pixelated text showing "STATUS: FINDING VIBE...", a tiny pixel-art avatar of a cute deer, and a small animated equalizer bar.
Middle section (Current Track): A recessed area with a warm vintage paper label displaying the currently playing song: "▶ Midnight Rain" in a typewriter font.
Bottom section (Mechanical Actions): Three chunky, physical-looking rectangular push buttons aligned vertically. The buttons are off-white with dark grey engraved text: "[ OPEN ECHOPET ]", "[ DEBUG ]", and "[ EJECT / EXIT ]". 

Overall style: Retro industrial design, skeuomorphism, cassette player aesthetics, highly detailed textures, tactile buttons, Dribbble quality UI design.
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

> **目标**：生成一只暖光小鹿的待机呼吸序列帧。切图后作为 `pet_conf.json` 中的 `default` (如 `stand_0.png` ~ `stand_3.png`)。

**Prompt:**
```text
A 2D sprite sheet of an adorable warm light deer mascot — just like a cute Pokemon deer such as Deerling or Sawsbuck, but softer and more cuddly. The character has a round, compact deer body, short stubby legs, a fluffy chest, small branching antlers that look like tiny tree branches with soft glowing tips, large expressive round eyes, and it is wearing a pair of cute vintage-style headphones.

Content: A horizontal sequence of 4 to 6 frames showing a gentle "idle breathing and tail swaying" animation. The round deer body gently bobs up and down with breathing. Its large eyes blink slowly in a peaceful, content expression. Its small branching antlers glow softly with a warm light. Its fluffy tail sways gently side to side. Tiny sparkles or warm light particles float and shimmer around it.
Color palette: Warm cream and soft brown fur, glowing warm orange antler tips, and gentle golden sparkles.
Style: Cute Pokemon deer, soft plush-like feel, smooth rounded shapes, warm natural aesthetic, safe and non-scary. Arranged in a neat horizontal row on a SOLID WHITE background.
```

### 2.2 状态变体：专注 (Focus State)

> **目标**：生成角色专注心流状态的序列帧。切图后对应 `focus_0.png` ~ `focus_3.png`。

**Prompt:**
```text
A 2D sprite sheet of an adorable warm light deer mascot — just like a cute Pokemon deer such as Deerling or Sawsbuck, but softer and more cuddly. The character has a round, compact deer body, short stubby legs, a fluffy chest, small branching antlers that look like tiny tree branches with soft glowing tips, large expressive round eyes, and it is wearing a pair of cute vintage-style headphones.

Content: A horizontal sequence of 4 to 6 frames showing a "focused and alert" animation. Its large eyes are wide open with sharp concentration and excitement. Its small branching antlers glow brighter with a warm energetic light. Its ears perk up straight and alert. A small glowing warm light or soundwave icon pulses above its head. Its fluffy tail stands still or vibrates slightly with tension. Tiny warm light particles spark and shimmer energetically around it.
Color palette: Warm cream and soft brown fur, bright glowing orange antler tips, and energetic golden sparkles.
Style: Cute Pokemon deer, alert energetic feel, smooth rounded shapes, warm natural aesthetic, safe and non-scary. Arranged in a neat horizontal row on a SOLID WHITE background.
```

### 2.3 状态变体：疲惫 (Tired State)

> **目标**：生成角色疲惫状态的序列帧。切图后对应 `tired_0.png` ~ `tired_3.png`。

**Prompt:**
```text
A 2D sprite sheet of an adorable warm light deer mascot — just like a cute Pokemon deer such as Deerling or Sawsbuck, but softer and more cuddly. The character has a round, compact deer body, short stubby legs, a fluffy chest, small branching antlers that look like tiny tree branches with dimmed glowing tips, large round eyes, and it is wearing a pair of cute vintage-style headphones that have slipped down around its neck.

Content: A horizontal sequence of 4 to 6 frames showing a "tired and sleepy" animation. Its large round eyes are half-closed and droopy, slowly blinking. Its small branching antlers glow dimly with a weak light. Its ears droop down tiredly. Small "Zzz" bubbles float up above its head. Its fluffy tail drags on the ground, swaying weakly. Its round body sways gently, getting heavier with sleepiness. The vintage headphones are askew.
Color palette: Warm cream and soft brown fur, dim glowing amber antler tips, and sleepy muted golden sparkles.
Style: Cute Pokemon deer, tired low-energy feel, smooth rounded shapes, warm natural aesthetic, safe and non-scary. Arranged in a neat horizontal row on a SOLID WHITE background.
```

### 2.4 状态变体：烦躁 (Frustrated State)

> **目标**：生成角色烦躁/Debug崩溃状态的序列帧。切图后对应 `frustrated_0.png` ~ `frustrated_3.png`。

**Prompt:**
```text
A 2D sprite sheet of an adorable warm light deer mascot — just like a cute Pokemon deer such as Deerling or Sawsbuck, but softer and more cuddly. The character has a round, compact deer body, short stubby legs, a fluffy chest, small branching antlers that look like tiny tree branches with flickering glowing tips, large round eyes, and it is wearing a pair of cute vintage-style headphones.

Content: A horizontal sequence of 4 to 6 frames showing a "frustrated but still adorable" animation. Its large eyes are squeezed shut tight in a squiggly frustrated expression. Its tiny mouth makes a small pouting shape. Its small branching antlers flicker erratically with an unstable light. Its fluffy tail bristles and flicks back and forth rapidly. Small puff clouds or spark symbols pop and dissipate above its head. Its ears flatten back in annoyance. The vintage headphones vibrate slightly.
Color palette: Warm cream and soft brown fur, warm flushed pink glowing antler tips, and soft passionate orange sparkles.
Style: Cute Pokemon deer, frustrated glitchy feel, smooth rounded shapes, warm natural aesthetic, safe and non-scary. Arranged in a neat horizontal row on a SOLID WHITE background.
```

### 2.5 状态变体：低落 (Sad State)

> **目标**：生成角色情绪低落状态的序列帧。切图后对应 `sad_0.png` ~ `sad_3.png`。

**Prompt:**
```text
A 2D sprite sheet of an adorable warm light deer mascot — just like a cute Pokemon deer such as Deerling or Sawsbuck, but softer and more cuddly. The character has a round, compact deer body, short stubby legs, a fluffy chest, small branching antlers that look like tiny tree branches with dimmed glowing tips, large round eyes, and it is wearing a pair of cute vintage-style headphones.

Content: A horizontal sequence of 4 to 6 frames showing a "sad and crying" animation. Its enormous round eyes are full of large glimmering teardrops. Its tiny triangular ears droop down completely. It is curled slightly into itself, looking down. A few tiny blue teardrops slowly fall from its eyes. Small wilted data particles or dimmed sparkles float around it. The glowing headphones are dimmed and flickering weakly.
Color palette: Dimmed cool blue-grey fur, melancholy deep blue glowing antler tips, and sad teardrop sparkles.
Style: Cute Pokemon deer, sad low-energy feel, smooth rounded shapes, warm natural aesthetic, safe and non-scary. Arranged in a neat horizontal row on a SOLID WHITE background.
```
