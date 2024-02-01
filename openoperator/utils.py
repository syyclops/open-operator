from typing import List
from urllib.parse import quote


def split_string_with_limit(text: str, limit: int, encoding) -> List[str]:
    """
    Splits a string into multiple parts with a limit on the number of tokens in each part.
    """
    tokens = encoding.encode(text)
    parts = []
    current_part = []
    current_count = 0

    for token in tokens:
        current_part.append(token)
        current_count += 1

        if current_count >= limit:
            parts.append(current_part)
            current_part = []
            current_count = 0

    if current_part:
        parts.append(current_part)

    text_parts = [encoding.decode(part) for part in parts]

    return text_parts


def create_uri(name: str) -> str:
    """
    Create a URI from string.
    """
    # name = re.sub(r'[^a-zA-Z0-9]', '', str(name).lower())
    # name = name.replace("'", "_")  # Replace ' with _
    name = quote(name.lower())
    return name