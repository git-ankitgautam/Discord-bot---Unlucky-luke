import asyncio
import json
import logging
import os
import re
import requests
from datetime import datetime
from datetime import timedelta
from html import unescape
from pathlib import Path
from typing import Literal, Optional

import discord
from discord import app_commands
from discord.ext import commands
from google import genai
from google.genai import types

from config import API_KEY, TOKEN
from enlightenme import get_quote
from faction_intros_embed import response_embed
from helpme import help_embed
from imbored import joke_response
from leader_dataset import (
    find_latest_dataset_file,
    load_leader_messages,
    pick_best_match,
    pick_random_message,
)
from moderation_logic import evaluate_exemption
from moderation_store import ModerationStore, render_member_template
from profanity_checker import profanity_check


logger = logging.getLogger("disbot")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    file_handler = logging.FileHandler("bot.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)


store = ModerationStore()
store.initialize()

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
LUKE_FILE_SEARCH_STORE = os.getenv("LUKE_FILE_SEARCH_STORE")
_gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
_system_prompt_path = Path("luke_system_prompt.txt")
if _system_prompt_path.exists():
    LUKE_SYSTEM_PROMPT = _system_prompt_path.read_text(encoding="utf-8")
else:
    LUKE_SYSTEM_PROMPT = (
        "You are a Discord assistant speaking in Luke's style. "
        "Keep replies concise, practical, and friendly."
    )
if not LUKE_FILE_SEARCH_STORE:
    logger.warning("LUKE_FILE_SEARCH_STORE is missing; mention replies will use local fallback only")

with open("Factionsdata.txt", encoding="utf-8") as _factions_file:
    _factions_data = json.load(_factions_file)
DEVLINS_FACTIONS_BY_ID = {
    int(entry["ID"]): entry["name"] for entry in _factions_data.values()
}
DEVLINS_FACTION_IDS = set(DEVLINS_FACTIONS_BY_ID.keys())

LEADER_DATASET_FILE = find_latest_dataset_file(".")
LEADER_MESSAGES = (
    load_leader_messages(LEADER_DATASET_FILE) if LEADER_DATASET_FILE else []
)
if LEADER_DATASET_FILE:
    logger.info(
        "Loaded leader dataset from %s with %s usable messages",
        LEADER_DATASET_FILE,
        len(LEADER_MESSAGES),
    )
else:
    logger.warning("No user_messages_*.jsonl dataset found; /luke_says will be unavailable")


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


def _strip_bot_mentions(text: str, bot_user_id: int) -> str:
    pattern = rf"<@!?{bot_user_id}>"
    cleaned = re.sub(pattern, "", text).strip()
    return cleaned


def _generate_local_fallback_reply(prompt: str) -> str:
    if not LEADER_MESSAGES:
        return "I heard you, but I do not have enough context loaded yet."
    selected = pick_best_match(LEADER_MESSAGES, prompt) if prompt else pick_random_message(LEADER_MESSAGES)
    if not selected:
        return "I heard you, but I do not have enough context loaded yet."
    return str(selected["content"])


def generate_luke_reply(prompt: str) -> str:
    if not LUKE_FILE_SEARCH_STORE:
        return _generate_local_fallback_reply(prompt)

    response = _gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=LUKE_SYSTEM_PROMPT,
            tools=[
                types.Tool(
                    file_search=types.FileSearch(
                        file_search_store_names=[LUKE_FILE_SEARCH_STORE]
                    )
                )
            ],
        ),
    )
    text = (response.text or "").strip()
    if not text:
        return _generate_local_fallback_reply(prompt)
    return text


def get_devlins_faction_name_for_discord_user(discord_user_id: int) -> Optional[str]:
    try:
        response = requests.get(
            f"https://api.torn.com/user/{discord_user_id}?selections=profile&key={API_KEY}",
            timeout=15,
        )
    except requests.RequestException as err:
        logger.warning("Torn API request failed for discord user %s: %s", discord_user_id, err)
        return None

    if response.status_code != 200:
        logger.warning(
            "Torn API returned non-200 for discord user %s: %s",
            discord_user_id,
            response.status_code,
        )
        return None

    payload = response.json()
    if "error" in payload:
        return None

    faction = payload.get("faction") or {}
    faction_id = faction.get("faction_id")
    if faction_id is None:
        return None

    try:
        faction_id_int = int(faction_id)
    except (TypeError, ValueError):
        return None

    if faction_id_int not in DEVLINS_FACTION_IDS:
        return None

    faction_name = DEVLINS_FACTIONS_BY_ID.get(faction_id_int) or faction.get("faction_name")
    if not faction_name:
        return None
    return unescape(str(faction_name))


def _normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def get_faction_role_mention(guild: discord.Guild, faction_name: str) -> Optional[str]:
    target = _normalize_name(faction_name)
    for role in guild.roles:
        if _normalize_name(role.name) == target:
            return role.mention
    return None


