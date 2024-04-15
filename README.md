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
        self.assertTrue(actions[0].action_type == itest.ActionType.SEND)
        self.assertTrue(actions[0].message["content"] == "Pong! extra text")
```

## Documentation

The `call_slash` method allows you to call a slash command with arguments, it will return a list of actions.
The `call_component` method allows you to call a component interaction, it will return a list of actions.
The `call_autocomplete` method allows you to call an autocomplete interaction, it will return a list of actions.

Each action has an `action_type` attribute that can be used to determine the type of action an a `creation_time` attribute that can be used to determine the order of the actions. For each action there is a subclass containing the data of the action.

## Features
- [X] context.edit message
- [X] context.delete message
- [X] context.send message
- [X] context.defer
- [X] context.send_modal
- [X] channel.get_message
- [X] channel.delete_message
- [X] component interaction
- [X] autocomplete interaction
- [X] message.delete
- [X] message.edit
- [X] message.reply
- [X] message.react
- [X] extensions

## TODO
- [ ] Add more examples
