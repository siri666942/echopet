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
    if (
        keyboard_state.get("focus", 0.0) >= 0.7
        and keyboard_state.get("stress", 0.0) >= 0.6
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
    if context.hour >= 23 or context.hour <= 5 or any(word in lowered for word in ["累", "困"]):
        return {
            "retrieval_query": "低能量、慢速、响度柔和、频谱不刺耳、整体平稳的音乐",
            "current_state": "tired",
            "bubble_text": "先放轻一点。",
            "assistant_reply": "我先给你放一首轻一点的。",
            "emotion_compat": {"emotion": "tired", "energy": 0.3, "need": "relaxation"},
        }
    return {
        "retrieval_query": "中等能量、节奏稳定、响度中等、频谱均衡、整体平稳的音乐",
        "current_state": "idle",
        "bubble_text": "我来选一首。",
        "assistant_reply": "我先给你选一首平稳一点的。",
        "emotion_compat": {"emotion": "calm", "energy": 0.5, "need": "companionship"},
    }
