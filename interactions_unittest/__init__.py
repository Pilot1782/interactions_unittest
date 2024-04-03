import datetime
import time
import typing
from copy import deepcopy
from os import urandom
from enum import Enum

import interactions
from interactions import (
    AllowedMentions,
    BaseComponent,
    Permissions,
    Client,
    GuildChannel,
    GuildCategory,
    ChannelType,
    Role,
    Member,
    Guild,
    Embed,
    Message,
    MessageReference,
    SlashCommandChoice,
    SlashContext,
    Snowflake_Type,
    Sticker,
    UPLOADABLE_TYPE,
    MessageFlags,
    models,
    to_snowflake,
    Attachment,
    process_message_payload,
)
from interactions.api.http.http_client import HTTPClient

class ActionType(str, Enum):
    """
    An enumeration of the different action types.
    """

    DEFER = "defer"
    SEND = "send"
    DELETE = "delete"
    EDIT = "edit"
    CREATE_REACTION = "create_reaction"
    SEND_MODAL = "send_modal"
    SEND_CHOICES = "send_choices"

class BaseAction:
    action_type: ActionType
    creation_time: float

    def __init__(self):
        self.creation_time = time.time_ns()

class DeferAction(BaseAction):
    action_type = ActionType.DEFER
    ephemeral: bool

    def __init__(self, ephemeral: bool):
        super().__init__()
        self.ephemeral = ephemeral

class SendAction(BaseAction):
    action_type = ActionType.SEND
    message: dict

    def __init__(self, message: dict):
        super().__init__()
        self.message = message

class DeleteAction(BaseAction):
    action_type = ActionType.DELETE
    message_id: int

    def __init__(self, message_id: int):
        super().__init__()
        self.message_id = message_id

class EditAction(BaseAction):
    action_type = ActionType.EDIT
    message: dict

    def __init__(self, message: dict):
        super().__init__()
        self.message = message

class CreateReactionAction(BaseAction):
    action_type = ActionType.CREATE_REACTION
    message_id: int
    emoji: str

    def __init__(self, message_id: int, emoji: str):
        super().__init__()
        self.message_id = message_id
        self.emoji = emoji

class SendModalAction(BaseAction):
    action_type = ActionType.SEND_MODAL
    modal: dict

    def __init__(self, modal: dict):
        super().__init__()
        self.modal = modal

class SendChoicesAction(BaseAction):
    action_type = ActionType.SEND_CHOICES
    choices: list[dict]

    def __init__(self, choices: list[dict]):
        super().__init__()
        self.choices = choices

def random_snowflake() -> int:
    timestamp = int(
        (datetime.datetime.now() - datetime.datetime(2015, 1, 1)).total_seconds() * 1000
    )
    worker = int("0x" + urandom(5).hex(), 0)
    process = int("0x" + urandom(5).hex(), 0)
    increment = int("0x" + urandom(12).hex(), 0)

    return int((timestamp << 22) | (worker << 17) | (process << 12) | increment)


class FakeSlashContext(SlashContext):
    """
    A fake SlashContext class for testing

    This class is used to simulate a SlashContext object for testing purposes.
    It will avoid calling the Discord API and instead store the actions that would be taken in a list.
    It is meant to be used with the other fake classes in this module.
    """

    __slots__ = ("actions", "_fake_cache", "http")
    actions: tuple[BaseAction, ...]
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
        self.actions += (DeferAction(ephemeral=ephemeral),)

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
            files: Files to send, the path, bytes or File() instance,
                   defaults to None. You may have up to 10 files.
            file: Files to send, the path, bytes or File() instance,
                  defaults to None. You may have up to 10 files.
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
                "Attachments are not files. "
                "Attachments only contain metadata about the file, "
                "not the file itself - to send an attachment, "
                "you need to download it first. Check Attachment.url"
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
            self.actions += (SendAction(message=message_data),)
            message = Message.from_dict(deepcopy(message_data), self.client)
            self._fake_cache[message.id] = message
            return message
        else:
            raise ValueError("Cannot send an empty message")

    respond = send

    async def delete(self, message: "Snowflake_Type" = "@original") -> None:
        """
        Delete a message sent in response to this interaction.

        Args:
            message: The message id to delete.
        """
        self.actions += (DeleteAction(message_id=to_snowflake(message) if message != "@original" else message),)
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
            self.actions += (EditAction(message=message_data),)
            self._fake_cache[message_data["id"]] = Message.from_dict(
                deepcopy(message_data), self.client
            )
            return Message.from_dict(deepcopy(message_data), self.client)

    async def send_modal(self, modal: interactions.Modal) -> dict | interactions.Modal:
        if self.responded:
            raise RuntimeError("Cannot send modal after responding")
        payload = modal if isinstance(modal, dict) else modal.to_dict()

        self.actions += (SendModalAction(modal=payload),)
        return modal

