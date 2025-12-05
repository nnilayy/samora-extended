import json
from pathlib import Path
from datetime import datetime
from loguru import logger


def save_chat_history(
    messages: list,
    output_dir: str = "logs/chats",
    filename_prefix: str = "conversation",
) -> str | None:
    """
    Save chat history to a JSON file.

    Args:
        messages: List of conversation messages from LLMContext.
        output_dir: Directory to save logs (default: logs/chats).
        filename_prefix: Prefix for the filename (default: conversation).

    Returns:
        The path to the saved file, or None if saving failed.
    """
    try:
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.json"
        filepath = output_path / filename

        # Prepare data
        dump_data = {
            "timestamp": timestamp,
            "saved_at": datetime.now().isoformat(),
            "total_messages": len(messages),
            "messages": messages,
        }

        # Write to file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(dump_data, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Chat history saved to {filepath} ({len(messages)} messages)")
        return str(filepath)

    except Exception as e:
        logger.error(f"Failed to save chat history: {e}")
        return None
