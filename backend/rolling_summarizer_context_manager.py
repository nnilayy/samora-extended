import asyncio
from loguru import logger
from typing import Optional, List
from pipecat.frames.frames import Frame, LLMFullResponseEndFrame
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection


# Default prompt for summarization
DEFAULT_SUMMARY_PROMPT = """Please provide a concise summary of the following conversation. 
Capture all key information, decisions, preferences, and important details that would be 
needed to continue the conversation naturally. Focus on facts and context, not the flow of dialogue.

CONVERSATION:
{conversation}

SUMMARY:"""


class RollingSummarizerContextManager(FrameProcessor):
    """
    Manages context window size through rolling summarization.

    When the message count exceeds the threshold, this processor:
    1. Takes a snapshot of current messages
    2. Summarizes old messages via LLM (in background)
    3. Keeps recent messages intact
    4. Merges the result on the next safe frame

    The summarization runs in parallel - conversation continues normally.
    Merge only happens at safe points (LLMFullResponseEndFrame).
    """

    def __init__(
        self,
        context,
        llm_service,
        threshold: int = 100,
        keep_recent: int = 20,
        summary_prompt: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the Rolling Summarizer Context Manager.

        Args:
            context: The LLMContext object (from context_aggregator.user().context)
            llm_service: Any Pipecat LLM service (OpenAI, Google, Cerebras, Groq, etc.)
            threshold: Trigger summarization when message count >= this value
            keep_recent: Number of recent messages to keep (not summarized)
            summary_prompt: Custom prompt for summarization (optional)
        """
        super().__init__(**kwargs)

        self._context = context
        self._llm_service = llm_service
        self._threshold = threshold
        self._keep_recent = keep_recent
        self._summary_prompt = summary_prompt or DEFAULT_SUMMARY_PROMPT

        # State for pending merge
        self._pending_merge: Optional[List[dict]] = None
        self._snapshot_len: Optional[int] = None
        self._summarization_task: Optional[asyncio.Task] = None

        logger.info(
            f"RollingSummarizerContextManager initialized: "
            f"threshold={threshold}, keep_recent={keep_recent}"
        )

    async def check_and_summarize(self):
        """
        Called externally (e.g., from LLM event handler) to check and trigger summarization.
        This is the primary trigger method - more reliable than waiting for frames.
        """
        # Step 1: Apply pending merge if exists (from previous summarization)
        if self._pending_merge is not None:
            await self._apply_pending_merge()

        # Step 2: Check if we need to start new summarization
        current_len = len(self._context.messages)

        if current_len >= self._threshold:
            # Only start if not already running
            if self._summarization_task is None or self._summarization_task.done():
                logger.info(
                    f"Context threshold reached ({current_len} >= {self._threshold}). Starting summarization..."
                )
                await self._run_summarization()
                if self._pending_merge is not None:
                    await self._apply_pending_merge()

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """Process frames, checking for summarization triggers."""
        await super().process_frame(frame, direction)

        # Trigger on LLMFullResponseEndFrame - safe point for context operations
        if isinstance(frame, LLMFullResponseEndFrame):
            # Step 1: Apply pending merge if exists
            if self._pending_merge is not None:
                await self._apply_pending_merge()

            # Step 2: Check if we need to start new summarization
            current_len = len(self._context.messages)
            if current_len >= self._threshold:
                if self._summarization_task is None or self._summarization_task.done():
                    logger.info(
                        f"Context threshold reached ({current_len} >= {self._threshold}). Starting summarization..."
                    )
                    await self._run_summarization()
                    if self._pending_merge is not None:
                        await self._apply_pending_merge()

        # Always push frame through - never block the pipeline
        await self.push_frame(frame, direction)

    async def _run_summarization(self):
        """
        Run summarization in background.

        This task:
        1. Takes a snapshot of current message count
        2. Builds a summary of old messages via LLM
        3. Stores result in _pending_merge (does NOT apply yet)

        The merge happens later on the next LLMFullResponseEndFrame.
        """
        try:
            messages = self._context.messages

            # Take snapshot of current length
            self._snapshot_len = len(messages)

            # Calculate indices
            # messages[0] = system prompt (always keep)
            # messages[1 : snapshot_len - keep_recent] = to summarize
            # messages[snapshot_len - keep_recent : snapshot_len] = keep as-is

            system_message = messages[0]
            summarize_end_idx = self._snapshot_len - self._keep_recent

            # Need at least some messages to summarize
            if summarize_end_idx <= 1:
                logger.debug("Not enough messages to summarize, skipping")
                self._pending_merge = None
                self._snapshot_len = None
                return

            messages_to_summarize = messages[1:summarize_end_idx]
            messages_to_keep = messages[summarize_end_idx : self._snapshot_len]

            logger.info(
                f"Summarizing {len(messages_to_summarize)} messages, keeping {len(messages_to_keep)} recent"
            )

            # Build conversation text for summarization
            conversation_text = self._build_conversation_text(messages_to_summarize)

            # Call LLM to get summary
            summary_text = await self._call_summarizer_llm(conversation_text)

            if not summary_text:
                logger.warning("Summarization returned empty result")
                self._pending_merge = None
                self._snapshot_len = None
                return

            # Build the new message list
            summary_message = {
                "role": "assistant",
                "content": f"[Previous conversation summary: {summary_text}]",
            }

            # Store pending merge
            self._pending_merge = [system_message, summary_message] + list(
                messages_to_keep
            )

            logger.info(
                f"Summarization complete. Will reduce from {self._snapshot_len} to {len(self._pending_merge)} messages"
            )

        except asyncio.CancelledError:
            logger.debug("Summarization task cancelled")
            self._pending_merge = None
            self._snapshot_len = None
            raise

        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            self._pending_merge = None
            self._snapshot_len = None

    async def _apply_pending_merge(self):
        """
        Apply the pending merge at a safe point.

        Merges:
        - Summarized messages (pending_merge)
        - Any new messages added since snapshot

        Uses set_messages() for in-place replacement.
        """
        if self._pending_merge is None or self._snapshot_len is None:
            return

        try:
            # Get messages that were added AFTER our snapshot
            current_messages = self._context.messages
            new_messages_since_snapshot = current_messages[self._snapshot_len :]

            # Final merged result
            final_messages = self._pending_merge + new_messages_since_snapshot

            # Apply using set_messages (in-place replacement)
            self._context.set_messages(final_messages)

            logger.info(
                f"Context merged: {len(final_messages)} messages (+{len(new_messages_since_snapshot)} during summarization)"
            )

        except Exception as e:
            logger.error(f"Failed to apply pending merge: {e}")

        finally:
            # Clear state regardless of success/failure
            self._pending_merge = None
            self._snapshot_len = None

    def _build_conversation_text(self, messages: List[dict]) -> str:
        """Build a text representation of messages for summarization."""
        lines = []
        for msg in messages:
            role = msg.get("role", "unknown").upper()
            content = msg.get("content", "")

            # Handle content that might be a list (multimodal)
            if isinstance(content, list):
                # Extract text from content list
                text_parts = []
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text_parts.append(part.get("text", ""))
                    elif isinstance(part, str):
                        text_parts.append(part)
                content = " ".join(text_parts)

            if content:
                lines.append(f"{role}: {content}")

        return "\n\n".join(lines)

    async def _call_summarizer_llm(self, conversation_text: str) -> Optional[str]:
        """
        Call the LLM service to generate a summary using run_inference().

        Uses Pipecat's built-in run_inference method which works with any LLM service.
        """
        try:
            from pipecat.processors.aggregators.openai_llm_context import (
                OpenAILLMContext,
            )

            # Build the prompt
            prompt = self._summary_prompt.format(conversation=conversation_text)

            # Create a temporary context for summarization
            summary_messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that creates concise conversation summaries.",
                },
                {"role": "user", "content": prompt},
            ]

            # Create a temporary LLMContext for the summary request
            summary_context = OpenAILLMContext(messages=summary_messages)

            # Use the LLM service's run_inference method
            result = await self._llm_service.run_inference(summary_context)

            if result:
                return result.strip()
            else:
                logger.warning("run_inference returned None")
                return None

        except NotImplementedError:
            logger.warning(
                f"run_inference not implemented for {type(self._llm_service).__name__}"
            )
            return None
        except Exception as e:
            logger.error(f"Error calling summarizer LLM: {e}")
            return None
