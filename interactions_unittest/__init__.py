import datetime
import typing
from copy import deepcopy
from os import urandom

import interactions
from interactions import (
    Permissions,
    SlashContext,
    Client,
    GuildChannel,
    GuildCategory,
    ChannelType,
    Role,
    Member,
    Guild,
    Message,
    Embed,
    BaseComponent,
    Sticker,
    Snowflake_Type,
    AllowedMentions,
    MessageReference,
    UPLOADABLE_TYPE,
    MessageFlags,
    models,
    to_snowflake,
    Attachment,
    process_message_payload,
)
from interactions.api.http.http_client import HTTPClient


def random_snowflake() -> int:
    timestamp = int(
        (datetime.datetime.now() - datetime.datetime(2015, 1, 1)).total_seconds() * 1000
    )
    worker = int("0x" + urandom(5).hex(), 0)
    process = int("0x" + urandom(5).hex(), 0)
    increment = int("0x" + urandom(12).hex(), 0)

    return int((timestamp << 22) | (worker << 17) | (process << 12) | increment)


class FakeSlashContext(SlashContext):
    __slots__ = ("actions", "_fake_cache", "http")
    fake_guild: typing.Optional["FakeGuild"] = None

    @property
    def guild(self) -> typing.Optional["FakeGuild"]:
        return self.fake_guild

    @guild.setter
    def guild(self, value: typing.Optional["FakeGuild"]):
        self.fake_guild = value
        self.guild_id = value.id

    fake_channel: typing.Optional["FakeChannel"] = None

    @property
    def channel(self) -> typing.Optional["FakeChannel"]:
        return self.fake_channel

    @channel.setter
    def channel(self, value: typing.Optional["FakeChannel"]):
        self.fake_channel = value
        self.channel_id = value.id

    fake_author: typing.Optional["FakeMember"] = None

    @property
    def author(self) -> typing.Optional["FakeMember"]:
        return self.fake_author

    @author.setter
    def author(self, value: typing.Optional["FakeMember"]):
        self.fake_author = value
        self.author_id = value.id

    def __init__(self, client: "interactions.Client"):
        self.actions = client.actions
        self._fake_cache = client._fake_cache
        super().__init__(client)
        self.http = self

    async def defer(self, *, ephemeral: bool = False) -> None:
        """
        Defer the interaction.

        Args:
            ephemeral: Whether the interaction response should be ephemeral.
        """
        self.deferred = True
        self.ephemeral = ephemeral
        self.actions += ({"action": "defer", "ephemeral": ephemeral},)

    async def send(
        self,
        content: typing.Optional[str] = None,
        *,
        embeds: typing.Optional[
            typing.Union[
                typing.Iterable[typing.Union["Embed", dict]],
                typing.Union["Embed", dict],
            ]
        ] = None,
        embed: typing.Optional[typing.Union["Embed", dict]] = None,
        components: typing.Optional[
            typing.Union[
                typing.Iterable[typing.Iterable[typing.Union["BaseComponent", dict]]],
                typing.Iterable[typing.Union["BaseComponent", dict]],
                "BaseComponent",
                dict,
            ]
        ] = None,
        stickers: typing.Optional[
            typing.Union[
                typing.Iterable[typing.Union["Sticker", "Snowflake_Type"]],
                "Sticker",
                "Snowflake_Type",
            ]
        ] = None,
        allowed_mentions: typing.Optional[typing.Union["AllowedMentions", dict]] = None,
        reply_to: typing.Optional[
            typing.Union["MessageReference", "Message", dict, "Snowflake_Type"]
        ] = None,
        files: typing.Optional[
            typing.Union["UPLOADABLE_TYPE", typing.Iterable["UPLOADABLE_TYPE"]]
        ] = None,
        file: typing.Optional["UPLOADABLE_TYPE"] = None,
        tts: bool = False,
        suppress_embeds: bool = False,
        silent: bool = False,
        flags: typing.Optional[typing.Union[int, "MessageFlags"]] = None,
        delete_after: typing.Optional[float] = None,
        ephemeral: bool = False,
        **kwargs: typing.Any,
    ) -> "Message":
        """
        Send a message.

        Args:
            content: Message text content.
            embeds: Embedded rich content (up to 6000 characters).
            embed: Embedded rich content (up to 6000 characters).
            components: The components to include with the message.
            stickers: IDs of up to 3 stickers in the server to send in the message.
            allowed_mentions: Allowed mentions for the message.
            reply_to: Message to reference, must be from the same channel.
            files: Files to send, the path, bytes or File() instance, defaults to None. You may have up to 10 files.
            file: Files to send, the path, bytes or File() instance, defaults to None. You may have up to 10 files.
            tts: Should this message use Text To Speech.
            suppress_embeds: Should embeds be suppressed on this send
            silent: Should this message be sent without triggering a notification.
            flags: Message flags to apply.
            delete_after: Delete message after this many seconds.
            ephemeral: Whether the response should be ephemeral

        Returns:
            New message object that was sent.
        """
        flags = MessageFlags(flags or 0)
        if ephemeral or self.ephemeral:
            flags |= MessageFlags.EPHEMERAL
            self.ephemeral = True
        if suppress_embeds:
            flags |= MessageFlags.SUPPRESS_EMBEDS
        if silent:
            flags |= MessageFlags.SILENT

        if not flags:
            flags = MessageFlags(0)
        if suppress_embeds:
            if isinstance(flags, int):
                flags = MessageFlags(flags)
            flags = flags | MessageFlags.SUPPRESS_EMBEDS
        if silent:
            if isinstance(flags, int):
                flags = MessageFlags(flags)
            flags = flags | MessageFlags.SILENT

        if (
            files
            and (
                isinstance(files, typing.Iterable)
                and any(
                    isinstance(file, interactions.models.discord.message.Attachment)
                    for file in files
                )
            )
            or isinstance(files, interactions.models.discord.message.Attachment)
        ):
            raise ValueError(
                "Attachments are not files. Attachments only contain metadata about the file, not the file itself - to send an attachment, you need to download it first. Check Attachment.url"
            )

        message_payload = models.discord.message.process_message_payload(
            content=content,
            embeds=embeds or embed,
            components=components,
            stickers=stickers,
            allowed_mentions=allowed_mentions,
            reply_to=reply_to,
            tts=tts,
            flags=flags,
            **kwargs,
        )

        message_data = deepcopy(message_payload)
        message_data["id"] = random_snowflake()

        if "embeds" in message_data:
            message_data["embeds"] = [
                embed.to_dict() if isinstance(embed, Embed) else embed
                for embed in message_data["embeds"]
            ]

        if message_data:
            self.actions += ({"action": "send", "message": message_data},)
            message = Message.from_dict(deepcopy(message_data), self.client)
            self._fake_cache[message.id] = message

            return message

    respond = send

    async def delete(self, message: "Snowflake_Type" = "@original") -> None:
        """
        Delete a message sent in response to this interaction.

        Args:
            message: The message to delete. Defaults to @original which represents the initial response message.
        """
        self.actions += (
            {
                "action": "delete",
                "message_id": to_snowflake(message)
                if message != "@original"
                else message,
            },
        )
        del self._fake_cache[
            to_snowflake(message) if message != "@original" else message
        ]

    async def edit(
        self,
        message: "Snowflake_Type" = "@original",
        *,
        content: typing.Optional[str] = None,
        embeds: typing.Optional[
            typing.Union[
                typing.Iterable[typing.Union["Embed", dict]],
                typing.Union["Embed", dict],
            ]
        ] = None,
        embed: typing.Optional[typing.Union["Embed", dict]] = None,
        components: typing.Optional[
            typing.Union[
                typing.Iterable[typing.Iterable[typing.Union["BaseComponent", dict]]],
                typing.Iterable[typing.Union["BaseComponent", dict]],
                "BaseComponent",
                dict,
            ]
        ] = None,
        attachments: typing.Optional[typing.Sequence[Attachment | dict]] = None,
        allowed_mentions: typing.Optional[typing.Union["AllowedMentions", dict]] = None,
        files: typing.Optional[
            typing.Union["UPLOADABLE_TYPE", typing.Iterable["UPLOADABLE_TYPE"]]
        ] = None,
        file: typing.Optional["UPLOADABLE_TYPE"] = None,
        tts: bool = False,
    ) -> "interactions.Message":
        message_payload = process_message_payload(
            content=content,
            embeds=embeds or embed,
            components=components,
            allowed_mentions=allowed_mentions,
            attachments=attachments,
            tts=tts,
        )

        self._fake_cache[
            to_snowflake(message) if message != "@original" else message
        ].update_from_dict(message_payload)
        message_data = deepcopy(
            self._fake_cache[
                to_snowflake(message) if message != "@original" else message
            ].to_dict()
        )
        message_data["id"] = (
            to_snowflake(message) if message != "@original" else message
        )

        if "embeds" in message_data:
            message_data["embeds"] = [
                embed.to_dict() if isinstance(embed, Embed) else embed
                for embed in message_data["embeds"]
            ]

        if message_data:
            self.actions += ({"action": "edit", "message": message_data},)
            self._fake_cache[message_data["id"]] = Message.from_dict(
                deepcopy(message_data), self.client
            )
            return Message.from_dict(deepcopy(message_data), self.client)


