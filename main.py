import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ========= 言語設定保存 =========
language_settings = {}

# 対応言語辞書
LANG = {
    "ja": {
        "time_result": "📅 結果:\n{b1} から {b2} までの差:\n➡ **{days}日 {hours}時間 {minutes}分** 経過しています。",
        "keika_result": "🕒 結果:\n基準: {base}\n経過: {d}日 {h}時間 {m}分 ({mode})\n➡ 結果: **{res}**",
        "mode_error": "❌ modeは `after` または `before` を選んでください。",
        "lang_set": "🌐 言語を日本語に変更しました。"
    },
    "en": {
        "time_result": "📅 Result:\nFrom {b1} to {b2}:\n➡ **{days} days, {hours} hours, {minutes} minutes** difference.",
        "keika_result": "🕒 Result:\nBase: {base}\nElapsed: {d} days, {h} hours, {m} minutes ({mode})\n➡ Result: **{res}**",
        "mode_error": "❌ mode must be `after` or `before`.",
        "lang_set": "🌐 Language set to English."
    },
    "zh": {
        "time_result": "📅 结果:\n从 {b1} 到 {b2}:\n➡ **{days}天 {hours}小时 {minutes}分钟** 的差。",
        "keika_result": "🕒 结果:\n基准: {base}\n经过: {d}天 {h}小时 {m}分钟 ({mode})\n➡ 结果: **{res}**",
        "mode_error": "❌ 模式必须是 `after` 或 `before`。",
        "lang_set": "🌐 已将语言设置为中文。"
    },
    "ko": {
        "time_result": "📅 결과:\n{b1} 부터 {b2} 까지:\n➡ **{days}일 {hours}시간 {minutes}분** 차이입니다.",
        "keika_result": "🕒 결과:\n기준: {base}\n경과: {d}일 {h}시간 {m}분 ({mode})\n➡ 결과: **{res}**",
        "mode_error": "❌ mode는 `after` 또는 `before`이어야 합니다.",
        "lang_set": "🌐 언어가 한국어로 설정되었습니다."
    }
}


# ========= 言語コマンド =========
@bot.tree.command(name="language", description="言語を変更します。Change the bot language.")
@app_commands.describe(language="言語を選んでください (ja/en/zh/ko)")
async def language(interaction: discord.Interaction, language: str):
    language = language.lower()
    if language not in LANG:
        await interaction.response.send_message("❌ 有効な言語: ja / en / zh / ko", ephemeral=True)
        return
    language_settings[interaction.user.id] = language
    await interaction.response.send_message(LANG[language]["lang_set"], ephemeral=True)


# ========= /time =========
@bot.tree.command(name="time", description="2つの日時の差を計算します。")
@app_commands.describe(
    year="基準の年",
    month="基準の月",
    day="基準の日",
    hour="基準の時",
    minute="基準の分",
    mode="after(後) or before(前)",
    year2="比較する年",
    month2="比較する月",
    day2="比較する日",
    hour2="比較する時",
    minute2="比較する分"
)
async def time(interaction: discord.Interaction, year: int, month: int, day: int, hour: int, minute: int,
               mode: str, year2: int, month2: int, day2: int, hour2: int, minute2: int):
    lang = language_settings.get(interaction.user.id, "en")
    try:
        base_date = datetime(year, month, day, hour, minute)
        target_date = datetime(year2, month2, day2, hour2, minute2)

        if mode.lower() == "after":
            diff = target_date - base_date
        elif mode.lower() == "before":
            diff = base_date - target_date
        else:
            await interaction.response.send_message(LANG[lang]["mode_error"], ephemeral=True)
            return

        total_seconds = int(diff.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60

        text = LANG[lang]["time_result"].format(
            b1=f"{year}/{month}/{day} {hour}:{minute:02d}",
            b2=f"{year2}/{month2}/{day2} {hour2}:{minute2:02d}",
            days=days, hours=hours, minutes=minutes
        )
        await interaction.response.send_message(text)

    except Exception as e:
        await interaction.response.send_message(f"⚠ Error: {e}", ephemeral=True)


# ========= /keika =========
@bot.tree.command(name="keika", description="基準の時間に経過時間を足します。")
@app_commands.describe(
    year="基準の年",
    month="基準の月",
    day="基準の日",
    hour="基準の時",
    minute="基準の分",
    mode="after(後) or before(前)",
    day2="経過する日数",
    hour2="経過する時間",
    minute2="経過する分"
)
async def keika(interaction: discord.Interaction, year: int, month: int, day: int, hour: int, minute: int,
                mode: str, day2: int = 0, hour2: int = 0, minute2: int = 0):
    lang = language_settings.get(interaction.user.id, "en")
    try:
        base_date = datetime(year, month, day, hour, minute)
        delta = timedelta(days=day2, hours=hour2, minutes=minute2)

        if mode.lower() == "after":
            result = base_date + delta
        elif mode.lower() == "before":
            result = base_date - delta
        else:
            await interaction.response.send_message(LANG[lang]["mode_error"], ephemeral=True)
            return

        text = LANG[lang]["keika_result"].format(
            base=f"{year}/{month}/{day} {hour}:{minute:02d}",
            d=day2, h=hour2, m=minute2, mode=mode,
            res=f"{result.year}/{result.month}/{result.day} {result.hour}:{result.minute:02d}"
        )
        await interaction.response.send_message(text)

    except Exception as e:
        await interaction.response.send_message(f"⚠ Error: {e}", ephemeral=True)


# ========= ステータス更新 =========
@tasks.loop(minutes=5)
async def update_status():
    await bot.wait_until_ready()
    server_count = len(bot.guilds)
    await bot.change_presence(
        activity=discord.Game(name=f"🌐 {server_count} servers | {server_count}個のサーバーで稼働中")
    )

@bot.event
async def on_ready():
    await bot.tree.sync()
    update_status.start()
    print(f"✅ Logged in as {bot.user} ({len(bot.guilds)} servers)")
    await bot.change_presence(
        activity=discord.Game(name=f"🌐 {len(bot.guilds)} servers | {len(bot.guilds)}個のサーバーで稼働中")
    )

bot.run(TOKEN)
