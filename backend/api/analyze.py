"""`POST /api/analyze` 核心接口。

这是后端最重要的一条链路。

前端把用户文本和当前环境上下文发过来，这个接口会按顺序做：

1. 情绪分析
   - 调 `emotion_service.analyze_emotion`
   - 得到 emotion / energy / need

2. 歌曲推荐
   - 调 `recommender.recommend`
   - 根据情绪、能量值、历史记忆，从 songs 表里挑一首歌

3. 记忆保存
   - 调 `save_memory`
   - 把这次“环境 + 情绪 + 推荐歌曲”存到 memory 表

4. 播放音乐
   - 调 `player_service.play`
   - 如果 mpv 可用，就尝试播放
   - 如果 mpv 不可用，不让接口崩，只返回 error/idle 这类状态

5. 组装前端需要的响应
   - 桌宠状态 current_state
   - 气泡文案 bubble_text
   - 推荐歌曲 recommendation
   - 播放器状态 player_status
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.models.schemas import AnalyzeRequest, AnalyzeResponse, EmotionResult
from backend.services import emotion_service, player_service, recommender
from backend.services.memory_service import save_memory
from backend.services.serialization import song_to_response


# prefix="/api" 表示这个文件里的接口都以 /api 开头。
# tags=["analyze"] 只是给 Swagger 分组用，方便在 /docs 页面里看。
router = APIRouter(prefix="/api", tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest, db: Session = Depends(get_db)) -> AnalyzeResponse:
    """分析用户文本并返回推荐结果。

    参数：
        req:
            FastAPI 会自动把请求 JSON 解析成 AnalyzeRequest。
            它里面有：
            - text: 用户说的话，比如“我 debug 一天了，有点烦”
            - input_source: 输入来源，text 或 faster_whisper
            - context: 当前上下文，比如时间、活跃软件、打字速度

        db:
            数据库会话。
            `Depends(get_db)` 的意思是：
            “这个参数由 FastAPI 自动调用 get_db() 生成，不需要前端传。”

    返回：
        AnalyzeResponse。
        这是前端 DyberPet 最需要的一包数据：
        - 情绪
        - 桌宠状态
        - 气泡文案
        - 推荐歌曲
        - 播放状态
    """

    # 1. 先判断用户现在是什么情绪。
    # 如果 .env 里有 OPENAI_API_KEY，会尝试调用 OpenAI。
    # 如果没有 key 或调用失败，会使用本地关键词规则兜底。
    emotion = await emotion_service.analyze_emotion(req.text, req.context)

    # 2. 根据情绪和上下文挑一首歌。
    # recommender 会同时看：
    # - 当前 emotion.energy
    # - 当前 context.hour / active_app
    # - 历史 positive 反馈
    song = recommender.recommend(db, emotion, req.context)

    # 理论上启动时会插入样例歌曲，所以一般不会为空。
    # 但如果数据库被手动清空，就返回 404，告诉前端“曲库为空”。
    if song is None:
        raise HTTPException(status_code=404, detail="Music library is empty")

    # 3. 保存记忆。
    # 注意：这里 feedback 先是 None，因为用户还没点喜欢/不喜欢。
    # 后面用户点反馈时，POST /api/feedback 会更新这条 memory。
    save_memory(db, req.context, emotion, song.id)

    # 4. 尝试播放。
    # 参数解释：
    # - song.file_path: 本地音乐路径，mpv 要靠它找到文件
    # - song.id/title/artist: 后端自己维护当前播放状态时要展示这些信息
    player_status = player_service.play(song.file_path, song.id, song.title, song.artist)

    # 5. 把内部对象转换成接口响应。
    # song 是数据库 ORM 对象，不能直接丢给前端；
    # song_to_response 会把 tags 从 JSON 字符串转成 list[str]。
    return AnalyzeResponse(
        transcript=req.text.strip(),
        emotion=emotion,
        current_state=_map_emotion_to_state(emotion),
        bubble_text=_bubble_text(emotion),
        assistant_reply=_assistant_reply(emotion, song.title),
        recommendation=song_to_response(song),
        play_action="play",
        player_status=player_status,
    )


def _map_emotion_to_state(emotion: EmotionResult) -> str:
    """把“后端情绪”映射成“前端桌宠状态”。

    为什么需要映射：
        后端情绪比较细，比如 anxious、happy、calm。
        前端动画资源可能没这么多，只支持 idle/focus/tired/frustrated/sad。

    参数：
        emotion:
            情绪分析结果，里面的 `emotion.emotion` 是字符串标签。

    返回：
        前端可直接使用的桌宠状态名。
    """

    mapping = {
        "frustrated": "frustrated",
        "sad": "sad",
        "tired": "tired",
        "anxious": "frustrated",
        "focused": "focus",
        "happy": "focus",
        "calm": "idle",
    }
    return mapping.get(emotion.emotion, "idle")


def _bubble_text(emotion: EmotionResult) -> str:
    """根据用户需求生成桌宠气泡文案。

    `emotion.need` 表示用户现在最需要什么：
    - comfort: 安抚
    - focus: 专注
    - energy: 补能量
    - relaxation: 放松
    - companionship: 陪伴

    这里先用固定模板，避免每次生成气泡都调用 LLM。
    """

    templates = {
        "comfort": "你现在有点紧绷，我先放一点柔和的。",
        "focus": "来点专注的音乐吧。",
        "energy": "给你加点能量。",
        "relaxation": "先放松一下，听点轻一点的。",
        "companionship": "我在这儿，先陪你听一首。",
    }
    return templates.get(emotion.need, "我来给你选首歌。")


def _assistant_reply(emotion: EmotionResult, title: str) -> str:
    """生成一段更完整的后端回复。

    参数：
        emotion:
            情绪分析结果。

        title:
            推荐歌曲标题。

    返回：
        一句给用户看的中文回复。
    """

    need_labels = {
        "comfort": "被安抚",
        "focus": "进入专注",
        "energy": "补一点能量",
        "relaxation": "放松下来",
        "companionship": "有人陪着",
    }
    need = need_labels.get(emotion.need, emotion.need)
    return f"我感觉你现在需要{need}，先给你放 {title}。"
