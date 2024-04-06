"""Fake models for testing purposes."""

import typing

from interactions import (
    UPLOADABLE_TYPE,
    ChannelType,
    Client,
    Guild,
    GuildCategory,
    GuildChannel,
    Member,
    Message,
    Permissions,
    Role,
    Snowflake_Type,
    to_snowflake,
)
from interactions.api.http.http_client import HTTPClient

from .actions import (
    BaseAction,
    CreateReactionAction,
    DeleteAction,
    EditAction,
)
from .helpers import fake_process_files, random_snowflake


class FakeGuild(Guild):
    """A fake Guild class for testing."""

    fake_channel: typing.Optional["FakeChannel"]
    fake_roles: typing.Optional["FakeRole"]
    fake_members: typing.Optional["FakeMember"]

    @property
    def channels(self) -> typing.List["GuildChannel"]:
        return self.fake_channel

    @property
    def roles(self) -> typing.List["Role"]:
        return self.fake_roles

    @property
    def members(self) -> typing.List["Member"]:
        return self.fake_members

    def __init__(
        self,
        channel_names: dict[str, list[str]],
        client: "FakeClient",
        *args,
        role_names: list[str] = None,
        member_names: dict[str, list[str]] = None,
        **kwargs,
    ):
        super().__init__(
            client=client,
            id=random_snowflake(),
            name="VirtualTest",
            preferred_locale="english_us",
            owner_id=random_snowflake(),
            *args,
            **kwargs,
        )
        self.fake_channel = []
        self.fake_roles = []
        self.fake_members = []
        for channel, sub_channels in channel_names.items():
            channel_id = random_snowflake()
            if not sub_channels:
                self.channels.append(
                    FakeChannel(client=client, name=channel, id=channel_id)
                )
            else:
                category = FakeCategory(
                    client=client, name=channel, id=channel_id, guild_id=self.id
                )
                self.channels.append(category)
                for sub_channel_name in sub_channels:
                    sub_channel = FakeChannel(
                        client=client,
                        name=sub_channel_name,
                        id=random_snowflake(),
                        parent_id=category.id,
                    )
                    self.channels.append(sub_channel)
                    category.channels.append(sub_channel)
        self.roles.extend(
            FakeRole(
                name=role,
                client=client,
                color="#ffffff",
                position=order,
                guild_id=self.id,
                permissions=Permissions.ALL,
                id=random_snowflake(),
            )
            for order, role in enumerate(role_names) or []
        )
        self.members.extend(
            FakeMember(
                nick=member,
                id=random_snowflake(),
                fake_roles=[role for role in self.roles if role.name in role_names],
                guild_id=self.id,
                client=client,
            )
            for member, role_names in member_names.items() or []
        )


class FakeRole(Role):
    """A fake Role class for testing"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class FakeMember(Member):
    """A fake Member class for testing"""

    fake_roles: list["FakeRole"] = []

    @property
    def roles(self) -> typing.List["Role"]:
        return self.fake_roles

    def __init__(self, *args, **kwargs):
        self.fake_roles = kwargs.pop("fake_roles", [])
        super().__init__(*args, **kwargs)


class FakeCategory(GuildCategory):
    """A fake Category class for testing"""

    fake_channel: typing.Optional["FakeChannel"]

    @property
    def channels(self) -> typing.List["GuildChannel"]:
        return self.fake_channel

    def __init__(self, *args, **kwargs):
        super().__init__(type=ChannelType.GUILD_CATEGORY, *args, **kwargs)
        self.fake_channel = []


class FakeChannel(GuildChannel):
    """A fake Channel class for testing"""

    async def delete_message(self, message: "Snowflake_Type") -> None:
        """Delete a message from the channel."""
        self.client.http.delete_message(self.id, message.id)
        self.client.actions += (DeleteAction(message_id=message.id),)

    def get_message(self, message_id: "Snowflake_Type") -> "Message":
        """Get a message from the channel."""
        return self.client.fake_get_message(message_id)

    def __init__(self, *args, **kwargs):
        super().__init__(type=ChannelType.GUILD_TEXT, *args, **kwargs)


class FakeClient(Client):
    """
    A fake Client class for testing

    This class is used to simulate a Client object for testing purposes.
    It will override the HTTPClient object with a FakeHttp object
    to bypass the discord api and store the actions that would be taken in a list.
    """

    __slots__ = ("_fake_cache", "actions")
    _fake_cache: dict[int, "Message"]
    actions: tuple[BaseAction, ...]

    def fake_get_message(self, message_id: "Snowflake_Type") -> "Message":
        """Get a message from the cache."""
        return self._fake_cache[to_snowflake(message_id)]

    def __init__(self, *args, **kwargs):
        self._fake_cache = {}
        self.actions = ()
        super().__init__(*args, **kwargs)
        self.http = FakeHttp(client=self)

    def __del__(self):
        self._fake_cache.clear()
        del self._fake_cache

    def command(self, *args, **kwargs):
        """dummy function to suppress abstract method error"""
        print(self, args, kwargs)


class FakeHttp(HTTPClient):
    """
    A fake HTTPClient class for testing

    This class will simulate any calls made to the discord api.
    """

    def __init__(self, *args, client: FakeClient, **kwargs):
        self.client = client
        self.actions = self.client.actions
        self._fake_cache = self.client._fake_cache
        super().__init__(*args, **kwargs)

    async def delete_message(
        self,
        channel_id: "Snowflake_Type",
        message_id: "Snowflake_Type",
        reason: str | None = None,
    ) -> None:
        """Delete a message from a channel."""
        self.actions += (
            DeleteAction(
                message_id=to_snowflake(message_id),
                channel_id=int(to_snowflake(channel_id)),
                reason=reason,
            ),
        )
        del self._fake_cache[to_snowflake(message_id)]

    async def edit_message(
        self,
        payload: dict,
        channel_id: "Snowflake_Type",
        message_id: "Snowflake_Type",
        files: list[UPLOADABLE_TYPE] | None = None,
    ) -> "Message":
        """Edit a message in a channel."""
        fake_process_files(files)
        message = self._fake_cache[to_snowflake(message_id)]
        message.update_from_dict(payload)
        self._fake_cache[to_snowflake(message_id)] = message
        self.actions += (
            EditAction(
                message=message.to_dict(), channel_id=int(to_snowflake(channel_id))
            ),
        )
        return message

    async def create_reaction(
        self, channel_id: "Snowflake_Type", message_id: "Snowflake_Type", emoji: str
    ) -> None:
        """Create a reaction on a message."""
        self._fake_cache[to_snowflake(message_id)].reactions.append(emoji)
        self.actions += (
            CreateReactionAction(
                message_id=to_snowflake(message_id),
                emoji=emoji,
                channel_id=to_snowflake(channel_id),
            ),
        )