class FakeAutoCompleteContext(FakeSlashContext):
    fake_input_text: str

    @property
    def input_text(self) -> str:
        return self.fake_input_text
    
    def __init__(self, client: "interactions.Client", input_text: str):
        super().__init__(client)
        self.fake_input_text = input_text

    async def send(
        self, choices: typing.Iterable[str | int | float | dict[str, int | float | str] | SlashCommandChoice]
    ) -> None:
        """
        Send your autocomplete choices to discord. Choices must be either a list of strings, or a dictionary following the following format:

        ```json
            {
              "name": str,
              "value": str
            }
        ```
        Where name is the text visible in Discord, and value is the data sent back to your client when that choice is
        chosen.

        Args:
            choices: 25 choices the user can pick
        """
        if len(choices) > 25:
            raise ValueError("You can only send 25 choices at a time")
        processed_choices = []
        for choice in choices:
            if isinstance(choice, dict):
                name = choice["name"]
                value = choice["value"]
            elif isinstance(choice, SlashCommandChoice):
                name = choice.name.get_locale(self.locale)
                value = choice.value
            else:
                name = str(choice)
                value = choice

            processed_choices.append({"name": name, "value": value})
        print('#'*25)
        print(processed_choices)
        print(choices)
        print('#'*25)
        self.actions += (SendChoicesAction(choices=deepcopy(processed_choices)),)

class FakeComponentContext(FakeSlashContext):
    fake_custom_id: str
    fake_message: "Message"

    @property
    def custom_id(self) -> str:
        return self.fake_custom_id

    @property
    def message(self) -> "Message":
        return self.fake_message

    def __init__(self, client: "interactions.Client", custom_id: str, message: "Message"=None):
        super().__init__(client)
        self.fake_custom_id = custom_id
        self.fake_message = message

class FakeGuild(Guild):
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
    fake_roles: list["FakeRole"] = []

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

    async def delete_message(self, message: "Snowflake_Type") -> None:
        self.client.http.delete_message(self.id, message.id)
        self.client.actions += (DeleteAction(message_id=message.id),)

    def get_message(self, message_id: "Snowflake_Type") -> "Message":
        return self.client._fake_cache[to_snowflake(message_id)]

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

    def __init__(self, *args, **kwargs):
        self._fake_cache = {}
        self.actions = ()
        super().__init__(*args, **kwargs)
        self.http = FakeHttp(client=self)

    def __del__(self):
        self._fake_cache.clear()
        del self._fake_cache


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
        self.actions += (DeleteAction(message_id=to_snowflake(message_id)),)
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
        self.actions += (EditAction(message=message.to_dict()),)
        return message

    async def create_reaction(
        self, channel_id: "Snowflake_Type", message_id: "Snowflake_Type", emoji: str
    ) -> None:
        self._fake_cache[to_snowflake(message_id)].reactions.append(emoji)
        self.actions += (CreateReactionAction(message_id=to_snowflake(message_id), emoji=emoji),)


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

    client = _client or FakeClient()
    if hasattr(func, "scopes") and all(
        func.resolved_name not in client.interactions_by_scope.get(scope,{})
        for scope in func.scopes
    ):
        client.add_interaction(func)
    ctx = FakeSlashContext(client)
    for key, value in kwargs.items():
        if key.startswith("test_ctx_"):
            setattr(ctx, key.split("test_ctx_", 1)[1], value)

    ctx.args = args
    ctx.kwargs = {
        key: value for key, value in kwargs.items() if not key.startswith("test_ctx")
    }
    start_time = time.time()
    await func(ctx, *args, **kwargs)


    return sorted(
        [action for action in list(ctx.actions+client.actions) if action.creation_time >= start_time],
        key=lambda x: x.creation_time)

async def call_autocomplete(
    func: typing.Callable, *args,input_text:str, _client: FakeClient = None,  **kwargs
):
    """
    Call an autocomplete function with the given arguments.
    """
    client = _client or FakeClient()

    ctx = FakeAutoCompleteContext(client, input_text)
    ctx.args = args
    for key, value in kwargs.items():
        if key.startswith("test_ctx_"):
            setattr(ctx, key.split("test_ctx_", 1)[1], value)

    ctx.args = args
    ctx.kwargs = {
        key: value for key, value in kwargs.items() if not key.startswith("test_ctx")
    }
    kwargs = {
        key: value for key, value in kwargs.items() if not key.startswith("test_ctx")
    }
    start_time = time.time()
    await func(client,ctx, *args, **kwargs)


    return sorted(
        [action for action in list(ctx.actions+client.actions) if action.creation_time >= start_time],
        key=lambda x: x.creation_time)

async def call_component(
    func: typing.Callable, *args, _client: FakeClient = None, **kwargs
):
    """
    Call a component function with the given arguments.

    :param func: The function to call.
    :param _client: A FakeClient instance to use.
    :param args: The positional arguments to pass to the function.
    :param kwargs: The keyword arguments to pass to the function.
    :return:
    """

    # default_kwargs

    client = _client or FakeClient()
    if all(
        func.resolved_name not in client.interactions_by_scope.get(scope,{})
        for scope in func.scopes
    ):
        client.add_interaction(func)

    source_message = kwargs.pop("test_ctx_message")
    source_message = Message.from_dict(deepcopy(source_message), client) if isinstance(source_message, dict) else source_message
    ctx = FakeComponentContext(client, kwargs.pop("test_ctx_custom_id"), source_message)

    ctx.args = args
    for key, value in kwargs.items():
        if key.startswith("test_ctx_"):
            setattr(ctx, key.split("test_ctx_", 1)[1], value)

    ctx.args = args
    ctx.kwargs = {
        key: value for key, value in kwargs.items() if not key.startswith("test_ctx")
    }
    start_time = time.time()
    await func(ctx, *args, **kwargs)


    return sorted(
        [action for action in list(ctx.actions+client.actions) if action.creation_time >= start_time],
        key=lambda x: x.creation_time)


def get_client() -> FakeClient:
    """Returns a FakeClient instance.

    :return: A FakeClient instance.
    """
    return FakeClient()
