from typing import List, Any


class Profile:
    title: str
    phone: str
    skype: str
    real_name: str
    real_name_normalized: str
    display_name: str
    display_name_normalized: str
    fields: any
    status_text: str
    status_emoji: str
    status_emoji_display_info: List[Any]
    status_expiration: int
    avatar_hash: str
    always_active: bool
    first_name: str
    last_name: str
    image_24: str
    image_32: str
    image_48: str
    image_72: str
    image_192: str
    image_512: str
    status_text_canonical: str
    team: str

    def __init__(self, title: str, phone: str, skype: str, real_name: str, real_name_normalized: str, display_name: str, display_name_normalized: str, fields: any, status_text: str, status_emoji: str, status_emoji_display_info: List[Any], status_expiration: int, avatar_hash: str, always_active: bool, first_name: str, last_name: str, image_24: str, image_32: str, image_48: str, image_72: str, image_192: str, image_512: str, status_text_canonical: str, team: str) -> None:
        self.title = title
        self.phone = phone
        self.skype = skype
        self.real_name = real_name
        self.real_name_normalized = real_name_normalized
        self.display_name = display_name
        self.display_name_normalized = display_name_normalized
        self.fields = fields
        self.status_text = status_text
        self.status_emoji = status_emoji
        self.status_emoji_display_info = status_emoji_display_info
        self.status_expiration = status_expiration
        self.avatar_hash = avatar_hash
        self.always_active = always_active
        self.first_name = first_name
        self.last_name = last_name
        self.image_24 = image_24
        self.image_32 = image_32
        self.image_48 = image_48
        self.image_72 = image_72
        self.image_192 = image_192
        self.image_512 = image_512
        self.status_text_canonical = status_text_canonical
        self.team = team


class User:
    id: str
    team_id: str
    name: str
    deleted: bool
    color: int
    real_name: str
    tz: str
    tz_label: str
    tz_offset: int
    profile: Profile
    is_admin: bool
    is_owner: bool
    is_primary_owner: bool
    is_restricted: bool
    is_ultra_restricted: bool
    is_bot: bool
    is_app_user: bool
    updated: int
    is_email_confirmed: bool
    who_can_share_contact_card: str

    def __init__(self, id: str, team_id: str, name: str, deleted: bool, color: int, real_name: str, tz: str, tz_label: str, tz_offset: int, profile: Profile, is_admin: bool, is_owner: bool, is_primary_owner: bool, is_restricted: bool, is_ultra_restricted: bool, is_bot: bool, is_app_user: bool, updated: int, is_email_confirmed: bool, who_can_share_contact_card: str) -> None:
        self.id = id
        self.team_id = team_id
        self.name = name
        self.deleted = deleted
        self.color = color
        self.real_name = real_name
        self.tz = tz
        self.tz_label = tz_label
        self.tz_offset = tz_offset
        self.profile = profile
        self.is_admin = is_admin
        self.is_owner = is_owner
        self.is_primary_owner = is_primary_owner
        self.is_restricted = is_restricted
        self.is_ultra_restricted = is_ultra_restricted
        self.is_bot = is_bot
        self.is_app_user = is_app_user
        self.updated = updated
        self.is_email_confirmed = is_email_confirmed
        self.who_can_share_contact_card = who_can_share_contact_card