class FakeGuild(Guild):
    fake_channel: typing.Optional["FakeChannel"] = []
    fake_roles: typing.Optional["FakeRole"] = []
    fake_members: typing.Optional["FakeMember"] = []

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
        *args,
        role_names: list[str] = None,
        member_names: dict[str, list[str]] = None,
        **kwargs,
    ):
        client = get_client()
        super().__init__(
            client=client,
            id=random_snowflake(),
            name="VirtualTest",
            preferred_locale="english_us",
            owner_id=random_snowflake(),
            *args,
            **kwargs,
        )
        for channel, sub_channels in channel_names.items():
            channel_id = random_snowflake()
            if not sub_channels:
                self.channels.append(
                    FakeChannel(client=client, name=channel, id=channel_id)
                )
            else:
                category = FakeCategory(client=client, name=channel, id=channel_id)
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class FakeMember(Member):
    fake_roles: typing.Optional["FakeRole"] = []

    @property
    def roles(self) -> typing.List["Role"]:
        return self.fake_roles

    def __init__(self, *args, **kwargs):
        self.fake_roles = kwargs.pop("fake_roles", [])
        super().__init__(*args, **kwargs)


class FakeCategory(GuildCategory):
    def __init__(self, *args, **kwargs):
        super().__init__(type=ChannelType.GUILD_CATEGORY, *args, **kwargs)


