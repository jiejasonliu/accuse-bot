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


def insert_line_breaks(text: str,
                       max_line_length: int = 75,
                       delimiter: str = '\n',
                       line_prepend: str = '') -> str:
    """
    Insert line breaks in a string after a specified number of characters.

    Args:
        text (str): The input text.
        max_line_length (int): Maximum number of characters per line.
        delimiter (str): Line break character or text to add between each line
        line_prepend (str): Text to add at the beginning of each line

    Returns:
        str: Text with line breaks inserted.
    """
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        if len(current_line) + len(word) <= max_line_length:
            current_line += word + " "
        else:
            lines.append(current_line.strip())
            current_line = word + " "

    if current_line:
        lines.append(current_line.strip())

    lines = [line_prepend + line for line in lines if line.strip() != '']
    return delimiter.join(lines)
