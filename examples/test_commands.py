import unittest

from commands import (
    test_slash,
    MyExtension,
    list_channel_slash,
    list_role_slash,
    list_member_slash,
)
from interactions_unittest import call_slash, get_client, FakeGuild


class TestCommands(unittest.IsolatedAsyncioTestCase):
    async def test_test_slash(self):
        actions = await call_slash(test_slash, option="test")

        self.assertTrue(len(actions) == 4)
        self.assertTrue(actions[0]["action"] == "defer", f"Action 0: {actions[0]}")
        self.assertTrue(actions[1]["action"] == "send", f"Action 1: {actions[1]}")
        self.assertTrue(actions[2]["action"] == "edit", f"Action 2: {actions[2]}")
        self.assertTrue(actions[3]["action"] == "delete", f"Action 3: {actions[3]}")

    async def test_list_channel_slash(self):
        fake_guild = FakeGuild(
            channel_names={"welcome": [], "smalltalk": [], "general": []}
        )

        self.assertIsNotNone(fake_guild, "FakeGuild is None")
        actions = await call_slash(
            list_channel_slash,
            test_ctx_guild=fake_guild,
            test_ctx_channel=fake_guild.channels[0],
        )

        self.assertTrue(len(actions) == 2)
        self.assertTrue(actions[0]["action"] == "defer", f"Action 0: {actions[0]}")
        self.assertTrue(actions[1]["action"] == "send", f"Action 1: {actions[1]}")
        self.assertTrue(
            "Channels" in actions[1]["message"]["content"], f"Action 1: {actions[1]}"
        )
        self.assertTrue(
            len(actions[1]["message"]["content"].split("\n")) == 4,
            f'Action 1: {actions[1]["message"]["content"]}',
        )

    async def test_list_role_slash(self):
        fake_guild = FakeGuild(
            channel_names={"welcome": [], "smalltalk": [], "general": []},
            role_names=["admin", "mod", "user"],
        )

        self.assertIsNotNone(fake_guild, "FakeGuild is None")
        actions = await call_slash(
            list_role_slash,
            test_ctx_guild=fake_guild,
            test_ctx_channel=fake_guild.channels[0],
        )

        self.assertTrue(len(actions) == 2)
        self.assertTrue(actions[0]["action"] == "defer", f"Action 0: {actions[0]}")
        self.assertTrue(actions[1]["action"] == "send", f"Action 1: {actions[1]}")
        self.assertTrue(
            "Roles" in actions[1]["message"]["content"], f"Action 1: {actions[1]}"
        )
        self.assertTrue(
            len(actions[1]["message"]["content"].split("\n")) == 4,
            f'Action 1: {actions[1]["message"]["content"]}',
        )

    async def test_list_member_slash(self):
        fake_guild = FakeGuild(
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
        self.assertTrue(actions[0]["action"] == "defer", f"Action 0: {actions[0]}")
        self.assertTrue(actions[1]["action"] == "send", f"Action 1: {actions[1]}")
        self.assertTrue(
            "Members" in actions[1]["message"]["content"], f"Action 1: {actions[1]}"
        )
        self.assertTrue(
            len(actions[1]["message"]["content"].split("\n")) == 4,
            f'Action 1: {actions[1]["message"]["content"]}',
        )

    async def test_extension(self):
        bot = get_client()
        bot.load_extension("commands")

        actions = await call_slash(MyExtension.ping_slash, _client=bot, option="test")

        self.assertTrue(len(actions) == 3)
        self.assertTrue(actions[0]["action"] == "defer", f"Action 0: {actions[0]}")
        self.assertTrue(actions[1]["action"] == "send", f"Action 1: {actions[1]}")
        self.assertTrue(actions[2]["action"] == "edit", f"Action 2: {actions[2]}")
