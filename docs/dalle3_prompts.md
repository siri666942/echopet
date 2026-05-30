# EchoPet DALL-E 3 (gpt-image) 提示词指南

本指南包含用于生成 EchoPet 界面设计图（UI Mockups）和角色资产（Character Assets）的 DALL-E 3 提示词。你可以直接复制这些英文提示词交给图像生成大模型。

---

## 1. UI 界面设计图生成提示词 (UI Mockups)

这些提示词用于生成界面的概念设计图，帮助你在黑客松路演中展示高级感，也可以作为前端切图的视觉参考。

### 1.1 主输入与音乐推荐面板 (Input & Music Response Panel)

> **目标**：生成一个深色模式、具有亚克力毛玻璃质感、结合了语音输入和音乐推荐卡片的现代 UI 窗口。

**Prompt:**
```text
A modern, high-end desktop application UI mockup for an emotional music AI agent called "EchoPet". The UI is a floating rectangular window with rounded corners. The theme is dark mode with a frosted glass (acrylic/blur) background. 

The window is vertically divided into two sections. 
Top section (Input): A sleek, minimalist search bar with placeholder text "Tell EchoPet how you feel...". Next to it, a prominent, glowing circular microphone button indicating active listening. 
Bottom section (Music Card): A beautifully designed music recommendation card. It features a square album art on the left, bold white text for the song title, grey text for the artist, and small pill-shaped tags like "[lofi]" and "[calm]" with a subtle purple tint. Below the track info, there are three minimalist buttons with emojis: "👍", "👎", and "⚡". 

The overall style should be Cyber-Warmth, minimalist, futuristic yet cozy, similar to Fluent Design or macOS macOS Big Sur design language. Clean typography, no cluttered gaming elements.
```

### 1.2 桌面右键菜单栏 (Desktop Context Menu)

> **目标**：生成一个带有微型状态卡片和操作选项的精致右键菜单。

**Prompt:**
```text
A highly polished, dark mode context menu UI design floating on a desktop background. The menu has soft rounded corners and a translucent frosted glass effect (acrylic material).

The menu has two main areas. 
Top area (Status Header): A mini-card integrated into the top of the menu. On the left, a small, cute avatar of a cyber-ghost wearing headphones. On the right, three lines of text neatly stacked: "🎧 Finding music for you..." (highlighted in soft blue), "▶️ Playing", and "🎵 Midnight Rain". 
Bottom area (Actions): Clean, minimalist list items with simple icons. The first item is "Open EchoPet" in bold text. Below it are subtle grey options like "Debug Tools" and "Exit".

The visual style is elegant, modern, and professional, suitable for a hackathon presentation. Crisp text, dark grey background (#1C1C1E), and precise padding.
```

---

## 2. 角色美术资产生成提示词 (Character Sprite Sheets)

**【极度重要：DyberPet 序列帧规范】**
DyberPet 需要的是可以播放动画的**序列帧图片 (Sprite Sequence)**，而不是单张静图。图片必须放入 `action/` 文件夹，并命名为 `动作名_0.png`, `动作名_1.png` 等。
因此，下面的提示词强制要求大模型生成**角色动作序列帧表 (Sprite Sheet)**，且采用纯色背景，方便你后期切图和抠出透明底。

### 2.1 角色基础设定 (Base Concept - Idle / Default State)

> **目标**：生成一个可爱的音乐赛博小精灵的待机呼吸序列帧。切图后作为 `pet_conf.json` 中的 `default` (如 `stand_0.png` ~ `stand_3.png`)。

**Prompt:**
```text
A 2D sprite sheet of a cute, friendly "music cyber-ghost" mascot. The character has a smooth, round, marshmallow-like body, wearing modern oversized over-ear headphones. 

Content: A horizontal sequence of 4 to 6 frames showing a smooth "idle breathing" animation. The character gently floats up and down, with eyes closed in a peaceful expression.
Color palette: Clean white and soft glowing blue. 
Style: Minimalist, flat vector design, cute, tech-friendly, similar to modern tech startup mascots. 
Layout: Arranged in a neat grid or a single horizontal row on a SOLID WHITE background (perfect for background removal). No background clutter.
```

### 2.2 状态变体：专注 (Focus State)

> **目标**：角色进入工作/心流状态的序列帧。切图后对应 `focus_0.png` ~ `focus_3.png`。

**Prompt:**
```text
A 2D sprite sheet of a cute, friendly "music cyber-ghost" mascot, identical in style to a smooth, round, marshmallow-like body wearing modern oversized over-ear headphones. 

Content: A horizontal sequence of 4 to 6 frames showing a "focus and typing" animation. Its eyes are wide open. It is typing on a floating holographic keyboard. Above its head, a small glowing purple soundwave icon pulses slightly across the frames.
Color palette: Clean white with soft glowing purple accents.
Style: Minimalist, flat vector design, tech-friendly. Arranged in a neat horizontal row on a SOLID WHITE background.
```

### 2.3 状态变体：疲惫 (Tired State)

> **目标**：角色表现出熬夜或疲劳的序列帧。切图后对应 `tired_0.png` ~ `tired_3.png`。

**Prompt:**
```text
A 2D sprite sheet of a cute, friendly "music cyber-ghost" mascot, identical in style to a smooth, round, marshmallow-like body. 

Content: A horizontal sequence of 4 to 6 frames showing a "tired and sleepy" animation. The oversized headphones have slipped down to rest around its neck. Its eyes are half-closed. It slowly nods off and wakes up. A small "Zzz" bubble floats and expands next to it across the frames.
Color palette: Clean white with dim, desaturated greyish-blue accents.
Style: Minimalist, flat vector design, tech-friendly. Arranged in a neat horizontal row on a SOLID WHITE background.
```

### 2.4 状态变体：烦躁 (Frustrated State)

> **目标**：角色表现出 Debug 失败时烦躁的序列帧。切图后对应 `frustrated_0.png` ~ `frustrated_3.png`。

**Prompt:**
```text
A 2D sprite sheet of a cute, friendly "music cyber-ghost" mascot, identical in style to a smooth, round, marshmallow-like body wearing modern oversized over-ear headphones. 

Content: A horizontal sequence of 4 to 6 frames showing a "frustrated and angry" animation. Its eyes are squeezed shut. Its body pulses with a faint red glow. Above its head, a red scribbled "tangled yarn" icon (💢) jiggles. Its tiny hands wave up and down in frustration.
Color palette: Clean white with glowing warning-red accents.
Style: Minimalist, flat vector design, tech-friendly. Arranged in a neat horizontal row on a SOLID WHITE background.
```

### 2.5 状态变体：低落 (Sad State)

> **目标**：角色表现出需要安慰的低落序列帧。切图后对应 `sad_0.png` ~ `sad_3.png`。

**Prompt:**
```text
A 2D sprite sheet of a cute, friendly "music cyber-ghost" mascot, identical in style to a smooth, round, marshmallow-like body wearing modern oversized over-ear headphones. 

Content: A horizontal sequence of 4 to 6 frames showing a "sad and shivering" animation. It is huddled up into a small ball, hugging its knees. Small, sad blue rain particles fall around it across the frames.
Color palette: Dimmed white with melancholy cold-cyan glowing accents.
Style: Minimalist, flat vector design, tech-friendly. Arranged in a neat horizontal row on a SOLID WHITE background.
```