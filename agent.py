import os
from typing import Any

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession, JobContext
from livekit.plugins import google


load_dotenv()

if not os.getenv("GOOGLE_API_KEY"):
    raise RuntimeError("Thiếu GOOGLE_API_KEY trong file .env")


server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    session: AgentSession[None] = AgentSession(
        llm=google.realtime.RealtimeModel(
            model="gemini-2.5-flash-native-audio-preview-12-2025",
            voice="Puck",
            temperature=0.8,
            instructions=(
                "Bạn là trợ lý giọng nói thân thiện. Trả lời ngắn gọn, tự nhiên bằng tiếng Việt."
            ),
        )
    )

    start_session: Any = getattr(session, "start")
    await start_session(
        room=ctx.room,
        agent=Agent(
            instructions="Chào người dùng khi họ kết nối và mời họ bắt đầu trò chuyện bằng giọng nói."
        ),
        capture_run=False,
    )
    await session.generate_reply(
        instructions="Chào người dùng bằng một câu ngắn bằng tiếng Việt."
    )


if __name__ == "__main__":
    agents.cli.run_app(server)