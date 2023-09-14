from typing import List, Any


class Message:
    type: str
    subtype: str
    text: str
    user: str
    ts: str
    blocks: List[Any]
    team: str
    channel: str

    def __init__(self, type: str, subtype: str, text: str, user: str, ts: str, blocks: List[Any], team: str, channel: str) -> None:
        self.type = type
        self.subtype = subtype
        self.text = text
        self.user = user
        self.ts = ts
        self.blocks = blocks
        self.team = team
        self.channel = channel