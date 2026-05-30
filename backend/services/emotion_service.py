"""情绪分析服务。

这个文件负责把：

    用户文本 + 当前环境

变成：

    emotion / energy / need

也就是：
    - emotion: 用户是什么情绪
    - energy: 当前能量高低
    - need: 用户现在最需要什么

实现策略：

1. 如果 `.env` 里配置了 OPENAI_API_KEY：
   - 优先调用 OpenAI。

2. 如果没有 Key，或者 OpenAI 调用失败：
   - 使用本地关键词规则兜底。

为什么要兜底：
    黑客松和本地开发最怕外部依赖卡住。
    就算没有 Key，这套后端也要能让前端完整联调。
"""

import json

from backend.config import settings
from backend.models.schemas import ContextModel, EmotionResult


# 这是给 OpenAI 的系统提示词。
# 要求模型只返回 JSON，字段必须符合接口约定。
SYSTEM_PROMPT = """You analyze the user's mood from text and context.
Return strict JSON with fields emotion, energy, need.
emotion must be one of frustrated, sad, happy, focused, tired, anxious, calm.
need must be one of comfort, focus, energy, relaxation, companionship."""


async def analyze_emotion(text: str, context: ContextModel) -> EmotionResult:
    """分析情绪的统一入口。

    参数：
        text:
            用户输入文本。

        context:
            当前环境上下文。

    返回：
        EmotionResult。

    调用链：
        `/api/analyze`
            -> emotion_service.analyze_emotion
                -> _analyze_with_openai 或 _heuristic_emotion
    """

    # 有 OpenAI Key 才尝试调用远程模型。
    if settings.openai_api_key:
        try:
            return await _analyze_with_openai(text, context)
        except Exception:
            # 不把异常抛出去。
            # 原因：情绪分析失败时，前端仍然应该能拿到一个兜底推荐。
            pass

    # 没 Key 或调用失败，就走本地规则。
    return _heuristic_emotion(text, context)


async def _analyze_with_openai(text: str, context: ContextModel) -> EmotionResult:
    """调用 OpenAI 做情绪分析。

    这是“更智能”的路径，但依赖网络和 API Key。

    注意：
        这个函数里用的是同步 OpenAI client。
        当前请求量很小，MVP 可以接受。
        后续高并发时可以改成异步客户端或放到线程池。
    """

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Text: {text}\n"
                    f"Hour: {context.hour}\n"
                    f"Active app: {context.active_app}\n"
                    f"KPM: {context.kpm}\n"
                    f"Backspace ratio: {context.backspace_ratio}"
                ),
            },
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )

    # OpenAI 返回的是字符串 JSON，这里解析成 dict。
    payload = json.loads(response.choices[0].message.content or "{}")

    # 再交给 EmotionResult 校验，确保字段和枚举值合法。
    return EmotionResult(**payload)


def _heuristic_emotion(text: str, context: ContextModel) -> EmotionResult:
    """本地关键词兜底情绪分析。

    这个函数不追求完美，只追求：
        - 稳定
        - 不依赖网络
        - 够前端演示

    规则从上到下匹配，先命中哪个就返回哪个。
    """

    lowered = text.lower()

    # Debug、bug、烦、崩：认为用户挫败，需要安抚。
    if any(word in lowered for word in ["烦", "崩", "debug", "bug", "红温", "frustrated"]):
        return EmotionResult(emotion="frustrated", energy=0.3, need="comfort")

    # 难过、低落、孤独：认为用户 sad，需要陪伴。
    if any(word in lowered for word in ["难过", "低落", "孤独", "失恋", "sad"]):
        return EmotionResult(emotion="sad", energy=0.2, need="companionship")

    # 累、困、熬夜：认为用户 tired，需要放松。
    if any(word in lowered for word in ["累", "困", "熬夜", "tired"]):
        return EmotionResult(emotion="tired", energy=0.25, need="relaxation")

    # 焦虑、紧张：认为用户 anxious，需要安抚。
    if any(word in lowered for word in ["焦虑", "紧张", "anxious"]):
        return EmotionResult(emotion="anxious", energy=0.35, need="comfort")

    # 开心：认为用户能量比较高。
    if any(word in lowered for word in ["开心", "高兴", "happy"]):
        return EmotionResult(emotion="happy", energy=0.75, need="energy")

    # 专注、学习、写代码：认为用户想进入 focus。
    if any(word in lowered for word in ["专注", "学习", "写代码", "focus"]):
        return EmotionResult(emotion="focused", energy=0.55, need="focus")

    # 深夜兜底：即使用户没说累，深夜也偏 tired。
    if context.hour >= 23 or context.hour <= 5:
        return EmotionResult(emotion="tired", energy=0.3, need="relaxation")

    # 默认：平静，需要陪伴。
    return EmotionResult(emotion="calm", energy=0.5, need="companionship")
