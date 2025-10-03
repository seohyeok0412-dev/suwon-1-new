import discord
from discord.ext import commands
from discord import app_commands
from rblxopencloud import Experience
from rblxopencloud.exceptions import NotFound
import datetime

# ========================
# 설정
# ========================
BOT_TOKEN = "MTQxNTY4NDIwNTE0MDI1MDcxNw.GTEwiN.8BtRWXc7ODJTB67jlmankJkF6q7AmYV9af-_mw"
API_KEY = "VSFINtAjWUqJ9VSjhu58+T7zHbrLByU07bNvHyZfscwIh2FBZXlKaGJHY2lPaUpTVXpJMU5pSXNJbXRwWkNJNkluTnBaeTB5TURJeExUQTNMVEV6VkRFNE9qVXhPalE1V2lJc0luUjVjQ0k2SWtwWFZDSjkuZXlKaGRXUWlPaUpTYjJKc2IzaEpiblJsY201aGJDSXNJbWx6Y3lJNklrTnNiM1ZrUVhWMGFHVnVkR2xqWVhScGIyNVRaWEoyYVdObElpd2lZbUZ6WlVGd2FVdGxlU0k2SWxaVFJrbE9kRUZxVjFWeFNqbFdVMnBvZFRVNEsxUTNla2hpY2t4Q2VWVXdOMkpPZGtoNVdtWnpZM2RKYURKR1FpSXNJbTkzYm1WeVNXUWlPaUl6TXpFM09UUTFPRGt5SWl3aVpYaHdJam94TnpVNE16Z3dOVFF4TENKcFlYUWlPakUzTlRnek56WTVOREVzSW01aVppSTZNVGMxT0RNM05qazBNWDAuYk8yUEtEd3RldWkybWhQVWYxeU5qTHJ0cjhNTEtvZ28yT0IwU29Kd24xZ1l1dTdjdnY4TDEyWFo3elhoRF9tNzBXdzR0c1djTHdDVlMwTERuR18zcG9ZSUdYZ295NUJnaXpOdG5MeGhSV3ZUR1hWV2V1ZlllXzJlelZqcHkxektxTjVHRm5oV1R4RWhVZ29jVzNrNlFyd2ZPS05xZHl0QmlOTnpQVjdZRHhLWHpDMUZQTXFMaEQ5WmlZWVBNWmxRTGxJd2JPc1phZXVHd2pNVGFtNzBraGpBbDZiLTd2dVl1d0RhaXNMbkkxUTR4WlB0S0djdTA3VUpFQU5xOGpkekVIUEgwZjdkb2ppaU9DY0gyaW9MaHlhUkhGUFdGa0hRelRRSzJjak52M1hHdXBPRnY5R3lhbnVhMGVaVEFJcWx0R0NoTWNOV1RHeEgxVnF4eURmNGln"
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
        # unique_id 없으면 새로 발급
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

    # 서버 메시지 Embed
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

    # DM Embed
    dm_embed = discord.Embed(
        title=f"환영합니다 {user.display_name} 님 🎉",
        description=f"수원시의 인증이 완료되었습니다.\n게임의 접근이 허가되었습니다 ✅",
        color=0x00ff00
    )
    try:
        await user.send(embed=dm_embed)
    except:
        pass

