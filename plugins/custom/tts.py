import httpx
import os
from dataclasses import dataclass
from typing import AsyncContextManager

from openai import AsyncClient, AsyncAPIResponse

from livekit.plugins import openai
from livekit.agents import tts, utils

from pyht import Client
from pyht.client import TTSOptions

from .utils import AsyncAzureADTokenProvider
from .log import logger

@dataclass
class _TTSOptions:
    model: str
    voice: str
    speed: float

OPENAI_TTS_SAMPLE_RATE = 24000
OPENAI_TTS_CHANNELS = 1

class TTS(openai.TTS):    
    
    @staticmethod
    def create_playht_client(
        *,
        api_key: str | None = None,
        user_id: str | None = None,
        voice: str = "s3://voice-cloning-zero-shot/d9ff78ba-d016-47f6-b0ef-dd630f59414e/female-cs/manifest.json",
        speed: float = 1.0,
        base_url: str | None = "https://api.play.ht/api/v2/tts/stream",
    ) -> openai.TTS:
        
        options = TTSOptions(voice=voice)
        
        user_id = user_id or os.environ.get("PLAYHT_USER_ID")
        if user_id is None:
            raise ValueError("PLAYHT_USER_ID is required")
        
        api_key = api_key or os.environ.get("PLAYHT_API_KEY")
        if api_key is None:
            raise ValueError("PLAYHT_API_KEY is required")
        
        client = Client(
            user_id=os.getenv("PLAYHT_USER_ID"),
            api_key=os.getenv("PLAYHT_API_KEY"),
        )
        
        return TTS(client=client, voice=voice, speed=speed) 
    
    def synthesize(self, text: str) -> "ChunkedStream":
        options = TTSOptions(voice=self._opts.voice)
        stream = self._client.tts(text, options)
        return ChunkedStream(stream, text, self._opts)


class ChunkedStream(tts.ChunkedStream):
    def __init__(
        self,
        oai_stream: AsyncContextManager[AsyncAPIResponse[bytes]],
        text: str,
        opts: _TTSOptions,
    ) -> None:
        super().__init__()
        self._opts, self._text = opts, text
        self._stream = oai_stream

    @utils.log_exceptions(logger=logger)
    async def _main_task(self):
        request_id = utils.shortuuid()
        segment_id = utils.shortuuid()
        
        decoder = utils.codecs.Mp3StreamDecoder()
        audio_bstream = utils.audio.AudioByteStream(
            sample_rate=OPENAI_TTS_SAMPLE_RATE,
            num_channels=OPENAI_TTS_CHANNELS,
        )
        for data_chunk in self._stream: 
            for frame in audio_bstream.write(data_chunk):
                # Directly send the synthesized audio frame data for each chunk
                self._event_ch.send_nowait(
                    tts.SynthesizedAudio(
                        request_id=request_id,
                        segment_id=segment_id,
                        frame=frame,
                    )
                )
        
        for frame in audio_bstream.flush():
            self._event_ch.send_nowait(
                tts.SynthesizedAudio(
                    request_id=request_id, segment_id=segment_id, frame=frame
                )
            )
