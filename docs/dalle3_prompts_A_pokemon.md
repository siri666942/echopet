# EchoPet DALL-E 3 (gpt-image) 提示词指南 (方案A-宝可梦风格角色：数据狐)

本指南包含用于生成 EchoPet **方案A宝可梦风格角色**（**数据狐 / Data Fox**）的 DALL-E 3 提示词。

> **角色设计核心**：方案A的宝可梦风格桌宠是一只**赛博科技感的数据狐狸**——类似于宝可梦里的伊布或六尾，但带有科技元素。流线型的狐狸身体、三角形的科技耳、发光的数据纹路、戴着耳机。整体是**未来科技+萌系可爱**的风格。

---

## 1. UI 界面设计图生成提示词 (UI Mockups)

**【生图尺寸建议】**
- 生成 UI 面板建议选择 **`1024x1536` (竖屏)** 或 **`1024x1024` (默认方形)**。

### 1.1 主输入与音乐推荐面板 (Input & Music Response Panel)

> **目标**：生成一个深色模式、具有亚克力毛玻璃质感、结合了语音输入和音乐推荐卡片的现代 UI 窗口。

**Prompt:**
```text
A modern, high-end desktop application UI mockup for an emotional music AI agent called "EchoPet". The UI is a floating rectangular window with rounded corners. The theme is dark mode with a frosted glass (acrylic/blur) background. 

The window is vertically divided into two sections. 
Top section (Input): A sleek, minimalist search bar with placeholder text "Tell EchoPet how you feel...". Next to it, a prominent, glowing circular microphone button indicating active listening. 
Bottom section (Music Card): A beautifully designed music recommendation card. It features a square album art on the left, bold white text for the song title, grey text for the artist, and small pill-shaped tags like "[lofi]" and "[calm]" with a subtle purple tint. Below the track info, there are three minimalist buttons with emojis: "👍", "👎", and "⚡". 

The overall style should be Cyber-Warmth, minimalist, futuristic yet cozy, similar to Fluent Design or macOS Big Sur design language. Clean typography, no cluttered gaming elements.
```

### 1.2 桌面右键菜单栏 (Desktop Context Menu)

> **目标**：生成一个带有微型状态卡片和操作选项的精致右键菜单。

**Prompt:**
```text
A highly polished, dark mode context menu UI design floating on a desktop background. The menu has soft rounded corners and a translucent frosted glass effect (acrylic material).

The menu has two main areas. 
Top area (Status Header): A mini-card integrated into the top of the menu. On the left, a small, cute circular avatar of a cyber data fox with headphones and glowing data patterns. On the right, three lines of text neatly stacked: "🎧 Finding music for you..." (highlighted in soft blue), "▶️ Playing", and "🎵 Midnight Rain". 
Bottom area (Actions): Clean, minimalist list items with simple icons. The first item is "Open EchoPet" in bold text. Below it are subtle grey options like "Debug Tools" and "Exit".

The visual style is elegant, modern, and professional, suitable for a hackathon presentation. Crisp text, dark grey background (#1C1C1E), and precise padding.
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

> **目标**：生成一只赛博数据狐狸的待机呼吸序列帧。切图后作为 `pet_conf.json` 中的 `default` (如 `stand_0.png` ~ `stand_3.png`)。

**Prompt:**
```text
A 2D sprite sheet of an adorable cyber data fox mascot — just like a cute Pokemon fox such as Eevee or Vulpix, but with futuristic tech elements. The character has a sleek, compact fox body, a large fluffy tail with glowing data pattern tips, triangular ears with circuit-like markings, enormous sparkly round eyes, and it is wearing a pair of oversized futuristic glowing headphones.

Content: A horizontal sequence of 4 to 6 frames showing a gentle "idle breathing and tail swaying" animation. The fluffy data-patterned tail gently sways side to side. Its enormous eyes blink slowly in a peaceful, content expression. Tiny sparkles or data particles float and shimmer around it. Its triangular ears twitch cutely.
Color palette: Clean white and soft grey fur, glowing blue circuit patterns, and soft purple data sparkles.
Style: Cute Pokemon fox, sleek tech aesthetic, smooth rounded shapes, cyber-tech mascot aesthetic, safe and non-scary. Arranged in a neat horizontal row on a SOLID WHITE background.
```

### 2.2 状态变体：专注 (Focus State)

> **目标**：生成角色专注心流状态的序列帧。切图后对应 `focus_0.png` ~ `focus_3.png`。

**Prompt:**
```text
A 2D sprite sheet of an adorable cyber data fox mascot — just like a cute Pokemon fox such as Eevee or Vulpix, but with futuristic tech elements. The character has a sleek, compact fox body, a large fluffy tail with glowing data pattern tips, triangular ears with circuit-like markings, enormous sparkly round eyes, and it is wearing a pair of oversized futuristic glowing headphones.