# ========================
# /송금
# ========================
@bot.tree.command(name="송금", description="다른 유저에게 돈을 송금")
@app_commands.describe(user="받는 유저", amount="송금 금액")
async def 송금(inter: discord.Interaction, user: discord.Member, amount: int):
    if amount <= 0:
        return await inter.response.send_message("❌ 송금 금액은 0보다 커야 합니다.", ephemeral=True)

    sender_nickname = get_nickname_by_discord(inter.user.id)
    receiver_nickname = get_nickname_by_discord(user.id)
    if not sender_nickname or not receiver_nickname:
        return await inter.response.send_message("❌ 송금은 인증된 유저만 가능합니다.", ephemeral=True)

    sender_data = ds_get(nickname_key(sender_nickname))
    receiver_data = ds_get(nickname_key(receiver_nickname))
    if sender_data["money"] < amount:
        return await inter.response.send_message("❌ 금액이 부족합니다.", ephemeral=True)

    # Confirm View
    class ConfirmView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=30)
            self.processed = False

        @discord.ui.button(label="확인", style=discord.ButtonStyle.green)
        async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.processed:
                return await interaction.response.send_message("이미 처리된 송금입니다.", ephemeral=True)
            self.processed = True

            # 송금 처리
            sender_data["money"] -= amount
            receiver_data["money"] += amount
            ds_set(nickname_key(sender_nickname), sender_data)
            ds_set(nickname_key(receiver_nickname), receiver_data)

            # 메시지 수정
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="송금 완료 ✅",
                    description=f"{user.mention} 님에게 {amount}원을 송금했습니다.",
                    color=0x00ff00
                ),
                view=None
            )

            # DM 발송
            dm_sender = discord.Embed(
                title="송금 완료",
                description=f"{amount}원을 {user.mention}님에게 송금했습니다.",
                color=0x00ff00
            )
            dm_receiver = discord.Embed(
                title="입금 완료",
                description=f"{inter.user.mention}님으로부터 {amount}원을 받았습니다.",
                color=0x00ff00
            )
            try:
                await inter.user.send(embed=dm_sender)
                await user.send(embed=dm_receiver)
            except:
                pass

        @discord.ui.button(label="취소", style=discord.ButtonStyle.red)
        async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.processed:
                return await interaction.response.send_message("이미 처리된 송금입니다.", ephemeral=True)
            self.processed = True
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="송금 취소 ❌",
                    description="송금이 취소되었습니다.",
                    color=0xff0000
                ),
                view=None
            )

    embed = discord.Embed(
        title="송금을 진행하시겠습니까?",
        description=f"받는이 : {user.mention}\n금액 : {amount}원",
        color=0xffaa00
    )
    await inter.response.send_message(embed=embed, view=ConfirmView(), ephemeral=True)

# ========================
# /돈 (관리자)
# ========================
@bot.tree.command(name="돈", description="관리자가 유저 돈을 설정")
@app_commands.describe(action="입금/출금", user="대상 유저", amount="금액")
async def 돈(inter: discord.Interaction, action: str, user: discord.Member, amount: int):
    if not inter.user.guild_permissions.administrator:
        return await inter.response.send_message("❌ 관리자 전용 명령어입니다.", ephemeral=True)

    target_nickname = get_nickname_by_discord(user.id)
    if not target_nickname:
        return await inter.response.send_message("❌ 대상 유저가 인증되지 않았습니다.", ephemeral=True)

    data = ds_get(nickname_key(target_nickname))
    if action == "입금":
        data["money"] += amount
    elif action == "출금":
        data["money"] -= amount
        if data["money"] < 0:
            data["money"] = 0
    else:
        return await inter.response.send_message("❌ action은 '입금' 또는 '출금'만 가능합니다.", ephemeral=True)

    ds_set(nickname_key(target_nickname), data)
    await inter.response.send_message(f"{user.mention} 님의 잔액을 {action} {amount}원 처리했습니다.", ephemeral=True)

# ========================
# /정보
# ========================
@bot.tree.command(name="정보", description="유저 정보를 확인합니다")
@app_commands.describe(user="조회할 유저 (선택 사항)")
async def 정보(inter: discord.Interaction, user: discord.Member = None):
    target = user or inter.user
    nickname = get_nickname_by_discord(target.id)

    embed = discord.Embed(
        title=f"{target.display_name} 님의 정보",
        color=0x3498db
    )
    if nickname:
        data = ds_get(nickname_key(nickname))
        embed.add_field(name="닉네임", value=nickname, inline=False)
        embed.add_field(name="고유번호", value=str(data['unique_id']), inline=False)
        embed.add_field(name="보유금액", value=str(data['money']), inline=False)
    else:
        embed.description = "❌ 유저가 인증되지 않았습니다."

    await inter.response.send_message(embed=embed, ephemeral=True)

# ========================
# 봇 준비
# ========================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user} - Commands synced")

bot.run(BOT_TOKEN)