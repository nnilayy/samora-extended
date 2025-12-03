#
# Samora AI Demo - Voice Pipeline with Hold/Wake Feature
# A voice AI agent using Pipecat with intelligent hold detection
# Deployed to Pipecat Cloud
#

import os
import re
from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import LLMRunFrame, TTSSpeakFrame, TranscriptionFrame, Frame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.processors.frameworks.rtvi import RTVIProcessor, RTVIObserver
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.elevenlabs.stt import ElevenLabsRealtimeSTTService
from pipecat.services.llm_service import FunctionCallParams
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
# from pipecat.services.openai.llm import OpenAILLMService
# from pipecat.services.groq.llm import GroqLLMService
from pipecat.services.cerebras.llm import CerebrasLLMService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.daily.transport import DailyParams
from pipecat.transports.websocket.fastapi import FastAPIWebsocketParams


# ============ HOLD/WAKE PROCESSOR ============
# Custom processor that filters transcriptions when on hold
# and detects wake phrases to resume the conversation

class HoldWakeProcessor(FrameProcessor):
    """Processor that implements hold/wake functionality.
    
    When on hold:
    - Filters out most transcriptions
    - Only passes through transcriptions containing wake phrases
    - When wake phrase detected, resumes normal operation
    """
    
    WAKE_PHRASES = [
        "hey samora",
        "hi samora",
        "samora",
        "hey there",
        "are you there",
        "you there",
        "i'm back",
        "i'm ready",
        "okay i'm done",
        "let's continue",
        "come back",
        "resume",
        "hello",
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_on_hold = False
        self._wake_patterns = [
            re.compile(r'\b' + re.escape(phrase) + r'\b', re.IGNORECASE)
            for phrase in self.WAKE_PHRASES
        ]
    
    def set_hold(self, on_hold: bool):
        """Set the hold state."""
        self.is_on_hold = on_hold
        if on_hold:
            logger.info("🔇 Hold mode ACTIVATED - waiting for wake phrase")
        else:
            logger.info("🔊 Hold mode DEACTIVATED - resuming conversation")
    
    def _contains_wake_phrase(self, text: str) -> bool:
        """Check if text contains any wake phrase."""
        for pattern in self._wake_patterns:
            if pattern.search(text):
                return True
        return False
    
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """Process frames, filtering transcriptions when on hold."""
        await super().process_frame(frame, direction)
        
        # If not on hold, pass everything through
        if not self.is_on_hold:
            await self.push_frame(frame, direction)
            return
        
        # When on hold, check transcriptions for wake phrases
        if isinstance(frame, TranscriptionFrame):
            text = frame.text
            logger.debug(f"🔇 On hold - received transcription: '{text}'")
            
            if self._contains_wake_phrase(text):
                logger.info(f"👋 Wake phrase detected: '{text}'")
                self.is_on_hold = False
                # Pass the frame through so LLM can respond
                await self.push_frame(frame, direction)
            else:
                # Silently drop the transcription
                logger.debug(f"🔇 Dropping transcription (on hold): '{text}'")
        else:
            # Pass through non-transcription frames
            await self.push_frame(frame, direction)

load_dotenv(override=True)

# Transport configuration for different connection types
transport_params = {
    "daily": lambda: DailyParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.3)),
    ),
    "webrtc": lambda: TransportParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.3)),
    ),
    "twilio": lambda: FastAPIWebsocketParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        add_wav_header=False,
        vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.3)),
    ),
}


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    logger.info("Starting Samora AI bot with Hold/Wake feature...")

    # Speech-to-Text: ElevenLabs Scribe v2 Realtime (better multilingual support)
    stt = ElevenLabsRealtimeSTTService(
        api_key=os.getenv("ELEVENLABS_API_KEY", ""),
        model= "scribe_v2_realtime"
        # language_code left as None for auto-detection,
    )
    
    # Speech-to-Text: Deepgram (commented out)
    # stt = DeepgramSTTService(
    #     api_key=os.getenv("DEEPGRAM_API_KEY", ""),
    # )

    # Text-to-Speech: Cartesia
    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY", ""),
        voice_id="11af83e2-23eb-452f-956e-7fee218ccb5c",  # British Reading Lady
    )

    # Hold/Wake processor - manages hold state and wake phrase detection
    hold_wake_processor = HoldWakeProcessor()

    # RTVI processor - enables messages to show in Pipecat Playground
    rtvi = RTVIProcessor()

    # ============ LLM OPTIONS ============
    # Uncomment the one you want to use

    # Option 1: OpenAI GPT-4 (commented out)
    # llm = OpenAILLMService(
    #     api_key=os.getenv("OPENAI_API_KEY", ""),
    #     model="gpt-4o-mini",
    # )

    # Option 2: Cerebras (ACTIVE - ultra fast inference!)
    llm = CerebrasLLMService(
        api_key=os.getenv("CEREBRAS_API_KEY", ""),
        model="gpt-oss-120b",
    )

    # Option 3: Groq (commented out)
    # llm = GroqLLMService(
    #     api_key=os.getenv("GROQ_API_KEY", ""),
    #     model="openai/gpt-oss-120b",  # Also: llama-3.1-8b-instant, mixtral-8x7b-32768
    # )

    # ============ HOLD FUNCTION ============
    # This function is called by the LLM when user wants to put the call on hold
    
    async def put_on_hold(params: FunctionCallParams):
        """Put the conversation on hold. User can say 'hey samora' to resume."""
        logger.info("🔇 Putting conversation on HOLD")
        hold_wake_processor.set_hold(True)
        
        # Acknowledge and inform user how to resume
        await params.llm.push_frame(
            TTSSpeakFrame("No problem! I'll wait right here. Just say 'Hey Samora' or 'I'm back' when you're ready to continue.")
        )
        
        # Return result to LLM
        await params.result_callback({
            "status": "on_hold",
            "message": "Conversation is now on hold. Waiting for wake phrase."
        })
    
    # ============ END CALL FUNCTION ============
    # This function is called by the LLM when user wants to end the call gracefully
    
    async def end_call(params: FunctionCallParams):
        """End the call gracefully after saying goodbye."""
        logger.info("👋 Ending call gracefully")
        
        # Speak farewell message
        await params.llm.push_frame(
            TTSSpeakFrame("It was great talking with you! Feel free to reach out anytime. Take care!")
        )
        
        # Return result to LLM
        await params.result_callback({
            "status": "call_ended",
            "message": "Call ending gracefully."
        })
        
        # Gracefully stop the pipeline after TTS finishes
        await task.stop_when_done()
    
    # Define the hold function schema for LLM
    hold_function = FunctionSchema(
        name="put_on_hold",
        description="""Put the conversation on hold when the user indicates they need a moment. 
        Call this when user says things like:
        - "hold on", "hold please", "one moment"
        - "give me a minute", "give me a second"  
        - "I need to think", "let me think"
        - "wait", "pause", "just a moment"
        - "I'm talking to someone else"
        - "be right back", "brb"
        - "hang on"
        - "stay on the line"
        The bot will wait silently until the user says a wake phrase like 'hey samora' or 'I'm back'.""",
        properties={},
        required=[]
    )
    
    # Define the end call function schema for LLM
    end_call_function = FunctionSchema(
        name="end_call",
        description="""End the call gracefully when the user indicates they are done.
        Call this when user says things like:
        - "That's all", "I'm done", "Nothing else"
        - "No thanks", "I'm good", "No more questions"
        - "Goodbye", "Bye", "Take care", "See you"
        - "I have nothing else", "That's everything"
        - Responds negatively to 'Is there anything else I can help with?'
        - "No", "Nope" (when asked if they need more help)
        The bot will say a friendly goodbye and then end the call.""",
        properties={},
        required=[]
    )
    
    # Create tools schema with both functions
    tools = ToolsSchema(standard_tools=[hold_function, end_call_function])
    
    # Register the function handlers
    llm.register_function("put_on_hold", put_on_hold)
    llm.register_function("end_call", end_call)

    # System prompt
    messages = [
        {
            "role": "system",
            "content": """You are Samora, a friendly and helpful voice AI assistant. 

Keep your responses concise and conversational since they will be spoken aloud.
Avoid using special characters, emojis, or bullet points.
Be warm, helpful, and engaging.

IMPORTANT - HOLD FEATURE:
When the user indicates they need a moment (saying things like "hold on", "give me a minute", 
"wait", "I need to think", "talking to someone", "be right back", etc.), you MUST call the 
'put_on_hold' function. This will put the call on hold until they say a wake phrase.

When the user returns after being on hold (indicated by phrases like "hey samora", "I'm back", 
"are you there"), greet them warmly and ask how you can help.

IMPORTANT - ENDING CALLS:
When ending a conversation, first ask if there's anything else you can help with.
If the user indicates they're done (saying things like "no", "that's all", "I'm done", 
"nothing else", "goodbye", "bye"), you MUST call the 'end_call' function.
Do NOT just say goodbye - you must call the function to properly end the call.""",
        },
    ]

    # Context management with tools
    context = LLMContext(messages, tools=tools)
    context_aggregator = LLMContextAggregatorPair(context)

    # Build the pipeline
    # Note: HoldWakeProcessor is added after STT to filter transcriptions when on hold
    # When on hold, only wake phrases will pass through to the LLM
    # RTVIProcessor enables real-time message display in Pipecat Playground
    pipeline = Pipeline(
        [
            transport.input(),              # Audio input from user
            rtvi,                           # RTVI processor for frontend messages
            stt,                            # Speech-to-Text
            hold_wake_processor,            # Hold/Wake filter (drops non-wake phrases when on hold)
            context_aggregator.user(),      # Aggregate user messages
            llm,                            # LLM processing
            tts,                            # Text-to-Speech
            transport.output(),             # Audio output to user
            context_aggregator.assistant(), # Aggregate assistant messages
        ]
    )

    # Create the task with RTVIObserver for frontend message display
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        observers=[RTVIObserver(rtvi)],  # Translates frames to RTVI messages for UI
        idle_timeout_secs=runner_args.pipeline_idle_timeout_secs,
    )

    # Event handlers
    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Client connected!")
        # Greet the user
        messages.append({
            "role": "system",
            "content": "Please greet the user warmly and introduce yourself as Samora, their AI assistant."
        })
        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        await task.cancel()

    # Run the pipeline
    runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)
    await runner.run(task)


async def bot(runner_args: RunnerArguments):
    """Main bot entry point for Pipecat Cloud."""
    transport = await create_transport(runner_args, transport_params)
    await run_bot(transport, runner_args)
