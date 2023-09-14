class Message:
    type: str
    subtype: str
    text: str
    user: str
    ts: str
    team: str
    channel: str

    def __init__(self, type: str, subtype: str, text: str, user: str, ts: str, team: str, channel: str) -> None:
        self.type = type
        self.subtype = subtype
        self.text = text
        self.user = user
        self.ts = ts
        self.team = team
        self.channel = channel
