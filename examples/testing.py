import asyncio
import json

from interactions import (
    slash_command,
    SlashContext,
    SlashCommandOption,
    OptionType, Embed,
)

import interactions_unittest as itest


@slash_command(
    name="test",
    description="Test command",
    options=[
        SlashCommandOption(
            name="option",
            description="Test option",
            type=OptionType.STRING,
            required=True,
        )
    ],
)
async def test_slash(ctx: SlashContext, option: str = None) -> None:
    await ctx.defer(ephemeral=True)

    embed = Embed(
        title="Test",
        description=f"Hello, World! You chose {option} as your option.",
        color=0x00FF00,
    )
    msg = await ctx.send(f"Hello, World! You chose {option} as your option.", embed=embed)

    await msg.edit(content=f"The message has changed! You chose {option} as your option.", context=ctx)

    await ctx.delete(msg)


async def test():
    actions = await itest.call_slash(test_slash, option="test")

    for act in actions:
        print(json.dumps(act, indent=4))


if __name__ == "__main__":
    asyncio.run(test())
