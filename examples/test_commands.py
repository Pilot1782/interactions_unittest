""" This module contains the unit tests for the commands module. """
import unittest

from commands import (
    example_slash,
    MyExtension,
    list_channel_slash,
    list_role_slash,
    list_member_slash,
)
from interactions_unittest import ActionType, call_slash, get_client, FakeGuild


class TestCommands(unittest.IsolatedAsyncioTestCase):
    """ The unit tests for the commands module. """

    async def test_example_slash(self):
        """ Test the example slash command. """
        actions = await call_slash(example_slash, option="test")

        self.assertTrue(len(actions) == 4)
        self.assertTrue(actions[0].action_type == ActionType.DEFER, f"Action 0: {actions[0]}")
        self.assertTrue(actions[1].action_type == ActionType.SEND, f"Action 1: {actions[1]}")
        self.assertTrue(actions[2].action_type == ActionType.EDIT, f"Action 2: {actions[2]}")
        self.assertTrue(actions[3].action_type == ActionType.DELETE, f"Action 3: {actions[3]}")

    async def test_list_channel_slash(self):
        """ Test the list channel slash command. """
        client = get_client()
        fake_guild = FakeGuild(
            client=client,
            channel_names={"welcome": [], "smalltalk": [], "general": []},
            role_names=[],
            member_names={},
        )

        self.assertIsNotNone(fake_guild, "FakeGuild is None")
        actions = await call_slash(
            list_channel_slash,
            _client=client,
            test_ctx_guild=fake_guild,
            test_ctx_channel=fake_guild.channels[0],
        )

        self.assertTrue(len(actions) == 2)
        self.assertTrue(actions[0].action_type == ActionType.DEFER, f"Action 0: {actions[0]}")
        self.assertTrue(actions[1].action_type == ActionType.SEND, f"Action 1: {actions[1]}")
        self.assertTrue(
            "Channels" in actions[1].message["content"], f"Action 1: {actions[1]}"
        )
        self.assertTrue(
            len(actions[1].message["content"].split("\n")) == 4,
            f'Action 1: {actions[1].message["content"]}',
        )

    async def test_list_role_slash(self):
        """ Test the list role slash command. """
        client = get_client()
        fake_guild = FakeGuild(
            client=client,
            channel_names={"welcome": [], "smalltalk": [], "general": []},
            role_names=["admin", "mod", "user"],
            member_names={},
        )

        self.assertIsNotNone(fake_guild, "FakeGuild is None")
        actions = await call_slash(
            list_role_slash,
            test_ctx_guild=fake_guild,
            test_ctx_channel=fake_guild.channels[0],
        )

        self.assertTrue(len(actions) == 2)
        self.assertTrue(actions[0].action_type == ActionType.DEFER, f"Action 0: {actions[0]}")
        self.assertTrue(actions[1].action_type == ActionType.SEND, f"Action 1: {actions[1]}")
        self.assertTrue("Roles" in actions[1].message["content"], f"Action 1: {actions[1]}")
        self.assertTrue(
            len(actions[1].message["content"].split("\n")) == 4,
            f'Action 1: {actions[1].message["content"]}',
        )

    async def test_list_member_slash(self):
        """ Test the list member slash command. """
        client = get_client()
        fake_guild = FakeGuild(
            client=client,
            channel_names={"welcome": [], "smalltalk": [], "general": []},
            role_names=["admin", "mod", "user"],
            member_names={
                "user1": ["user", "admin"],
                "user2": ["user"],
                "user3": ["user"],
            },
        )

        self.assertIsNotNone(fake_guild, "FakeGuild is None")
        actions = await call_slash(
            list_member_slash,
            test_ctx_guild=fake_guild,
            test_ctx_channel=fake_guild.channels[0],
        )

        self.assertTrue(len(actions) == 2)
        self.assertTrue(actions[0].action_type == ActionType.DEFER, f"Action 0: {actions[0]}")
        self.assertTrue(actions[1].action_type == ActionType.SEND, f"Action 1: {actions[1]}")
        self.assertTrue(
            "Members" in actions[1].message["content"], f"Action 1: {actions[1]}"
        )
        self.assertTrue(
            len(actions[1].message["content"].split("\n")) == 4,
            f'Action 1: {actions[1].message["content"]}',
        )

    async def test_extension_ping(self):
        """ Test the extension class with the ping slash command. """
        bot = get_client()
        bot.load_extension("commands")

        actions = await call_slash(MyExtension.ping_slash, _client=bot, option="test")

        self.assertTrue(len(actions) == 3)
        self.assertTrue(actions[0].action_type == ActionType.DEFER, f"Action 0: {actions[0]}")
        self.assertTrue(actions[1].action_type == ActionType.SEND, f"Action 1: {actions[1]}")
        self.assertTrue(actions[2].action_type == ActionType.EDIT, f"Action 2: {actions[2]}")