Content: A horizontal sequence of 4 to 6 frames showing a "focused and alert" animation. Its enormous eyes are wide open with sharp concentration. Its triangular ears perk up straight and alert, twitching at sounds. A small glowing data HUD or soundwave icon pulses above its head. Its data-patterned tail stands still or vibrates slightly with tension. Tiny data particles spark and shimmer energetically around it.
Color palette: Clean white and soft grey fur, bright glowing blue circuit patterns, and energetic purple data sparkles.
Style: Cute Pokemon fox, sleek alert tech aesthetic, smooth rounded shapes, cyber-tech mascot aesthetic, safe and non-scary. Arranged in a neat horizontal row on a SOLID WHITE background.
```

### 2.3 状态变体：疲惫 (Tired State)

> **目标**：生成角色疲惫状态的序列帧。切图后对应 `tired_0.png` ~ `tired_3.png`。

**Prompt:**
```text
A 2D sprite sheet of an adorable cyber data fox mascot — just like a cute Pokemon fox such as Eevee or Vulpix, but with futuristic tech elements. The character has a sleek, compact fox body, a large fluffy tail with dimmed data pattern tips, triangular ears with circuit-like markings, enormous round eyes, and it is wearing a pair of oversized futuristic glowing headphones that have slipped down around its neck.

Content: A horizontal sequence of 4 to 6 frames showing a "tired and sleepy" animation. Its enormous round eyes are half-closed and droopy, slowly blinking. Its triangular ears droop down tiredly. Small "Zzz" bubbles float up above its head. Its fluffy data-patterned tail drags on the ground, swaying weakly. Its whole body sways gently, getting heavier with sleepiness. The glowing headphones are dimmed.
Color palette: Clean white and soft grey fur, dim glowing blue-grey circuit patterns, and sleepy muted blue data sparkles.
Style: Cute Pokemon fox, tired low-energy tech aesthetic, smooth rounded shapes, cyber-tech mascot aesthetic, safe and non-scary. Arranged in a neat horizontal row on a SOLID WHITE background.
```

### 2.4 状态变体：烦躁 (Frustrated State)

> **目标**：生成角色烦躁/Debug崩溃状态的序列帧。切图后对应 `frustrated_0.png` ~ `frustrated_3.png`。

**Prompt:**
```text
A 2D sprite sheet of an adorable cyber data fox mascot — just like a cute Pokemon fox such as Eevee or Vulpix, but with futuristic tech elements. The character has a sleek, compact fox body, a large fluffy tail with flickering data pattern tips, triangular ears with circuit-like markings, enormous round eyes, and it is wearing a pair of oversized futuristic glowing headphones.

Content: A horizontal sequence of 4 to 6 frames showing a "frustrated but still adorable" animation. Its enormous eyes are squeezed shut tight in a squiggly frustrated expression. Its tiny mouth makes a small pouting shape. Its fluffy data-patterned tail bristles and flicks back and forth rapidly. Small puff clouds or error symbols pop and dissipate above its head. Its triangular ears flatten back in annoyance. The glowing headphones flicker erratically.
Color palette: Clean white and soft grey fur, warm flushed pink glowing circuit patterns, and soft passionate orange data sparkles.
Style: Cute Pokemon fox, frustrated glitchy tech aesthetic, smooth rounded shapes, cyber-tech mascot aesthetic, safe and non-scary. Arranged in a neat horizontal row on a SOLID WHITE background.
```

### 2.5 状态变体：低落 (Sad State)

> **目标**：生成角色情绪低落状态的序列帧。切图后对应 `sad_0.png` ~ `sad_3.png`。

**Prompt:**
```text
A 2D sprite sheet of an adorable cyber data fox mascot — just like a cute Pokemon fox such as Eevee or Vulpix, but with futuristic tech elements. The character has a sleek, compact fox body, a large fluffy tail with dimmed data pattern tips, triangular ears with circuit-like markings, enormous round eyes, and it is wearing a pair of oversized futuristic glowing headphones.

Content: A horizontal sequence of 4 to 6 frames showing a "sad and crying" animation. Its enormous round eyes are full of large glimmering teardrops. Its tiny triangular ears droop down completely. It is curled slightly into itself, looking down. A few tiny blue teardrops slowly fall from its eyes. Small wilted data particles or dimmed sparkles float around it. The glowing headphones are dimmed and flickering weakly.
Color palette: Dimmed cool blue-grey fur, melancholy deep blue glowing circuit patterns, and sad teardrop data sparkles.
Style: Cute Pokemon fox, sad low-energy tech aesthetic, smooth rounded shapes, cyber-tech mascot aesthetic, safe and non-scary. Arranged in a neat horizontal row on a SOLID WHITE background.
```
