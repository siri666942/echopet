"""
GPT-Image-2 生图 & 改图脚本
API: https://n.lconai.com
"""

import requests
import base64
import os
from datetime import datetime

# ========== 配置 ==========
API_KEY = "sk-Mrm6DJ2eE52DTv7GPLZTIt45GL4e5370kDvVvoCHaZ42xCP0"  # 替换为你的 API Key
BASE_URL = "https://s.lconai.com"

GEN_URL = f"{BASE_URL}/v1/images/generations"
EDIT_URL = f"{BASE_URL}/v1/images/edits"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
}

OUTPUT_DIR = "output"
PROMPT_FILE = "prompt.txt"


def _ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def _save_image(data, prefix="img"):
    """从 API 响应中保存图片，返回文件路径列表"""
    _ensure_output_dir()
    saved = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for i, item in enumerate(data):
        filename = f"{prefix}_{timestamp}_{i}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)

        if "b64_json" in item:
            img_bytes = base64.b64decode(item["b64_json"])
            with open(filepath, "wb") as f:
                f.write(img_bytes)
        elif "url" in item:
            resp = requests.get(item["url"], timeout=120)
            resp.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(resp.content)
        else:
            print(f"[警告] 第 {i} 张图片无法识别格式，跳过")
            continue

        saved.append(filepath)
        print(f"[保存] {filepath}")

    return saved


# ===================== 生图 =====================
def generate_image(
    prompt,
    size="1024x1024",
    n=1,
    quality="auto",
    response_format="b64_json",
):
    """
    文生图

    参数:
        prompt:          提示词
        size:            尺寸 (1024x1024 / 1536x1024 / 1024x1536 / auto)
        n:               生成数量
        quality:         质量 (auto / high / medium / low)
        response_format: 返回格式 (b64_json / url)
    """
    payload = {
        "model": "gpt-image-2",
        "prompt": prompt,
        "size": size,
        "n": n,
        "quality": quality,
        "response_format": response_format,
    }

    print(f"[生图] prompt: {prompt}")
    print(f"       size={size}, quality={quality}, n={n}")

    resp = requests.post(GEN_URL, headers=HEADERS, json=payload, timeout=300)
    resp.raise_for_status()
    result = resp.json()

    return _save_image(result["data"], prefix="gen")


# ===================== 改图 =====================
def edit_image(
    image_path,
    prompt,
    mask_path=None,
    size="1024x1024",
    n=1,
    quality="auto",
    response_format="b64_json",
):
    """
    图片编辑 (改图)

    参数:
        image_path:      原图路径
        prompt:          编辑提示词
        mask_path:       蒙版路径 (可选，透明区域为待编辑区域)
        size:            输出尺寸
        n:               生成数量
        quality:         质量
        response_format: 返回格式
    """
    files = {
        "image": ("image.png", open(image_path, "rb"), "image/png"),
    }
    if mask_path:
        files["mask"] = ("mask.png", open(mask_path, "rb"), "image/png")

    data = {
        "model": "gpt-image-2",
        "prompt": prompt,
        "size": size,
        "n": str(n),
        "quality": quality,
        "response_format": response_format,
    }

    print(f"[改图] image: {image_path}")
    if mask_path:
        print(f"       mask:  {mask_path}")
    print(f"       prompt: {prompt}")

    resp = requests.post(
        EDIT_URL, headers=HEADERS, files=files, data=data, timeout=300
    )
    resp.raise_for_status()
    result = resp.json()

    for f in files.values():
        f[1].close()

    return _save_image(result["data"], prefix="edit")


# ===================== 交互选项 =====================

SIZE_OPTIONS = ["1024x1024", "1536x1024", "1024x1536", "auto"]
QUALITY_OPTIONS = ["auto", "high", "medium", "low"]


def _pick(label, options, default=0):
    """交互式单选"""
    print(f"\n{label}")
    for i, opt in enumerate(options):
        marker = " (默认)" if i == default else ""
        print(f"  [{i}] {opt}{marker}")
    raw = input("请选择 (直接回车用默认): ").strip()
    if raw == "":
        return options[default]
    try:
        return options[int(raw)]
    except (ValueError, IndexError):
        print(f"  无效输入，使用默认: {options[default]}")
        return options[default]


def _read_prompt_file():
    """从 prompt.txt 读取提示词"""
    if not os.path.isfile(PROMPT_FILE):
        print(f"[错误] 找不到 {PROMPT_FILE}，请先创建该文件并写入提示词")
        return ""
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
    if not content or content == "在这里写你的提示词，保存后运行脚本即可。":
        print(f"[错误] {PROMPT_FILE} 为空或未修改，请先编辑该文件写入提示词")
        return ""
    print(f"[提示词] 已从 {PROMPT_FILE} 读取:\n{content}")
    return content



def _input_int(label, default=1):
    raw = input(f"{label} (默认 {default}): ").strip()
    if raw == "":
        return default
    try:
        return max(1, int(raw))
    except ValueError:
        return default


def interactive_generate():
    """交互式文生图"""
    print("\n===== 文生图 =====")
    prompt = _read_prompt_file()
    if not prompt:
        return
    size = _pick("尺寸", SIZE_OPTIONS, default=0)
    quality = _pick("质量", QUALITY_OPTIONS, default=0)
    n = _input_int("生成数量", default=1)

    generate_image(prompt=prompt, size=size, quality=quality, n=n)


def interactive_edit():
    """交互式改图"""
    print("\n===== 改图 =====")
    image_path = input("原图路径: ").strip()
    if not image_path or not os.path.isfile(image_path):
        print(f"文件不存在: {image_path}")
        return

    prompt = _read_prompt_file()
    if not prompt:
        return

    mask_input = input("蒙版路径 (可选，直接回车跳过): ").strip()
    mask_path = mask_input if mask_input and os.path.isfile(mask_input) else None

    size = _pick("输出尺寸", SIZE_OPTIONS, default=0)
    quality = _pick("质量", QUALITY_OPTIONS, default=0)
    n = _input_int("生成数量", default=1)

    edit_image(
        image_path=image_path,
        prompt=prompt,
        mask_path=mask_path,
        size=size,
        quality=quality,
        n=n,
    )


if __name__ == "__main__":
    while True:
        print("\n========== GPT-Image-2 ==========")
        print("  [1] 文生图")
        print("  [2] 改图")
        print("  [q] 退出")
        choice = input("请选择: ").strip().lower()

        if choice == "1":
            interactive_generate()
        elif choice == "2":
            interactive_edit()
        elif choice in ("q", "quit", "exit"):
            print("再见!")
            break
        else:
            print("无效选项，请重新选择")
