"""把用户上下文翻译成音乐检索意图。"""

import json

from backend.config import settings
from backend.models.schemas import ContextModel, EmotionResult


SYSTEM_PROMPT = """你把用户文本、环境上下文、键盘状态弱信号翻译成音乐检索语言。
键盘状态只代表打字节奏、专注、压力、疲劳和稳定性，不是情绪识别器；不要根据键盘状态硬判“愤怒/难过/开心”。
只输出 JSON：
{
  "retrieval_query": "中等能量、节奏稳定、有支撑感、不吵、不太悲伤的器乐音乐",
  "current_state": "idle|focus|focused_stressed|tired|frustrated|sad",
  "bubble_text": "短句",
  "assistant_reply": "短句",
  "emotion_compat": {"emotion":"frustrated|sad|happy|focused|tired|anxious|calm","energy":0.0,"need":"comfort|focus|energy|relaxation|companionship"}
}
retrieval_query 只能描述音乐特征，不要写隐私、故事或“适合某人”。"""

PRODUCTIVE_APP_KEYWORDS = (
    "code",
    "cursor",
    "vscode",
    "visual studio",
    "pycharm",
    "idea",
    "terminal",
    "powershell",
    "windows terminal",
    "notion",
    "obsidian",
)


async def build_music_intent(
    text: str,
    context: ContextModel,
    keyboard_state: dict | None,
    user_profile: dict,
) -> dict:
    if settings.openai_api_key:
        try:
            return _build_with_llm(text, context, keyboard_state, user_profile)
        except Exception:
            pass
    return _fallback_intent(text, context, keyboard_state)


def _build_with_llm(
    text: str,
    context: ContextModel,
    keyboard_state: dict | None,
    user_profile: dict,
) -> dict:
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "text": text,
                        "context": context.model_dump(),
                        "keyboard_state": keyboard_state or {},
                        "user_profile": user_profile,
                    },
                    ensure_ascii=False,
                ),
            },
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    payload = json.loads(response.choices[0].message.content or "{}")
    payload["emotion_compat"] = EmotionResult(**payload["emotion_compat"]).model_dump()
    return payload


def _fallback_intent(text: str, context: ContextModel, keyboard_state: dict | None = None) -> dict:
    lowered = text.lower()
    keyboard_state = keyboard_state or {}
    active_app = (context.active_app or "").lower()
    typing_state = keyboard_state.get("typing_state", "")
    focus_score = float(keyboard_state.get("focus", 0.0) or 0.0)
    stress_score = float(keyboard_state.get("stress", 0.0) or 0.0)
    fatigue_score = float(keyboard_state.get("fatigue", 0.0) or 0.0)
    stable_focus = typing_state in {"focused_typing", "steady_typing"} or (
        focus_score >= 0.68 and stress_score < 0.6
    )
    productive_app = any(keyword in active_app for keyword in PRODUCTIVE_APP_KEYWORDS)

    if any(word in lowered for word in ["难过", "伤心", "失落", "低落", "想哭"]):
        return {
            "retrieval_query": "低到中低能量、温柔、包裹感强、不压迫、带一点陪伴感的音乐",
            "current_state": "sad",
            "bubble_text": "我先陪你待一会儿。",
            "assistant_reply": "我先给你放一首温柔一点、不会打扰你的。",
            "emotion_compat": {"emotion": "sad", "energy": 0.22, "need": "companionship"},
        }
    if (
        focus_score >= 0.7
        and stress_score >= 0.6
        and not any(word in lowered for word in ["烦", "崩", "debug", "bug", "红温"])
    ):
        return {
            "retrieval_query": "中等能量、节奏稳定、有支撑感、不吵、不太悲伤、适合高强度专注输出的器乐音乐",
            "current_state": "focused_stressed",
            "bubble_text": "你现在像是在高强度输出，我先放点稳住节奏的。",
            "assistant_reply": "我给你切一首有支撑感但不打扰的。",
            "emotion_compat": {"emotion": "focused", "energy": 0.55, "need": "focus"},
        }
    if any(word in lowered for word in ["烦", "崩", "debug", "bug", "红温"]):
        return {
            "retrieval_query": "中等偏低能量、节奏稳定、有支撑感、不吵、不太悲伤的器乐音乐",
            "current_state": "frustrated",
            "bubble_text": "你现在有点紧，我先放点稳一点的。",
            "assistant_reply": "我先给你选一首稳一点、有支撑感的。",
            "emotion_compat": {"emotion": "frustrated", "energy": 0.45, "need": "comfort"},
        }
    if any(word in lowered for word in ["专注", "学习", "写代码", "focus"]):
        return {
            "retrieval_query": "中等能量、节奏稳定、重复感清晰、干扰少、适合保持持续注意力的器乐音乐",
            "current_state": "focus",
            "bubble_text": "来点稳稳的节奏。",
            "assistant_reply": "我给你选一首不抢注意力、能托住节奏的。",
            "emotion_compat": {"emotion": "focused", "energy": 0.55, "need": "focus"},
        }
    if (
        fatigue_score >= 0.65
        or typing_state == "fatigued_typing"
        or context.hour >= 23
        or context.hour <= 5
        or any(word in lowered for word in ["累", "困", "疲惫", "熬夜"])
    ):
        return {
            "retrieval_query": "低能量、慢速、响度柔和、频谱不刺耳、整体平稳的音乐",
            "current_state": "tired",
            "bubble_text": "先放轻一点。",
            "assistant_reply": "我先给你放一首轻一点的。",
            "emotion_compat": {"emotion": "tired", "energy": 0.3, "need": "relaxation"},
        }
    if stable_focus and productive_app:
        return {
            "retrieval_query": "中等能量、节奏稳定、重复感清晰、干扰少、适合保持持续注意力的器乐音乐",
            "current_state": "focus",
            "bubble_text": "你已经进状态了，我帮你继续稳住节奏。",
            "assistant_reply": "我给你接一首不抢注意力、适合持续输出的。",
            "emotion_compat": {"emotion": "focused", "energy": 0.58, "need": "focus"},
        }
    if stress_score >= 0.62 or context.backspace_ratio >= 0.18:
        return {
            "retrieval_query": "中低能量、节奏稳定、收敛感强、不过分压抑的器乐音乐",
            "current_state": "frustrated",
            "bubble_text": "你现在有点绷，我先帮你稳一下。",
            "assistant_reply": "我给你放一首更稳一点的，先把节奏拉回来。",
            "emotion_compat": {"emotion": "anxious", "energy": 0.4, "need": "comfort"},
        }
    return {
        "retrieval_query": "中等能量、节奏稳定、响度中等、频谱均衡、整体平稳的音乐",
        "current_state": "idle",
        "bubble_text": "我来选一首。",
        "assistant_reply": "我先给你选一首平稳一点的。",
        "emotion_compat": {"emotion": "calm", "energy": 0.5, "need": "companionship"},
    }
