import asyncio
from datetime import timedelta
from typing import Literal, Optional

import discord
from discord import app_commands
from discord.ext import commands

from config import TOKEN
from enlightenme import get_quote
from faction_intros_embed import response_embed
from helpme import help_embed
from imbored import joke_response
from moderation_logic import evaluate_exemption
from moderation_store import ModerationStore, render_member_template
from profanity_checker import profanity_check


store = ModerationStore()
store.initialize()


def has_manage_guild(member: discord.Member) -> bool:
    perms = member.guild_permissions
    return perms.manage_guild or perms.administrator


def has_moderation_perms(member: discord.Member) -> bool:
    perms = member.guild_permissions
    return (
        perms.moderate_members
        or perms.manage_messages
        or perms.manage_guild
        or perms.administrator
    )


def is_exempt(member: discord.Member, settings) -> bool:
    return evaluate_exemption(
        mode=str(settings["exemption_mode"]),
        exempt_role_id=settings["exempt_role_id"],
        user_role_ids=[role.id for role in member.roles],
        is_moderator=has_moderation_perms(member),
    )


async def ensure_guild_interaction(interaction: discord.Interaction) -> bool:
    if interaction.guild is None:
        await interaction.response.send_message(
            "This command can only be used in a server.", ephemeral=True
        )
        return False
    return True


class BotClient(commands.Bot):
    async def on_ready(self):
        print("Unlucky_luke ready")
        try:
            store.initialize()
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} commands")
        except Exception as e:
            print(f"Unlucky_luke ran into an error: {e}")

    async def on_member_join(self, member: discord.Member):
        try:
            await send_welcome_for_member(member)
        except Exception as e:
            print(f"Failed welcome flow for guild={member.guild.id}: {e}")

    async def on_message(self, message: discord.Message):
        if message.author == self.user or message.author.bot:
            return

        msg = message.content.lower()

        if msg.startswith("hi luke"):
            await message.channel.send(
                f"Hello {message.author.display_name}, this is a 100 percent luke, there is no doubt to it, trust me :D"
            )

        if not profanity_check(msg):
            return

        if message.guild is None or not isinstance(message.author, discord.Member):
            return

        try:
            settings = store.ensure_guild_settings(message.guild.id)
            if is_exempt(message.author, settings):
                return

            store.add_warning(
                guild_id=message.guild.id,
                user_id=message.author.id,
                message_id=message.id,
                channel_id=message.channel.id,
                reason="profanity",
            )

            warning_count = store.count_active_warnings(
                message.guild.id,
                message.author.id,
                int(settings["warning_expiry_days"]),
            )
            threshold = int(settings["warn_threshold"])

            await message.reply(
                f"Please avoid profanity. Warning {warning_count}/{threshold} (active for {int(settings['warning_expiry_days'])} days)."
            )

            if warning_count >= threshold:
                timeout_minutes = int(settings["timeout_minutes"])
                timeout_until = discord.utils.utcnow() + timedelta(minutes=timeout_minutes)
                try:
                    await message.author.timeout(timeout_until, reason="Profanity threshold reached")
                    await message.channel.send(
                        f"{message.author.mention} has been timed out for {timeout_minutes} minute(s) due to repeated profanity."
                    )
                except discord.Forbidden:
                    await message.channel.send(
                        "I do not have permission to timeout this member."
                    )
                except discord.HTTPException as err:
                    await message.channel.send(
                        f"Failed to timeout member due to an API error: {err}"
                    )
        except Exception as e:
            print(f"Profanity moderation error in guild={message.guild.id}: {e}")


intents_list = discord.Intents.default()
intents_list.message_content = True
intents_list.members = True
client = BotClient(command_prefix="!", intents=intents_list)


async def send_welcome_for_member(member: discord.Member) -> tuple[bool, bool]:
    dm_sent = False
    channel_sent = False
    settings = store.ensure_guild_settings(member.guild.id)

    if settings["welcome_dm_enabled"]:
        dm_text = render_member_template(
            settings["welcome_dm_template"],
            member.mention,
            member.display_name,
            member.guild.name,
        )
        try:
            await member.send(dm_text)
            dm_sent = True
        except discord.Forbidden:
            dm_sent = False

    entry_channel_id = settings["entry_channel_id"]
    if entry_channel_id:
        channel = member.guild.get_channel(int(entry_channel_id))
        if channel and isinstance(channel, discord.TextChannel):
            join_text = render_member_template(
                settings["join_template"],
                member.mention,
                member.display_name,
                member.guild.name,
            )
            await channel.send(join_text)
            channel_sent = True

    return dm_sent, channel_sent


@client.tree.command(name="hello", description="say hello to Luke")
async def say_hello(interaction: discord.Interaction):
    await interaction.response.send_message(
        "hello!, this is a 100 percent luke, there is no doubt to it, trust me :D \n beware of anyone else claiming to be me, I've seen some around :eyes:"
    )


