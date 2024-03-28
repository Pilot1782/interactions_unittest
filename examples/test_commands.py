import unittest

from commands import test_slash, MyExtension
from interactions_unittest import call_slash, get_client


class TestCommands(unittest.IsolatedAsyncioTestCase):
    async def test_test_slash(self):
        actions = await call_slash(test_slash, option="test")

        self.assertTrue(len(actions) == 4)
        self.assertTrue(actions[0]["action"] == "defer", f'Action 0: {actions[0]}')
        self.assertTrue(actions[1]["action"] == "send", f'Action 1: {actions[1]}')
        self.assertTrue(actions[2]["action"] == "edit", f'Action 2: {actions[2]}')
        self.assertTrue(actions[3]["action"] == "delete", f'Action 3: {actions[3]}')

    async def test_extension(self):
        bot = get_client()
        bot.load_extension("commands")

        actions = await call_slash(MyExtension.ping_slash, _client=bot, option="test")

        self.assertTrue(len(actions) == 2)
        self.assertTrue(actions[0]["action"] == "defer", f'Action 0: {actions[0]}')
        self.assertTrue(actions[1]["action"] == "send", f'Action 1: {actions[1]}')
