from typing import List, Any


class Purpose:
    value: str
    creator: str
    last_set: int

    def __init__(self, value: str, creator: str, last_set: int) -> None:
        self.value = value
        self.creator = creator
        self.last_set = last_set


class Channel:
    id: str
    name: str
    is_channel: bool
    is_group: bool
    is_im: bool
    is_mpim: bool
    is_private: bool
    created: int
    is_archived: bool
    is_general: bool
    unlinked: int
    name_normalized: str
    is_shared: bool
    is_org_shared: bool
    is_pending_ext_shared: bool
    pending_shared: List[Any]
    context_team_id: str
    updated: int
    parent_conversation: None
    creator: str
    is_ext_shared: bool
    shared_team_ids: List[str]
    pending_connected_team_ids: List[Any]
    is_member: bool
    topic: Purpose
    purpose: Purpose
    previous_names: List[Any]
    num_members: int

    def __init__(self, id: str, name: str, is_channel: bool, is_group: bool, is_im: bool, is_mpim: bool, is_private: bool, created: int, is_archived: bool, is_general: bool, unlinked: int, name_normalized: str, is_shared: bool, is_org_shared: bool, is_pending_ext_shared: bool, pending_shared: List[Any], context_team_id: str, updated: int, parent_conversation: None, creator: str, is_ext_shared: bool, shared_team_ids: List[str], pending_connected_team_ids: List[Any], is_member: bool, topic: Purpose, purpose: Purpose, previous_names: List[Any], num_members: int) -> None:
        self.id = id
        self.name = name
        self.is_channel = is_channel
        self.is_group = is_group
        self.is_im = is_im
        self.is_mpim = is_mpim
        self.is_private = is_private
        self.created = created
        self.is_archived = is_archived
        self.is_general = is_general
        self.unlinked = unlinked
        self.name_normalized = name_normalized
        self.is_shared = is_shared
        self.is_org_shared = is_org_shared
        self.is_pending_ext_shared = is_pending_ext_shared
        self.pending_shared = pending_shared
        self.context_team_id = context_team_id
        self.updated = updated
        self.parent_conversation = parent_conversation
        self.creator = creator
        self.is_ext_shared = is_ext_shared
        self.shared_team_ids = shared_team_ids
        self.pending_connected_team_ids = pending_connected_team_ids
        self.is_member = is_member
        self.topic = topic
        self.purpose = purpose
        self.previous_names = previous_names
        self.num_members = num_members