@client.tree.command(
    name="repeat",
    description="Have it say what you always wanted Luke to say! its the same thing! especially for legal purposes!",
)
async def repeat_whatever_message_says(interaction: discord.Interaction, repeat: str):
    await interaction.response.send_message(repeat)


@client.tree.command(name="faction_intro", description="get a snapshot of devlin factions from luke")
async def fruit(
    interaction: discord.Interaction,
    faction_name: Literal[
        "Brave survivors",
        "Flying cadets",
        "Jack of Trades",
        "Merciful Vanguards",
        "Rusty's ravagers",
        "School of Devlins",
    ],
):
    fembed = response_embed(faction_name)
    await interaction.response.send_message(embed=fembed)


@client.tree.command(
    name="enlightenme",
    description="luke sends you his words of enlightment, so you can transcend life",
)
async def enlightenme(interaction: discord.Interaction):
    quote = get_quote()
    await interaction.response.send_message(embed=quote)


@client.tree.command(name="imbored", description="luke will try to cheer you up")
async def imbored(interaction: discord.Interaction):
    joke = joke_response()
    await interaction.response.send_message(f"{joke[0]}")
    await asyncio.sleep(4)
    if joke[1]:
        await interaction.followup.send(joke[1] + " :rofl:")


@client.tree.command(name="set_entry_channel", description="Set the channel for join messages")
@app_commands.guild_only()
@app_commands.default_permissions(manage_guild=True)
@app_commands.describe(channel="Channel where join messages should be sent")
async def set_entry_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    if not await ensure_guild_interaction(interaction):
        return
    if not isinstance(interaction.user, discord.Member) or not has_manage_guild(interaction.user):
        await interaction.response.send_message(
            "You need Manage Server permission to use this command.",
            ephemeral=True,
        )
        return

    store.update_guild_settings(interaction.guild.id, entry_channel_id=channel.id)
    await interaction.response.send_message(
        f"Entry channel set to {channel.mention}.", ephemeral=True
    )


@client.tree.command(name="welcome_dm", description="Enable or disable welcome DMs")
@app_commands.guild_only()
@app_commands.default_permissions(manage_guild=True)
@app_commands.describe(enabled="Whether new members should receive welcome DMs")
async def welcome_dm(interaction: discord.Interaction, enabled: bool):
    if not await ensure_guild_interaction(interaction):
        return
    if not isinstance(interaction.user, discord.Member) or not has_manage_guild(interaction.user):
        await interaction.response.send_message(
            "You need Manage Server permission to use this command.",
            ephemeral=True,
        )
        return

    store.update_guild_settings(interaction.guild.id, welcome_dm_enabled=int(enabled))
    status = "enabled" if enabled else "disabled"
    await interaction.response.send_message(f"Welcome DMs are now {status}.", ephemeral=True)


@client.tree.command(
    name="set_welcome_templates",
    description="Set join channel and DM welcome templates",
)
@app_commands.guild_only()
@app_commands.default_permissions(manage_guild=True)
@app_commands.describe(
    join_text="Join message template ({user_mention}, {user_name}, {server})",
    dm_text="Welcome DM template ({user_mention}, {user_name}, {server})",
)
async def set_welcome_templates(
    interaction: discord.Interaction,
    join_text: Optional[str] = None,
    dm_text: Optional[str] = None,
):
    if not await ensure_guild_interaction(interaction):
        return
    if not isinstance(interaction.user, discord.Member) or not has_manage_guild(interaction.user):
        await interaction.response.send_message(
            "You need Manage Server permission to use this command.",
            ephemeral=True,
        )
        return

    if not join_text and not dm_text:
        await interaction.response.send_message(
            "Provide at least one template to update.", ephemeral=True
        )
        return

    updates = {}
    if join_text:
        updates["join_template"] = join_text
    if dm_text:
        updates["welcome_dm_template"] = dm_text

    try:
        _ = render_member_template(
            join_text or "{user_mention}",
            "@User",
            "SampleUser",
            interaction.guild.name,
        )
        _ = render_member_template(
            dm_text or "{user_mention}",
            "@User",
            "SampleUser",
            interaction.guild.name,
        )
    except KeyError:
        await interaction.response.send_message(
            "Invalid placeholder used. Allowed: {user_mention}, {user_name}, {server}.",
            ephemeral=True,
        )
        return

    store.update_guild_settings(interaction.guild.id, **updates)
    await interaction.response.send_message("Welcome templates updated.", ephemeral=True)


