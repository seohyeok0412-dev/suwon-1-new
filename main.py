import discord
from discord.ext import commands
from discord import app_commands
from rblxopencloud import Experience
from rblxopencloud.exceptions import NotFound
import datetime
import os   # ✅ os 모듈 추가

# ========================
# 설정 (환경변수에서 불러오기)
# ========================
BOT_TOKEN = os.environ["BOT_TOKEN"]   # ✅ 환경변수 BOT_TOKEN
API_KEY = os.environ["API_KEY"]       # ✅ 환경변수 API_KEY
UNIVERSE_ID = "8616482885"
DATASTORE_NAME = "molang"
SCOPE = "global"

# ========================
# Roblox Experience 연결
# ========================
experience = Experience(UNIVERSE_ID, api_key=API_KEY)
datastore = experience.get_datastore(DATASTORE_NAME, scope=SCOPE)
print("✅ Roblox Datastore 연결 성공!")

# ========================
# Discord Bot 준비
# ========================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True  # Privileged Intent 활성화
bot = commands.Bot(command_prefix="/", intents=intents)

# ========================
# DataStore 유틸
# ========================
def ds_get(key: str):
    try:
        value, _ = datastore.get_entry(key)
        return value
    except NotFound:
        return None

def ds_set(key: str, value):
    datastore.set_entry(key, value)

def nickname_key(nickname: str) -> str:
    return nickname

def discord_map_key(discord_id: int) -> str:
    return f"map:discord:{discord_id}"

def get_nickname_by_discord(discord_id: int):
    return ds_get(discord_map_key(discord_id))

def get_next_unique_id() -> int:
    counter = ds_get("UniqueIdCounter")
    if counter is None:
        counter = 0
    counter += 1
    ds_set("UniqueIdCounter", counter)
    return counter

def ensure_user_record(nickname: str, discord_id: int):
    key = nickname_key(nickname)
    data = ds_get(key)
    if data is None:
        uid = get_next_unique_id()
        data = {"money": 0, "discord_id": str(discord_id), "unique_id": uid}
        ds_set(key, data)
    else:
        if "unique_id" not in data or data["unique_id"] is None:
            data["unique_id"] = get_next_unique_id()
        data["discord_id"] = str(discord_id)
        ds_set(key, data)
    ds_set(discord_map_key(discord_id), nickname)
    return data

# ========================
# /인증
# ========================
@bot.tree.command(name="인증", description="관리자가 유저 인증")
@app_commands.describe(user="인증할 유저", roblox_nickname="로블록스 닉네임")
async def 인증(inter: discord.Interaction, user: discord.Member, roblox_nickname: str):
    if not inter.user.guild_permissions.administrator:
        await inter.response.send_message("❌ 관리자만 인증 가능", ephemeral=True)
        return

    data = ensure_user_record(roblox_nickname, user.id)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    embed = discord.Embed(
        title=f"{user.display_name} 님의 인증이 완료되었습니다 ✅",
        color=0x00ff00,
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="닉네임", value=roblox_nickname, inline=False)
    embed.add_field(name="고유번호", value=str(data['unique_id']), inline=False)
    embed.add_field(name="인증시각", value=now, inline=False)
    embed.add_field(name="관리자", value=inter.user.mention, inline=False)

    await inter.response.send_message(embed=embed)

    dm_embed = discord.Embed(
        title=f"환영합니다 {user.display_name} 님 🎉",
        description=f"수원시의 인증이 완료되었습니다.\n게임의 접근이 허가되었습니다 ✅",
        color=0x00ff00
    )
    try:
        await user.send(embed=dm_embed)
    except:
        pass

# (나머지 /송금, /돈, /정보 함수 그대로 유지)

# ========================
# 봇 준비
# ========================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user} - Commands synced")

bot.run(BOT_TOKEN)
