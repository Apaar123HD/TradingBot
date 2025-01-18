import yfinance as yf
from datetime import datetime, time
import datetime
from datetime import datetime as dt
import pytz
import discord
from discord.ext import commands
from discord.ext import tasks
import numpy as np
import mysql.connector
import creds

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd=creds.SQL_pass,
    database="TradingBot"
)

cursor = connection.cursor()

intents = discord.Intents.all()
intents.message_content = True

client = commands.Bot(intents=intents, command_prefix='.', case_insensitive=True)

@client.event
async def on_ready():
    send_messages.start()

@tasks.loop(seconds=60)
async def send_messages():
    if datetime.datetime.now().time() >= datetime.time(20, 0) and datetime.datetime.now().time() <= datetime.time(2, 30):
        data2 = yf.download('AAPL', period="1d", interval="1m")
        channel = client.get_channel(1329783059914166333)
        new_msg = float(data2['Close'].values[-1])
        cursor.execute(f"INSERT INTO prices VALUES ('{new_msg}')")
        cursor.execute("SELECT * FROM prices")
        result = cursor.fetchall()
        average = np.average(result[-5])
        cursor.execute("select shares from everything")
        shares = cursor.fetchall()
        shares = int(shares[0][0])
        cursor.execute("select liquid from everything")
        liquidity = cursor.fetchall()
        liquidity = int(liquidity[0][0])
        if new_msg < average and shares < 60:
            shares += 1
            liquidity -= new_msg
            cursor.execute(f"UPDATE everything SET liquid = {liquidity} WHERE share_name = 'AAPL'")
        elif new_msg > average and shares > 0:
            shares -= 1
            liquidity += new_msg
            cursor.execute(f"UPDATE everything SET liquid = {liquidity}")
        elif new_msg == average:
            cursor.execute(f"UPDATE everything SET liquid = {liquidity}")
        elif shares == 60:
            cursor.execute(f"UPDATE everything SET liquid = {liquidity}")
        elif shares == 0:
            new_purchase_amount = liquidity/2
            liquidity -= new_purchase_amount
            shares = new_purchase_amount/new_msg
            cursor.execute(f"UPDATE everything SET liquid = {liquidity}")
        cursor.execute(f"UPDATE everything SET shares = {shares} where share_name ='AAPL' ")
        cursor.execute(f"UPDATE everything SET share_worth = {shares*new_msg} where share_name ='AAPL'")
        connection.commit()
        embed = discord.Embed(title="Profit",
                          description=f"${round(liquidity + (shares * new_msg) - 10032, 2)}",
                          colour=0x00b0f4,
                          timestamp=datetime.datetime.now(pytz.timezone("Asia/Kolkata")),)

        embed.set_author(name="apaar's AAPL Trading Bot",
                     icon_url="https://media.discordapp.net/attachments/784418965912944641/1329898582941237308/yournamekiminonawamitsuha.jpg?ex=678c0412&is=678ab292&hm=3ccfea9068358b85f032849d2f6b7155480d36038e7906f1014e86036f1f6b99&=&format=webp&width=548&height=546")

        embed.add_field(name="Apple Share Price",
                    value=f"${round(new_msg, 2)}",
                    inline=False)
        embed.add_field(name="Total Shares Owned",
                    value=f"{round(shares, 2)}",
                    inline=False)
        embed.add_field(name="Worth of Shares",
                    value=f"${round(shares*new_msg, 2)}",
                    inline=False)
        embed.add_field(name="Liquid Money",
                    value=f"${round(liquidity, 2)}",
                    inline=False)

        embed.set_footer(text="Market Open: 8PM - 2:30AM",
                     icon_url="https://cdn.discordapp.com/attachments/784418965912944641/1329898760385597543/ai.png?ex=678c043c&is=678ab2bc&hm=e80ab8afc95bba104208932e67ce374ba7f7031a349283a4e11fbc7c6503ca9c&")

        await channel.send(embed=embed)
    else:
        now = dt.now()
        pm8 = dt(now.year, now.month, now.day, 20, 0)
        time_diff = pm8 - now
        embed = discord.Embed(title=f"The Market Opens in {time_diff} hours",)
        channel = client.get_channel(1329783059914166333)
        await channel.send(embed=embed)

client.run(creds.discord_key)

