import asyncio
import logging
import os
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import deepgram, openai, silero
from plugins import custom

load_dotenv()

logger = logging.getLogger("voice-assistant")


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
 
agents = {}

async def entrypoint(ctx: JobContext):
    global agents

    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are a voice assistant created by LiveKit. Your interface with users will be voice. "
            "You should use short and concise responses,nected and avoiding usage of unpronouncable punctuation."
        ),
    )

    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)

    # wait for the first participant to connect
    participant = await ctx.wait_for_participant()
    logger.info(f"starting voice assistant for participant {participant.identity}")

    dg_model = "nova-2-general"
    if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
        # use a model optimized for telephony
        dg_model = "nova-2-phonecall"
    
    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=openai.STT(),
        llm=custom.LLM.with_groq(),
        tts=custom.TTS.create_playht_client(),
        chat_ctx=initial_ctx
    )

    def on_save_transcriptions(data: llm.ChatMessage): 
        # You can save the transcription in here.
        # requests.post(url, body)
        print(participant.identity)
        print(data.role, data.content) 


    agent.on("agent_speech_committed", on_save_transcriptions)
    agent.on("user_speech_committed", on_save_transcriptions)

    agent.start(ctx.room, participant)

    # listen to incoming chat messages, only required if you'd like the agent to
    # answer incoming messages from Chat
    chat = rtc.ChatManager(ctx.room) 
    @ctx.room.on("data_received")
    def on_data_received(data:rtc.DataPacket):
        if data.topic == "role":
            prompt = data.data.decode()
            logger.info(f"instruction changed -- {prompt}") 
            agent.chat_ctx.append(role="system", text=prompt)

    async def answer_from_text(txt: str):
        chat_ctx = agent.chat_ctx.copy()
        chat_ctx.append(role="user", text=txt)
        stream = agent.llm.chat(chat_ctx=chat_ctx)
        await agent.say(stream) 

    @chat.on("message_received")
    def on_chat_received(msg: rtc.ChatMessage):
        if msg.message:
            asyncio.create_task(answer_from_text(msg.message))

    await agent.say("Hey, how can I help you today?", allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm, host="0.0.0.0", port=8080))