@client.tree.command(name="mod_settings", description="Set profanity moderation thresholds")
@app_commands.guild_only()
@app_commands.default_permissions(manage_guild=True)
@app_commands.describe(
    threshold="Warnings before timeout (1-10)",
    timeout_minutes="Timeout duration in minutes (1-1440)",
    expiry_days="Days before warnings expire (1-90)",
)
async def mod_settings(
    interaction: discord.Interaction,
    threshold: app_commands.Range[int, 1, 10],
    timeout_minutes: app_commands.Range[int, 1, 1440],
    expiry_days: app_commands.Range[int, 1, 90],
):
    if not await ensure_guild_interaction(interaction):
        return
    if not isinstance(interaction.user, discord.Member) or not has_manage_guild(interaction.user):
        await interaction.response.send_message(
            "You need Manage Server permission to use this command.",
            ephemeral=True,
        )
        return

    store.update_guild_settings(
        interaction.guild.id,
        warn_threshold=int(threshold),
        timeout_minutes=int(timeout_minutes),
        warning_expiry_days=int(expiry_days),
    )
    await interaction.response.send_message(
        f"Moderation settings updated: {threshold} warnings -> {timeout_minutes} minute timeout, expiry {expiry_days} day(s).",
        ephemeral=True,
    )


@client.tree.command(name="set_exemption", description="Configure profanity warning exemptions")
@app_commands.guild_only()
@app_commands.default_permissions(manage_guild=True)
@app_commands.describe(
    mode="Exemption mode",
    role="Role to exempt when mode is role",
)
async def set_exemption(
    interaction: discord.Interaction,
    mode: Literal["none", "admins_mods", "role"],
    role: Optional[discord.Role] = None,
):
    if not await ensure_guild_interaction(interaction):
        return
    if not isinstance(interaction.user, discord.Member) or not has_manage_guild(interaction.user):
        await interaction.response.send_message(
            "You need Manage Server permission to use this command.",
            ephemeral=True,
        )
        return

    updates = {"exemption_mode": mode, "exempt_role_id": None}
    if mode == "role":
        if role is None:
            await interaction.response.send_message(
                "You must provide a role when mode is role.", ephemeral=True
            )
            return
        updates["exempt_role_id"] = role.id

    store.update_guild_settings(interaction.guild.id, **updates)
    await interaction.response.send_message("Exemption settings updated.", ephemeral=True)


@client.tree.command(name="warnings", description="View a member's active warnings")
@app_commands.guild_only()
@app_commands.default_permissions(moderate_members=True)
@app_commands.describe(user="Member to inspect")
async def warnings(interaction: discord.Interaction, user: discord.Member):
    if not await ensure_guild_interaction(interaction):
        return
    if not isinstance(interaction.user, discord.Member) or not has_moderation_perms(interaction.user):
        await interaction.response.send_message(
            "You need moderation permissions to use this command.",
            ephemeral=True,
        )
        return

    settings = store.ensure_guild_settings(interaction.guild.id)
    count = store.count_active_warnings(
        interaction.guild.id,
        user.id,
        int(settings["warning_expiry_days"]),
    )
    latest = store.latest_warning_time(interaction.guild.id, user.id)
    latest_text = latest if latest else "No warnings found"

    await interaction.response.send_message(
        f"{user.mention} has {count} active warning(s). Latest warning: {latest_text}",
        ephemeral=True,
    )


@client.tree.command(name="clear_warnings", description="Clear all warnings for a member")
@app_commands.guild_only()
@app_commands.default_permissions(moderate_members=True)
@app_commands.describe(user="Member whose warnings should be cleared")
async def clear_warnings(interaction: discord.Interaction, user: discord.Member):
    if not await ensure_guild_interaction(interaction):
        return
    if not isinstance(interaction.user, discord.Member) or not has_moderation_perms(interaction.user):
        await interaction.response.send_message(
            "You need moderation permissions to use this command.",
            ephemeral=True,
        )
        return

    cleared = store.clear_warnings(interaction.guild.id, user.id)
    await interaction.response.send_message(
        f"Cleared {cleared} warning(s) for {user.mention}.", ephemeral=True
    )


@client.tree.command(
    name="test_welcome",
    description="Test welcome DM and entry-channel join message for a member",
)
@app_commands.guild_only()
@app_commands.default_permissions(manage_guild=True)
@app_commands.describe(member="Member to run welcome flow for (defaults to you)")
async def test_welcome(
    interaction: discord.Interaction,
    member: Optional[discord.Member] = None,
):
    if not await ensure_guild_interaction(interaction):
        return
    if not isinstance(interaction.user, discord.Member) or not has_manage_guild(interaction.user):
        await interaction.response.send_message(
            "You need Manage Server permission to use this command.",
            ephemeral=True,
        )
        return

    target = member or interaction.user
    dm_sent, channel_sent = await send_welcome_for_member(target)

    await interaction.response.send_message(
        (
            f"Welcome test complete for {target.mention}. "
            f"DM sent: {'yes' if dm_sent else 'no'}. "
            f"Entry channel message sent: {'yes' if channel_sent else 'no'}."
        ),
        ephemeral=True,
    )


@client.tree.command(name="help", description="a summary of all commands")
async def help(interaction: discord.Interaction):
    embed = help_embed()
    await interaction.response.send_message(embed=embed)


client.run(TOKEN)
