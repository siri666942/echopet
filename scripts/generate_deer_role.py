from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QImage, QPainter


ROOT = Path(r"c:\Users\thyss\Documents\GitHub\echopet")
SHEET_PATH = ROOT / "THEDEER.png"
ROLE_ROOT = ROOT / "DyberPet-main" / "res" / "role" / "EchoDeer"
ACTION_DIR = ROLE_ROOT / "action"
CANVAS_WIDTH = 148
CANVAS_HEIGHT = 128
SHEET_FRAME_COUNT = 5
BACKGROUND_THRESHOLD = 36


def ensure_dirs() -> None:
    ACTION_DIR.mkdir(parents=True, exist_ok=True)
    for path in ACTION_DIR.glob("stand_*.png"):
        path.unlink()


def color_distance(a: QColor, b: QColor) -> int:
    return abs(a.red() - b.red()) + abs(a.green() - b.green()) + abs(a.blue() - b.blue())


def remove_background(image: QImage) -> QImage:
    image = image.convertToFormat(QImage.Format_ARGB32)
    bg = QColor(image.pixel(0, 0))
    for y in range(image.height()):
        for x in range(image.width()):
            color = QColor(image.pixel(x, y))
            if color_distance(color, bg) <= BACKGROUND_THRESHOLD:
                image.setPixelColor(x, y, QColor(0, 0, 0, 0))
    return image


def retain_largest_component(image: QImage) -> QImage:
    width = image.width()
    height = image.height()
    visited: set[tuple[int, int]] = set()
    largest: list[tuple[int, int]] = []

    for y in range(height):
        for x in range(width):
            if (x, y) in visited:
                continue
            if image.pixelColor(x, y).alpha() == 0:
                visited.add((x, y))
                continue

            stack = [(x, y)]
            component: list[tuple[int, int]] = []
            visited.add((x, y))
            while stack:
                cx, cy = stack.pop()
                component.append((cx, cy))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in visited:
                        if image.pixelColor(nx, ny).alpha() > 0:
                            visited.add((nx, ny))
                            stack.append((nx, ny))
                        else:
                            visited.add((nx, ny))

            if len(component) > len(largest):
                largest = component

    if not largest:
        return image

    keep = set(largest)
    result = QImage(width, height, QImage.Format_ARGB32)
    result.fill(Qt.transparent)
    for x, y in keep:
        result.setPixelColor(x, y, image.pixelColor(x, y))
    return result


def bounding_box(image: QImage) -> QRect:
    min_x = image.width()
    min_y = image.height()
    max_x = -1
    max_y = -1
    for y in range(image.height()):
        for x in range(image.width()):
            if QColor(image.pixelColor(x, y)).alpha() > 0:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
    if max_x < min_x or max_y < min_y:
        return QRect(0, 0, image.width(), image.height())
    return QRect(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)


