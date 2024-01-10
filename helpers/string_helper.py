def escape_markdown(text: str) -> str:
    """
    Escape text to avoid unintended Markdown formatting.

    Args:
        text (str): The input text to be escaped.

    Returns:
        str: Escaped text.
    """
    # List of characters to escape
    escape_chars = [
        '_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|',
        '{', '}', '.', '!'
    ]

    # Escape each character in the text
    escaped_text = ''.join(
        ['\\' + char if char in escape_chars else char for char in text])

    return escaped_text
