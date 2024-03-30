import datetime
import typing
from copy import deepcopy
from os import urandom

import interactions
from interactions import (
    UPLOADABLE_TYPE,
    AllowedMentions,
    Attachment,
    BaseComponent,
    Client,
    Embed,
    Message,
    MessageFlags,
    MessageReference,
    SlashContext,
    Snowflake_Type,
    Sticker,
    models,
    process_message_payload,
    to_snowflake,
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
    """
    A fake SlashContext class for testing

    This class is used to simulate a SlashContext object for testing purposes.
    It will avoid calling the Discord API and instead store the actions that would be taken in a list.
    It is meant to be used with the other fake classes in this module.
    """

    __slots__ = ("actions", "_fake_cache", "http")

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
            self.actions += ({"action": "send", "message": message_data},)
            message = Message.from_dict(deepcopy(message_data), self.client)
            self._fake_cache[message.id] = message

            return message

    respond = send

    async def delete(self, message: "Snowflake_Type" = "@original") -> None:
        """
        Delete a message sent in response to this interaction.

        Args:
            message: The message id to delete.
        """
        self.actions += (
            {
                "action": "delete",
                "message_id": (
                    to_snowflake(message) if message != "@original" else message
                ),
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


class FakeClient(Client):
    """
    A fake Client class for testing

    This class is used to simulate a Client object for testing purposes.
    It will override the HTTPClient object with a FakeHttp object
    to bypass the discord api and store the actions that would be taken in a list.
    """

    __slots__ = ("_fake_cache", "actions")

    def __init__(self, *args, **kwargs):
        self._fake_cache = {}
        self.actions = ()
        super().__init__(*args, **kwargs)
        self.http = FakeHttp(client=self)


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
    ctx.args = args
    ctx.kwargs = kwargs

    await func(ctx, *args, **kwargs)

    return deepcopy(ctx.actions)


def get_client() -> FakeClient:
    """Returns a FakeClient instance.

    :return: A FakeClient instance.
    """

    return FakeClient()