class FakeChannel(GuildChannel):
    def __init__(self, *args, **kwargs):
        super().__init__(type=ChannelType.GUILD_TEXT, *args, **kwargs)


class FakeClient(Client):
    __slots__ = ("_fake_cache", "actions")

    def __init__(self, *args, **kwargs):
        self._fake_cache = {}
        self.actions = ()
        super().__init__(*args, **kwargs)
        self.http = FakeHttp(client=self)


class FakeHttp(HTTPClient):
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
        self.actions += ({"action": "delete", "message_id": to_snowflake(message_id)},)
        del self._fake_cache[to_snowflake(message_id)]

    async def edit_message(
        self,
        payload: dict,
        channel_id: "Snowflake_Type",
        message_id: "Snowflake_Type",
        files: list["UPLOADABLE_TYPE"] | None = None,
    ) -> "Message":
        message = self._fake_cache[to_snowflake(message_id)]
        message.update_from_dict(payload)
        self._fake_cache[to_snowflake(message_id)] = message
        self.actions += ({"action": "edit", "message": message.to_dict()},)
        return message

    async def create_reaction(
        self, channel_id: "Snowflake_Type", message_id: "Snowflake_Type", emoji: str
    ) -> None:
        self._fake_cache[to_snowflake(message_id)].reactions.append(emoji)
        self.actions += (
            {
                "action": "create_reaction",
                "message_id": to_snowflake(message_id),
                "emoji": emoji,
            },
        )


async def call_slash(
    func: typing.Callable, *args, _client: FakeClient = None, **kwargs
):
    """
    Call a slash command function with the given arguments.

    :param func: The function to call.
    :param _client: A FakeClient instance to use.
    :param args: The positional arguments to pass to the function.
    :param kwargs: The keyword arguments to pass to the function.
    :return:
    """

    # default_kwargs

    client = FakeClient() or _client
    client.add_interaction(func)
    ctx = FakeSlashContext(client)
    for key, value in kwargs.items():
        if key.startswith("test_ctx_"):
            setattr(ctx,key.split("test_ctx_", 1)[1], value)

    ctx.args = args
    ctx.kwargs = {
        key: value for key, value in kwargs.items() if not key.startswith("text_ctx")
    }

    await func(ctx, *args, **kwargs)

    return deepcopy(ctx.actions)


def get_client() -> FakeClient:
    return FakeClient()
