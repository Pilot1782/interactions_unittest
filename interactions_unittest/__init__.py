"""
# About

This package allows you to test you discord bot's commands without having to run the bot itself.
It is made to be a drop-in library to be used with unittest or pytest.

## Installation

```bash
pip install interactions-unittest
```

## Usage

```python
import unittest

import interactions

import interactions_unittest as itest
from interactions_unittest import ActionType

@interactions.SlashCommand(
    name="ping",
    description="Replies with pong",
    options=[
        interactions.Option(
            name="extra",
            description="extra text",
            type=interactions.OptionType.STRING,
            required=False
        )
    ]
)
async def ping(ctx: interactions.SlashContext, extra: str = None):
    await ctx.send(f"Pong! {extra}")


class TestPing(unittest.IsolatedAsyncioTestCase):
    async def test_ping(self):
        actions = await itest.call_slash(ping, extra="extra text")
        self.assertTrue(actions[0].action_type == ActionType.SEND, f"Action 0: {actions[0]}")
        self.assertTrue(actions[0].message["content"] == "Pong! extra text")
```
"""

import time
import typing
from copy import deepcopy

from interactions import Message

from .actions import (
    ActionType,
    BaseAction,
    CreateReactionAction,
    DeferAction,
    DeleteAction,
    EditAction,
    SendAction,
    SendChoicesAction,
    SendModalAction,
)
from .helpers import random_snowflake
from .fake_models import FakeClient, FakeGuild, FakeMember, FakeRole, FakeChannel
from .fake_contexts import (
    FakeAutoCompleteContext,
    FakeComponentContext,
    FakeSlashContext,
)

# dummy usage to suppress flake8 error
_ = ActionType
_ = BaseAction
_ = CreateReactionAction
_ = DeferAction
_ = DeleteAction
_ = EditAction
_ = SendAction
_ = SendChoicesAction
_ = SendModalAction
_ = random_snowflake
_ = FakeClient
_ = FakeGuild
_ = FakeMember
_ = FakeRole
_ = FakeChannel
_ = FakeAutoCompleteContext


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
    client = _client or FakeClient()
    if hasattr(func, "scopes") and all(
        func.resolved_name not in client.interactions_by_scope.get(scope, {})
        for scope in func.scopes
    ):
        client.add_interaction(func)
    ctx = FakeSlashContext(client)
    kwargs = organize_kwargs(args, kwargs, ctx)
    start_time = time.time()
    await func(ctx, *args, **kwargs)

    return sorted(
        [
            action
            for action in list(ctx.actions + client.actions)
            if action.creation_time >= start_time
        ],
        key=lambda x: x.creation_time,
    )


async def call_autocomplete(
    func: typing.Callable, *args, input_text: str, _client: FakeClient = None, **kwargs
):
    """Call an autocomplete function with the given arguments."""
    client = _client or FakeClient()

    ctx = FakeAutoCompleteContext(client, input_text)
    kwargs = organize_kwargs(args, kwargs, ctx)
    start_time = time.time()
    await func(client, ctx, *args, **kwargs)

    return sorted(
        [
            action
            for action in list(ctx.actions + client.actions)
            if action.creation_time >= start_time
        ],
        key=lambda x: x.creation_time,
    )


def organize_kwargs(args: tuple, kwargs: dict[str, typing.Any], ctx: FakeSlashContext):
    """
    Organize the keyword arguments.

    Keyword arguments that start with "test_ctx_" will be set as attributes (without prefix) of
    the context object and removed from the kwargs.

    :param args: The positional arguments.
    :param kwargs: The keyword arguments.
    :param ctx: The context object.
    """
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
    return kwargs


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
    client = _client or FakeClient()
    if all(
        func.resolved_name not in client.interactions_by_scope.get(scope, {})
        for scope in func.scopes
    ):
        client.add_interaction(func)

    source_message = kwargs.pop("test_ctx_message")
    source_message = (
        Message.from_dict(deepcopy(source_message), client)
        if isinstance(source_message, dict)
        else source_message
    )
    ctx = FakeComponentContext(client, kwargs.pop("test_ctx_custom_id"), source_message)
    kwargs = organize_kwargs(args, kwargs, ctx)
    start_time = time.time()
    await func(ctx, *args, **kwargs)

    return sorted(
        [
            action
            for action in list(ctx.actions + client.actions)
            if action.creation_time >= start_time
        ],
        key=lambda x: x.creation_time,
    )


def get_client() -> FakeClient:
    """Returns a new FakeClient instance."""
    return FakeClient()
