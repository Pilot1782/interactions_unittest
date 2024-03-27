import json
import unittest
from interactions_unittest import call_slash
from commands import test_slash


class TestCommands(unittest.IsolatedAsyncioTestCase):
    async def test_test_slash(self):

        actions = await call_slash(test_slash, option="test")

        for act in actions:
            print(json.dumps(act, indent=4))
