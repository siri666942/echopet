# EchoPet DALL-E 3 (gpt-image) 提示词指南 (方案B)

本指南用于生成 EchoPet 方案B（**复古随身听/像素蒸汽波 Retro Lo-Fi / Pixel Vaporwave**）的 UI 设计图和角色资产。

---

## 1. UI 界面设计图生成提示词 (UI Mockups)

### 1.1 主输入与音乐推荐面板 (Input & Music Response Panel)

> **目标**：生成一个看起来像复古随身听、带有实体按钮质感和复古配色的 UI 面板。

**Prompt:**
```text
A UI mockup for an emotional music AI desktop app named "EchoPet". The UI window is designed to look like a modern, minimalist retro Walkman or vintage synthesizer. The background color is a nostalgic creamy off-white (#F4F1EA). The design features "neo-brutalism" or retro UI elements with hard black shadows and thick borders.

The window is vertically divided. 
Top section (Input): Looks like a cassette tape slot with a paper label serving as the text input area. Next to it is a prominent, tactile, chunky red circular "REC" (Record) button that looks like a physical mechanical button. A small red LED light is glowing next to it.
Bottom section (Music Card): A retro music player display. A square lo-fi album cover on the left. On the right, a greenish LCD screen displaying the song title and artist in pixelated digital font. Below this, three chunky rectangular mechanical buttons with the labels "[ KEEP ]", "[ SKIP ]", and "[ BOOST ]". 

Overall style: Retro Lo-Fi, nostalgic comfort, neat, highly detailed UI design, Dribbble style, aesthetic, vaporwave color accents (sunset orange, tape green).
```

### 1.2 桌面右键菜单栏 (Desktop Context Menu)

> **目标**：生成一个带有 LCD 屏幕状态栏的复古风格右键菜单。

**Prompt:**
```text
A highly polished UI design of a desktop context menu in a Retro/Neo-brutalism style. The menu has a creamy off-white background with a thick black outline and a solid hard drop shadow.

Top area (Status Header): Designed to look like a mini vintage LCD display screen. The background of this top area is a classic digital yellow-green color. It shows a tiny pixel-art avatar of a cute cassette tape, and next to it, black pixelated text reading: "STATUS: SEARCHING...", "PLAYING: LO-FI".
Bottom area (Actions): Clean menu items. The first item says "Open EchoPet" with a small retro eject icon. Below it are items like "Debug Tools" and "Exit".

Style: Clean retro tech, 90s aesthetic, UI/UX design, nostalgic, highly detailed.
```

---

## 2. 角色美术资产生成提示词 (Character Sprite Sheets)

**【极度重要：DyberPet 序列帧规范】**
DyberPet 需要的是可以播放动画的**序列帧图片 (Sprite Sequence)**，而不是单张静图。图片必须放入 `action/` 文件夹，并命名为 `动作名_0.png`, `动作名_1.png` 等。
下面的提示词强制要求生成**像素角色动作序列帧表 (Pixel Sprite Sheet)**，并采用纯白背景，方便后期一键去底。

### 2.1 角色基础设定 (Base Concept - Idle / Default State)

> **目标**：生成一个可爱的像素随身听精灵的待机序列帧。切图后作为 `pet_conf.json` 中的 `default` (如 `stand_0.png` ~ `stand_3.png`)。

**Prompt:**
```text
A high-quality 2D pixel art sprite sheet of a cute, friendly mascot. The character is a living, anthropomorphic retro cassette tape or mini walkman wearing tangled wired earphones.

Content: A horizontal sequence of 4 to 6 frames showing an "idle breathing" animation. The cassette reels spin slowly. Small pixelated musical notes float above its head and change positions across the frames.
Color palette: Nostalgic creamy white, cassette green, and soft warm orange accents.
Style: Premium hi-bit pixel art, cute, retro gaming aesthetic. Arranged in a neat horizontal row on a SOLID WHITE background (perfect for sprite sheet cutting).
```

### 2.2 状态变体：专注 (Focus State)

> **目标**：生成角色专注心流状态的序列帧。切图后对应 `focus_0.png` ~ `focus_3.png`。

**Prompt:**
```text
A high-quality 2D pixel art sprite sheet of a cute anthropomorphic retro cassette tape wearing wired earphones.

Content: A horizontal sequence of 4 to 6 frames showing a "focused and studying" animation. It is wearing thick black "nerd" glasses. A tiny pixelated flame of determination burns and flickers above its head across the frames. The cassette reels spin very fast.
Color palette: Creamy white with focused yellow and orange accents.
Style: Premium hi-bit pixel art, cute, retro gaming aesthetic. Arranged in a neat horizontal row on a SOLID WHITE background.
```

### 2.3 状态变体：疲惫 (Tired State)

> **目标**：生成角色疲惫状态的序列帧。切图后对应 `tired_0.png` ~ `tired_3.png`。

**Prompt:**
```text
A high-quality 2D pixel art sprite sheet of a cute anthropomorphic retro cassette tape wearing wired earphones.

Content: A horizontal sequence of 4 to 6 frames showing a "tired and glitchy" animation. The character's eyes are swirling spirals. A piece of magnetic tape hangs out of its mouth, swaying slightly. A pixelated "Zzz" bubble floats next to it. There is a slight VHS glitch effect flickering on its edges across the frames.
Color palette: Creamy white with dim, tired grey and sunset orange accents.
Style: Premium hi-bit pixel art, cute, retro gaming aesthetic. Arranged in a neat horizontal row on a SOLID WHITE background.
```

### 2.4 状态变体：烦躁 (Frustrated State)

> **目标**：生成角色烦躁/Debug崩溃状态的序列帧。切图后对应 `frustrated_0.png` ~ `frustrated_3.png`。

**Prompt:**
```text
A high-quality 2D pixel art sprite sheet of a cute anthropomorphic retro cassette tape wearing wired earphones.

Content: A horizontal sequence of 4 to 6 frames showing a "frustrated and angry" animation. Its face is flushed red. A lot of magnetic tape is tangled up around it, wriggling messily. Above its head, a pixelated anger symbol (💢) throbs across the frames.
Color palette: Creamy white with strong, frustrated retro red accents.
Style: Premium hi-bit pixel art, cute, retro gaming aesthetic. Arranged in a neat horizontal row on a SOLID WHITE background.
```

### 2.5 状态变体：低落 (Sad State)

> **目标**：生成角色情绪低落状态的序列帧。切图后对应 `sad_0.png` ~ `sad_3.png`。

**Prompt:**
```text
A high-quality 2D pixel art sprite sheet of a cute anthropomorphic retro cassette tape wearing wired earphones.

Content: A horizontal sequence of 4 to 6 frames showing a "sad and melancholic" animation. It looks downcast. A large pixel tear drops from its eye. Above it, a tiny dark pixel cloud rains small blue drops continuously across the frames.
Color palette: Desaturated creamy white with melancholy midnight blue and cold cyan accents.
Style: Premium hi-bit pixel art, cute, retro gaming aesthetic. Arranged in a neat horizontal row on a SOLID WHITE background.
```