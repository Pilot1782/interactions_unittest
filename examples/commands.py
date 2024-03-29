import interactions
from interactions import (
    slash_command,
    SlashContext,
    SlashCommandOption,
    OptionType, Embed,
)


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

    await msg.delete(context=ctx)


class MyExtension(interactions.Extension):
    @interactions.slash_command(
        name="ping",
        description="Ping command",
        options=[
            interactions.SlashCommandOption(
                name="option",
                description="Test option",
                type=interactions.OptionType.STRING,
                required=True,
            )
        ],
    )
    async def ping_slash(self, ctx: interactions.SlashContext, option: str = None) -> None:
        await ctx.defer(ephemeral=True)

        msg = await ctx.send(f"Please hold...")

        await msg.edit(context=ctx, embed=interactions.Embed(
            title="Pong!",
            description=f"Hello, World! You chose {option} as your option.",
            color=0x00FF00,
        ))