class BotClient(commands.Bot):
    async def on_ready(self):
        logger.info("Unlucky_luke ready")
        try:
            store.initialize()
            synced = await self.tree.sync()
            logger.info("Synced %s commands", len(synced))
        except Exception as e:
            logger.exception("Unlucky_luke ran into an error: %s", e)

    async def on_member_join(self, member: discord.Member):
        try:
            await send_welcome_for_member(member)
        except Exception as e:
            logger.exception("Failed welcome flow for guild=%s: %s", member.guild.id, e)

    async def on_message(self, message: discord.Message):
        if message.author == self.user or message.author.bot:
            return

        msg = message.content.lower()

        if msg.startswith("hi luke"):
            await message.channel.send(
                f"Hello {message.author.display_name}, this is a 100 percent luke, there is no doubt to it, trust me :D"
            )

        if self.user and self.user in message.mentions:
            user_prompt = _strip_bot_mentions(message.content, self.user.id)
            if not user_prompt:
                user_prompt = "Say a short hello to the member in Luke style."
            try:
                luke_reply = await asyncio.to_thread(generate_luke_reply, user_prompt)
            except Exception as err:
                logger.exception("Mention reply generation failed: %s", err)
                luke_reply = _generate_local_fallback_reply(user_prompt)
            await message.reply(luke_reply, mention_author=False)

        if not profanity_check(msg):
            return

        if message.guild is None or not isinstance(message.author, discord.Member):
            return

        try:
            logger.info(
                "Profanity detected in guild=%s user=%s message_id=%s",
                message.guild.id,
                message.author.id,
                message.id,
            )
            settings = store.ensure_guild_settings(message.guild.id)
            if is_exempt(message.author, settings):
                logger.info(
                    "Profanity moderation skipped due to exemption for user=%s guild=%s",
                    message.author.id,
                    message.guild.id,
                )
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

            try:
                with open("captain-america.gif", "rb") as language_gif:
                    await message.reply(file=discord.File(language_gif))
            except FileNotFoundError:
                logger.warning("captain-america.gif not found; skipping GIF reply")

            await message.reply(
                f"Please avoid profanity. Warning {warning_count}/{threshold} (active for {int(settings['warning_expiry_days'])} days)."
            )

            if warning_count >= threshold:
                timeout_minutes = int(settings["timeout_minutes"])
                timeout_until = discord.utils.utcnow() + timedelta(minutes=timeout_minutes)
                try:
                    await message.author.timeout(timeout_until, reason="Profanity threshold reached")
                    logger.warning(
                        "Applied timeout to user=%s guild=%s duration_minutes=%s",
                        message.author.id,
                        message.guild.id,
                        timeout_minutes,
                    )
                    await message.channel.send(
                        f"{message.author.mention} has been timed out for {timeout_minutes} minute(s) due to repeated profanity."
                    )
                except discord.Forbidden:
                    logger.warning(
                        "Missing permission to timeout user=%s in guild=%s",
                        message.author.id,
                        message.guild.id,
                    )
                    await message.channel.send(
                        "I do not have permission to timeout this member."
                    )
                except discord.HTTPException as err:
                    logger.exception(
                        "Discord API error while timing out user=%s in guild=%s: %s",
                        message.author.id,
                        message.guild.id,
                        err,
                    )
                    await message.channel.send(
                        f"Failed to timeout member due to an API error: {err}"
                    )
        except Exception as e:
            logger.exception("Profanity moderation error in guild=%s: %s", message.guild.id, e)


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
            logger.info(
                "Welcome DM blocked for user=%s guild=%s (DM likely closed)",
                member.id,
                member.guild.id,
            )

    entry_channel_id = settings["entry_channel_id"]
    if entry_channel_id:
        channel = member.guild.get_channel(int(entry_channel_id))
        if channel and isinstance(channel, discord.TextChannel):
            faction_name = await asyncio.to_thread(
                get_devlins_faction_name_for_discord_user, member.id
            )
            if faction_name:
                faction_role = get_faction_role_mention(member.guild, faction_name)
                faction_label = faction_role or faction_name
                join_text = f"{member.mention} of {faction_label} has joined the server"
            else:
                join_text = render_member_template(
                    settings["join_template"],
                    member.mention,
                    member.display_name,
                    member.guild.name,
                )
            await channel.send(join_text)
            channel_sent = True

    logger.info(
        "Welcome flow finished for user=%s guild=%s dm_sent=%s channel_sent=%s",
        member.id,
        member.guild.id,
        dm_sent,
        channel_sent,
    )
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


@client.tree.command(
    name="luke_dataset_stats",
    description="Show status of Luke context sources",
)
@app_commands.default_permissions(manage_guild=True)
@app_commands.guild_only()
async def luke_dataset_stats(interaction: discord.Interaction):
    if not await ensure_guild_interaction(interaction):
        return
    if not isinstance(interaction.user, discord.Member) or not has_manage_guild(interaction.user):
        await interaction.response.send_message(
            "You need Manage Server permission to use this command.",
            ephemeral=True,
        )
        return

    if not LEADER_DATASET_FILE:
        await interaction.response.send_message(
            "No dataset file found in this folder (`user_messages_*.jsonl`).",
            ephemeral=True,
        )
        return

    await interaction.response.send_message(
        (
            f"Gemini store: `{LUKE_FILE_SEARCH_STORE or 'not-set'}`\n"
            f"Dataset file: `{LEADER_DATASET_FILE.name}`\n"
            f"Usable messages loaded: {len(LEADER_MESSAGES)}"
        ),
        ephemeral=True,
    )


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
