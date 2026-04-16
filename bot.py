import discord
from discord.ext import commands
from discord import app_commands
import pytz
from datetime import datetime, timedelta
import json
import os

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
DATA_FILE = "bot_data.json"


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"timezones": {}, "availability": {}}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


data = load_data()


def parse_time(time_str):
    time_str = time_str.strip().lower()
    for fmt in ["%I%p", "%I:%M%p", "%I %p", "%I:%M %p", "%H:%M", "%H"]:
        try:
            parsed = datetime.strptime(time_str, fmt)
            return parsed.hour, parsed.minute if fmt not in ["%I%p", "%H"] else 0
        except ValueError:
            continue
    return None, None


def local_to_utc(hour, minute, tz_str):
    tz = pytz.timezone(tz_str)
    now = datetime.now(tz)
    local = now.replace(hour=hour, minute=minute, second=0)
    return local.astimezone(pytz.UTC)


def utc_to_local(utc_time, tz_str):
    return utc_time.astimezone(pytz.timezone(tz_str))


def find_overlaps(availabilities, days_ahead=7):
    now = datetime.now(pytz.UTC)
    overlaps = []

    for day in range(days_ahead):
        base = now + timedelta(days=day)
        day_start = base.replace(hour=0, minute=0, second=0, microsecond=0)

        user_windows = {}
        for uid, slots in availabilities.items():
            tz = data["timezones"].get(uid)
            if not tz:
                continue

            windows = []
            for slot in slots:
                local_tz = pytz.timezone(tz)
                local_start = day_start.astimezone(local_tz).replace(
                    hour=slot["start_h"], minute=slot["start_m"]
                )
                local_end = day_start.astimezone(local_tz).replace(
                    hour=slot["end_h"], minute=slot["end_m"]
                )
                if local_end < local_start:
                    local_end += timedelta(days=1)

                windows.append(
                    {
                        "start": local_start.astimezone(pytz.UTC),
                        "end": local_end.astimezone(pytz.UTC),
                    }
                )
            user_windows[uid] = windows

        if len(user_windows) < 2:
            continue

        uids = list(user_windows.keys())
        for w1 in user_windows.get(uids[0], []):
            start, end = w1["start"], w1["end"]
            available = [uids[0]]

            for other in uids[1:]:
                found = False
                for w2 in user_windows.get(other, []):
                    s = max(start, w2["start"])
                    e = min(end, w2["end"])
                    if s < e:
                        start, end = s, e
                        available.append(other)
                        found = True
                        break
                if not found:
                    break

            if len(available) >= 2:
                overlaps.append(
                    {
                        "utc_start": start,
                        "utc_end": end,
                        "duration": int((end - start).total_seconds() / 60),
                        "count": len(available),
                        "users": available,
                    }
                )

    overlaps.sort(key=lambda x: (-x["count"], -x["duration"]))
    return overlaps[:5]


@bot.event
async def on_ready():
    print(f"Bot ready: {bot.user}")
    await bot.tree.sync()


@bot.tree.command(name="settimezone", description="Set your timezone")
@app_commands.describe(timezone="Start typing your timezone (e.g., Asia/Kolkata or America/New_York)")
async def set_timezone(interaction: discord.Interaction, timezone: str):
    # Validate that the submitted timezone is actually valid
    if timezone not in pytz.all_timezones:
        await interaction.response.send_message(
            "❌ Invalid timezone. Please select one from the autocomplete list.", 
            ephemeral=True
        )
        return

    data["timezones"][str(interaction.user.id)] = timezone
    save_data(data)
    local = datetime.now(pytz.timezone(timezone))
    await interaction.response.send_message(
        f"✅ Timezone set to **{timezone}**\nYour current time: {local.strftime('%I:%M %p')}",
        ephemeral=True,
    )

@set_timezone.autocomplete("timezone")
async def timezone_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    # Filter common timezones based on what the user has typed
    matches = [tz for tz in pytz.common_timezones if current.lower() in tz.lower()]
    # Discord limits autocomplete choices to 25
    return [app_commands.Choice(name=tz, value=tz) for tz in matches[:25]]


