"""Example commands"""

import interactions
from interactions import (
    slash_command,
    SlashContext,
    SlashCommandOption,
    OptionType,
    Embed,
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
async def example_slash(ctx: SlashContext, option: str = None) -> None:
    """Example command"""
    await ctx.defer(ephemeral=True)

    embed = Embed(
        title="Test",
        description=f"Hello, World! You chose {option} as your option.",
        color=0x00FF00,
    )
    msg = await ctx.send(
        f"Hello, World! You chose {option} as your option.", embed=embed
    )

    await msg.edit(
        content=f"The message has changed! You chose {option} as your option.",
        context=ctx,
    )

    await msg.delete(context=ctx)


@slash_command(
    name="list_channel",
    description="List channel command",
)
async def list_channel_slash(ctx: SlashContext) -> None:
    """List channel command"""
    await ctx.defer(ephemeral=True)

    channels = ctx.guild.channels
    channel_list = "\n".join([f"{channel.name} ({channel.id})" for channel in channels])

    await ctx.send(
        f"Channels in {ctx.guild_id} {ctx.guild.name}:\n{channel_list}", ephemeral=True
    )


@slash_command(
    name="list_role",
    description="List role command",
)
async def list_role_slash(ctx: SlashContext) -> None:
    """List role command"""
    await ctx.defer(ephemeral=True)

    roles = ctx.guild.roles
    role_list = "\n".join([f"{role.name} ({role.id})" for role in roles])

    await ctx.send(f"Roles:\n{role_list}", ephemeral=True)


@slash_command(
    name="list_member",
    description="List member command",
)
async def list_member_slash(ctx: SlashContext) -> None:
    """List member command"""
    await ctx.defer(ephemeral=True)

    members = ctx.guild.members
    member_list = "\n".join(
        [f"{member.display_name} ({member.id})" for member in members]
    )

    await ctx.send(f"Members:\n{member_list}", ephemeral=True)


class MyExtension(interactions.Extension):
    """My extension class"""

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
    async def ping_slash(
        self, ctx: interactions.SlashContext, option: str = None
    ) -> None:
        """Ping command"""
        await ctx.defer(ephemeral=True)

        msg = await ctx.send("Please hold...")

        await msg.edit(
            context=ctx,
            embed=interactions.Embed(
                title="Pong!",
                description=f"Hello, World! You chose {option} as your option.",
                color=0x00FF00,
            ),
        )