def fit_to_canvas(
    image: QImage,
    canvas_width: int = CANVAS_WIDTH,
    canvas_height: int = CANVAS_HEIGHT,
    scale: float = 1.0,
    reference_width: int | None = None,
    reference_height: int | None = None,
) -> QImage:
    bounds = bounding_box(image)
    cropped = image.copy(bounds)
    source_width = max(1, reference_width or cropped.width())
    source_height = max(1, reference_height or cropped.height())
    ratio = min((canvas_width * scale) / source_width, (canvas_height * scale) / source_height)
    scaled_width = max(1, round(cropped.width() * ratio))
    scaled_height = max(1, round(cropped.height() * ratio))
    scaled = cropped.scaled(scaled_width, scaled_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    canvas = QImage(canvas_width, canvas_height, QImage.Format_ARGB32)
    canvas.fill(Qt.transparent)
    painter = QPainter(canvas)
    x = (canvas_width - scaled.width()) // 2
    y = canvas_height - scaled.height() - 4
    painter.drawImage(x, y, scaled)
    painter.end()
    return canvas


def find_character_ranges(image: QImage) -> list[tuple[int, int]]:
    counts = []
    for x in range(image.width()):
        opaque = 0
        for y in range(image.height()):
            if image.pixelColor(x, y).alpha() > 0:
                opaque += 1
        counts.append(opaque)

    ranges: list[tuple[int, int]] = []
    start = None
    threshold = 22
    for x, count in enumerate(counts):
        if count >= threshold and start is None:
            start = x
        elif count < threshold and start is not None:
            ranges.append((start, x - 1))
            start = None
    if start is not None:
        ranges.append((start, len(counts) - 1))

    if len(ranges) != SHEET_FRAME_COUNT:
        step = image.width() // SHEET_FRAME_COUNT
        ranges = [(i * step, (i + 1) * step - 1) for i in range(SHEET_FRAME_COUNT)]

    expanded = []
    for left, right in ranges:
        expanded.append((max(0, left - 18), min(image.width() - 1, right + 18)))
    return expanded


def extract_frames() -> list[QImage]:
    sheet = QImage(str(SHEET_PATH))
    if sheet.isNull():
        raise RuntimeError(f"Failed to read {SHEET_PATH}")
    cleaned_sheet = remove_background(sheet)
    ranges = find_character_ranges(cleaned_sheet)

    frames: list[QImage] = []
    for left, right in ranges:
        rect = QRect(left, 0, right - left + 1, cleaned_sheet.height())
        segment = cleaned_sheet.copy(rect)
        segment = retain_largest_component(segment)
        frames.append(segment)
    return frames


def normalize_frames(images: list[QImage]) -> list[QImage]:
    bounds = [bounding_box(image) for image in images]
    reference_width = max(bound.width() for bound in bounds)
    reference_height = max(bound.height() for bound in bounds)
    return [
        fit_to_canvas(
            image,
            reference_width=reference_width,
            reference_height=reference_height,
        )
        for image in images
    ]


def transform_frame(image: QImage, rotation: float = 0.0, x_scale: float = 1.0, y_scale: float = 1.0) -> QImage:
    work = QImage(CANVAS_WIDTH, CANVAS_HEIGHT, QImage.Format_ARGB32)
    work.fill(Qt.transparent)

    painter = QPainter(work)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    painter.translate(CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2)
    painter.rotate(rotation)
    painter.scale(x_scale, y_scale)
    painter.translate(-image.width() / 2, -image.height() / 2)
    painter.drawImage(0, 0, image)
    painter.end()
    return work


def offset_frame(image: QImage, dx: int = 0, dy: int = 0) -> QImage:
    work = QImage(CANVAS_WIDTH, CANVAS_HEIGHT, QImage.Format_ARGB32)
    work.fill(Qt.transparent)
    painter = QPainter(work)
    painter.drawImage(dx, dy, image)
    painter.end()
    return work


def wag_tail(image: QImage, dx: int = 0, dy: int = 0) -> QImage:
    # Only nudge the tail tip, never the root connected to the body.
    tip_rect = QRect(118, 60, 16, 18)
    tip = image.copy(tip_rect)
    result = image.copy()
    painter = QPainter(result)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    painter.setOpacity(0.45)
    painter.drawImage(tip_rect.x() + dx, tip_rect.y() + dy, tip)
    painter.end()
    return result


def save_image(image: QImage, name: str) -> None:
    image.save(str(ACTION_DIR / name))


def write_role_config() -> None:
    pet_conf = {
        "width": CANVAS_WIDTH,
        "height": CANVAS_HEIGHT,
        "scale": 1.0,
        "refresh": 5,
        "interact_speed": 0.02,
        "default": "default",
        "up": "up",
        "down": "down",
        "left": "left",
        "right": "right",
        "drag": "drag",
        "fall": "fall",
        "on_floor": "onfloor",
        "random_act": [
            {"name": "站立", "act_list": ["default"], "act_prob": 1.0, "act_type": [2, 0]},
            {"name": "onfloor", "act_list": ["onfloor"], "act_prob": 0, "act_type": [0, 10000]},
        ],
    }
    act_conf = {
        "default": {"images": "stand", "act_num": 3, "frame_refresh": 0.38},
        "up": {"images": "stand", "act_num": 3, "frame_refresh": 0.38},
        "down": {"images": "stand", "act_num": 3, "frame_refresh": 0.38},
        "left": {"images": "stand", "act_num": 3, "frame_refresh": 0.38},
        "right": {"images": "stand", "act_num": 3, "frame_refresh": 0.38},
        "drag": {"images": "drag", "act_num": 1},
        "fall": {"images": "fall", "act_num": 1},
        "onfloor": {"images": "onfloor", "act_num": 1, "frame_refresh": 0.08},
    }
    (ROLE_ROOT / "pet_conf.json").write_text(json.dumps(pet_conf, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROLE_ROOT / "act_conf.json").write_text(json.dumps(act_conf, ensure_ascii=False, indent=2), encoding="utf-8")


def update_settings() -> None:
    settings_path = ROOT / "DyberPet-main" / "data" / "settings.json"
    data = json.loads(settings_path.read_text(encoding="utf-8"))
    data.setdefault("usertag_dict", {})["EchoDeer"] = ""
    data.setdefault("scale_dict", {})["EchoDeer"] = 1.0
    data.setdefault("defaultAct", {})["EchoDeer"] = None
    data["default_pet"] = "EchoDeer"
    settings_path.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    raw_frames = normalize_frames(extract_frames())
    base_frame = raw_frames[0]
    selected_frames = [
        wag_tail(transform_frame(base_frame, rotation=-0.6, x_scale=1.0, y_scale=1.0), dx=-1),
        wag_tail(offset_frame(base_frame, dy=-1), dx=0),
        wag_tail(transform_frame(base_frame, rotation=0.6, x_scale=1.0, y_scale=1.0), dx=1),
    ]
    for index, frame in enumerate(selected_frames):
        save_image(frame, f"stand_{index}.png")

    drag = transform_frame(selected_frames[1], rotation=-8.0, x_scale=1.03, y_scale=0.98)
    fall = transform_frame(selected_frames[2], rotation=68.0, x_scale=1.03, y_scale=0.96)
    onfloor = transform_frame(selected_frames[2], rotation=90.0, x_scale=1.03, y_scale=0.92)

    save_image(drag, "drag_0.png")
    save_image(fall, "fall_0.png")
    save_image(onfloor, "onfloor_0.png")

    write_role_config()
    update_settings()
    print(f"EchoDeer role generated in: {ROLE_ROOT}")


if __name__ == "__main__":
    main()