@bot.tree.command(name="free", description="When are you free? (in YOUR timezone)")
@app_commands.describe(start="e.g., 6pm, 18:00", end="e.g., 10pm, 22:00")
async def add_free(interaction: discord.Interaction, start: str, end: str):
    uid = str(interaction.user.id)
    tz = data["timezones"].get(uid)

    if not tz:
        await interaction.response.send_message(
            "Set timezone first: `/settimezone`", ephemeral=True
        )
        return

    sh, sm = parse_time(start)
    eh, em = parse_time(end)

    if sh is None or eh is None:
        await interaction.response.send_message(
            "Invalid time. Use: 6pm, 18:00, 6:30", ephemeral=True
        )
        return

    if sm is None:
        sm = 0
    if em is None:
        em = 0

    if uid not in data["availability"]:
        data["availability"][uid] = []

    data["availability"][uid].append(
        {"start_h": sh, "start_m": sm, "end_h": eh, "end_m": em}
    )
    save_data(data)

    utc_start = local_to_utc(sh, sm, tz)
    utc_end = local_to_utc(eh, em, tz)

    await interaction.response.send_message(
        f"✅ Free from **{start}** to **{end}** ({tz})\n"
        f"That's **{utc_start.strftime('%H:%M')}-{utc_end.strftime('%H:%M')}** UTC"
    )


@bot.tree.command(name="findtime", description="Find best meeting time")
async def find_time(interaction: discord.Interaction):
    guild = interaction.guild
    if not guild:
        await interaction.response.send_message("Use in server", ephemeral=True)
        return

    avail = {}
    for m in guild.members:
        if m.bot:
            continue
        uid = str(m.id)
        if data["timezones"].get(uid) and data["availability"].get(uid):
            avail[uid] = data["availability"][uid]

    if len(avail) < 2:
        await interaction.response.send_message(
            f"Need 2+ people. Only {len(avail)} ready.\n"
            "Everyone do: `/settimezone` then `/free`",
            ephemeral=True,
        )
        return

    await interaction.response.defer()
    overlaps = find_overlaps(avail)

    if not overlaps:
        await interaction.followup.send(
            "No overlapping times found. Adjust your availability."
        )
        return

    embed = discord.Embed(title="🎙️ Best Meeting Times", color=discord.Color.green())

    for ov in overlaps:
        details = []
        for uid in ov["users"]:
            m = guild.get_member(int(uid))
            tz = data["timezones"][uid]
            local_start = utc_to_local(ov["utc_start"], tz)
            local_end = utc_to_local(ov["utc_end"], tz)
            details.append(
                f"**{m.display_name if m else uid}**: "
                f"{local_start.strftime('%I:%M %p')} - {local_end.strftime('%I:%M %p')}"
            )

        embed.add_field(
            name=f"{ov['count']} people | {ov['duration']} min | {ov['utc_start'].strftime('%a %b %d')}",
            value=f"UTC: {ov['utc_start'].strftime('%H:%M')}-{ov['utc_end'].strftime('%H:%M')}\n"
            + "\n".join(details),
            inline=False,
        )

    await interaction.followup.send(embed=embed)


@bot.tree.command(name="myavailability", description="View or clear your availability")
@app_commands.describe(action="View or clear")
@app_commands.choices(
    action=[
        app_commands.Choice(name="view", value="view"),
        app_commands.Choice(name="clear", value="clear"),
    ]
)
async def my_avail(interaction: discord.Interaction, action: str = "view"):
    uid = str(interaction.user.id)

    if action == "clear":
        if uid in data["availability"]:
            del data["availability"][uid]
            save_data(data)
        await interaction.response.send_message("Cleared.", ephemeral=True)
        return

    slots = data["availability"].get(uid, [])
    if not slots:
        await interaction.response.send_message(
            "No availability. Use `/free`", ephemeral=True
        )
        return

    text = "\n".join(
        [
            f"{s['start_h']:02d}:{s['start_m']:02d} - {s['end_h']:02d}:{s['end_m']:02d}"
            for s in slots
        ]
    )
    await interaction.response.send_message(
        f"Your availability:\n{text}", ephemeral=True
    )


if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_BOT_TOKEN")
        if not TOKEN:
        print("Set DISCORD_BOT_TOKEN env variable")
        exit(1)
    bot.run(TOKEN)
