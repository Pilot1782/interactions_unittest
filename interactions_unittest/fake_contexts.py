"""Fake context classes for testing purposes."""

import typing
from copy import deepcopy

import interactions
from interactions import (
    UPLOADABLE_TYPE,
    AllowedMentions,
    Attachment,
    BaseComponent,
    Embed,
    Message,
    MessageFlags,
    MessageReference,
    SlashCommandChoice,
    SlashContext,
    Snowflake_Type,
    Sticker,
    models,
    process_message_payload,
    to_snowflake,
)

from .actions import (
    BaseAction,
    DeferAction,
    DeleteAction,
    EditAction,
    SendAction,
    SendChoicesAction,
    SendModalAction,
)
from .helpers import random_snowflake, fake_process_files
from .fake_models import FakeChannel, FakeGuild, FakeMember


class FakeSlashContext(SlashContext):
    """
    A fake SlashContext class for testing

    This class is used to simulate a SlashContext object for testing purposes.
    It will avoid calling the Discord API and instead store the actions that
    would be taken in a list. It is meant to be used with the other fake classes
    in this module.
    """

    __slots__ = ("actions", "_fake_cache", "http")
    actions: tuple[BaseAction, ...]
    fake_guild: typing.Optional[FakeGuild] = None

    @property
    def guild(self) -> typing.Optional[FakeGuild]:
        return self.fake_guild

    @guild.setter
    def guild(self, value: typing.Optional[FakeGuild]):
        self.fake_guild = value
        self.guild_id = value.id

    fake_channel: typing.Optional[FakeChannel] = None

    @property
    def channel(self) -> typing.Optional[FakeChannel]:
        return self.fake_channel

    @channel.setter
    def channel(self, value: typing.Optional[FakeChannel]):
        self.fake_channel = value
        self.channel_id = value.id

    fake_author: typing.Optional[FakeMember] = None

    @property
    def author(self) -> typing.Optional[FakeMember]:
        return self.fake_author

    @author.setter
    def author(self, value: typing.Optional[FakeMember]):
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
                typing.Iterable[typing.Iterable[typing.Union[BaseComponent, dict]]],
                typing.Iterable[typing.Union[BaseComponent, dict]],
                BaseComponent,
                dict,
            ]
        ] = None,
        stickers: typing.Optional[
            typing.Union[
                typing.Iterable[typing.Union[Sticker, "Snowflake_Type"]],
                Sticker,
                "Snowflake_Type",
            ]
        ] = None,
        allowed_mentions: typing.Optional[typing.Union[AllowedMentions, dict]] = None,
        reply_to: typing.Optional[
            typing.Union[MessageReference, Message, dict, "Snowflake_Type"]
        ] = None,
        files: typing.Optional[
            typing.Union[UPLOADABLE_TYPE, typing.Iterable[UPLOADABLE_TYPE]]
        ] = None,
        file: typing.Optional[UPLOADABLE_TYPE] = None,
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
        flags = self.fake_process_flags(suppress_embeds, silent, flags, ephemeral)
        fake_process_files(files, file)

        if delete_after is not None:
            print("delete_after is not supported in FakeSlashContext.send yet")

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

        self.deconstruct_embeds(message_data)

        if message_data:
            self.actions += (SendAction(message=message_data),)
            message = Message.from_dict(deepcopy(message_data), self.client)
            self._fake_cache[message.id] = message
            return message
        raise ValueError("Cannot send an empty message")

    @staticmethod
    def deconstruct_embeds(message_data):
        """Deconstruct the embeds in the message data."""
        if "embeds" in message_data:
            message_data["embeds"] = [
                embed.to_dict() if isinstance(embed, Embed) else embed
                for embed in message_data["embeds"]
            ]

    def fake_process_flags(self, suppress_embeds, silent, flags, ephemeral):
        """Construct the flags."""
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
        return flags

    respond = send

    async def delete(self, message: "Snowflake_Type" = "@original") -> None:
        """
        Delete a message sent in response to this interaction.

        Args:
            message: The message id to delete.
        """
        self.actions += (
            DeleteAction(
                message_id=to_snowflake(message) if message != "@original" else message
            ),
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
                typing.Iterable[typing.Iterable[typing.Union[BaseComponent, dict]]],
                typing.Iterable[typing.Union[BaseComponent, dict]],
                BaseComponent,
                dict,
            ]
        ] = None,
        attachments: typing.Optional[typing.Sequence[Attachment | dict]] = None,
        allowed_mentions: typing.Optional[typing.Union[AllowedMentions, dict]] = None,
        files: typing.Optional[
            typing.Union[UPLOADABLE_TYPE, typing.Iterable[UPLOADABLE_TYPE]]
        ] = None,
        file: typing.Optional[UPLOADABLE_TYPE] = None,
        tts: bool = False,
    ) -> "interactions.Message":
        """Edit a message sent in response to this interaction."""
        fake_process_files(files, file)
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
        """Send a modal to the user."""
        if self.responded:
            raise RuntimeError("Cannot send modal after responding")
        payload = modal if isinstance(modal, dict) else modal.to_dict()

        self.actions += (SendModalAction(modal=payload),)
        return modal


class FakeAutoCompleteContext(FakeSlashContext):
    """
    A fake AutoCompleteContext class for testing

    For simplicity, this class is a subclass of FakeSlashContext instead of BaseInteractionContext.
    """

    fake_input_text: str

    @property
    def input_text(self) -> str:
        """Override the input_text property to return the fake input text."""
        return self.fake_input_text

    def __init__(self, client: "interactions.Client", input_text: str):
        super().__init__(client)
        self.fake_input_text = input_text

    async def send_choices(
        self,
        choices: typing.Iterable[
            str | int | float | dict[str, int | float | str] | SlashCommandChoice
        ],
    ) -> None:
        """
        Send your autocomplete choices to discord.

        Choices must be either a list of strings, or a dictionary following the following format:

        ```json
            {
              "name": str,
              "value": str
            }
        ```
        Where name is the text visible in Discord, and value is the data sent back to your client
        when that choice is chosen.

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
        self.actions += (SendChoicesAction(choices=deepcopy(processed_choices)),)

    send = send_choices


class FakeComponentContext(FakeSlashContext):
    """A fake ComponentContext class for testing"""

    fake_custom_id: str
    fake_message: "Message"

    @property
    def custom_id(self) -> str:
        """Override the custom_id property to return the fake custom id."""
        return self.fake_custom_id

    @property
    def message(self) -> "Message":
        return self.fake_message

    def __init__(
        self, client: "interactions.Client", custom_id: str, message: "Message" = None
    ):
        super().__init__(client)
        self.fake_custom_id = custom_id
        self.fake_message = message
