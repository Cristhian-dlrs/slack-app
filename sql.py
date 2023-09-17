from sqlalchemy import Boolean, Column, ForeignKey, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id: Column('id', String, primary_key=True)
    team_id: Column('team_id', String)
    name: Column('name', String)
    deleted: Column('deleted', Boolean)
    real_name: Column('real_name', String)

    messages: relationship('message', backref='user')
    channels: relationship('channel', backref='user')

    def __init__(self, id: str, team_id: str, name: str, deleted: bool, real_name: str) -> None:
        self.id = id
        self.team_id = team_id
        self.name = name
        self.deleted = deleted
        self.real_name = real_name


class Channel(Base):
    __tablename__ = 'channels'

    id: str
    user: str
    name: str
    is_channel: bool
    is_group: bool
    is_im: bool
    is_mpim: bool
    is_private: bool
    created: int
    is_archived: bool
    is_general: bool

    def __init__(self, id: str, user: str, name: str, is_channel: bool, is_group: bool, is_im: bool, is_mpim: bool, is_private: bool, created: int, is_archived: bool, is_general: bool) -> None:
        self.id = id
        self.user = user
        self.name = name
        self.is_channel = is_channel
        self.is_group = is_group
        self.is_im = is_im
        self.is_mpim = is_mpim
        self.is_private = is_private
        self.created = created
        self.is_archived = is_archived
        self.is_general = is_general


class Message(Base):
    __tablename__ = 'messages'

    type: Column('type', String)
    subtype: Column('subtype', String)
    text: Column('text', String)
    ts: str
    team: str

    channel: Column('channel', String, ForeignKey('channel.id'))
    user: Column('user', String, ForeignKey('user.id'))

    def __init__(self, type: str, subtype: str, text: str, user: str, ts: str, team: str, channel: str) -> None:
        self.type = type
        self.subtype = subtype
        self.text = text
        self.user = user
        self.ts = ts
        self.team = team
        self.channel = channel


engine = create_engine("sqlite:///slack.db", echo=True)
Base.metadata.create_all(bind=engine)

Conn = sessionmaker(bind=engine)
dbCtx = Conn()
