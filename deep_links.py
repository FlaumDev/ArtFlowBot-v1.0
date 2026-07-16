import re


COMPETITION_PAYLOAD_RE = re.compile(r"competition_([1-9]\d*)")
START_COMMAND_RE = re.compile(r"/start(?:@\w+)?(?:\s+(.+))?")


def parse_competition_deep_link(message_text):
    if not isinstance(message_text, str):
        return None

    text = message_text.strip()

    if not text:
        return None

    start_match = START_COMMAND_RE.fullmatch(text)

    if start_match:
        payload = start_match.group(1)

        if not payload:
            return None
    else:
        payload = text

    payload_match = COMPETITION_PAYLOAD_RE.fullmatch(payload.strip())

    if not payload_match:
        return None

    return int(payload_match.group(1))
