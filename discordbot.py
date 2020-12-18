from discord.ext import commands
import os
import traceback

bot = commands.Bot(command_prefix='/')
token = os.environ['DISCORD_BOT_TOKEN']


@bot.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, "original", error)
    error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
    await ctx.send(error_msg)


@bot.command()
async def ping(ctx):
    await ctx.send('pong')


bot.run(token)


import requests
import os.path
import re
import discord
import asyncio
from bs4 import BeautifulSoup

# 通知管理用ファイルパス指定
listFilePath = 'list.txt'

# 自分のBotのアクセストークンに置き換えてください
TOKEN = 'Nzg5NTMzNjYwMzE4NTMxNjI0.X9zchQ.OYpcg99QCXrxlOEqRPvkEC6wNtk'

# 任意のチャンネルID(int)
CHANNEL_ID = 0000000000000000

# 確認したいコミュニティを設定
targetCommunitys = ['co5061903']

# リスト内検索 あればTrue 無ければFalseを返す
def searchList(liveURL):
    # ファイル存在チェック
    if not os.path.exists(listFilePath):
        return False

    liveLV = liveIdExtraction(liveURL)

    #ファイル内チェック
    with open(listFilePath) as f:
        for i, line in enumerate(f):
            if line == liveLV + '\n':
                return True
    print(line)
    return False

# リストに放送ID追記
def addList(liveURL):
    liveLV = liveIdExtraction(liveURL)
    with open(listFilePath, 'a') as f:
        print(liveLV, file=f)

# 放送URLから放送ID(lvXXXXXXX)抽出
def liveIdExtraction(liveURL):
    repatter = re.compile('lv[0-9]+')
    return repatter.search(liveURL).group()

# 放送URLから放送タイトル取得
def getLiveTitle(liveURL):
    r = requests.get(liveURL)
    soup = BeautifulSoup(r.content, "html.parser")
    for meta_tag in soup.find_all('meta', attrs={'property': 'og:title'}):
        return meta_tag.get('content')

# 放送URLから放送者名取得
def getLiveName(liveURL):
    r = requests.get(liveURL)
    soup = BeautifulSoup(r.content, "html.parser")
    return soup.find("span",{"class":"name"}).text



# 接続に必要なオブジェクトを生成
client = discord.Client()

# 起動時に動作する処理
@client.event
async def on_ready():
    while(True):
        # ターゲットコミュニティの数だけ繰り返す
        for targetCommunity in targetCommunitys:
            # URLを設定
            r = requests.get("https://com.nicovideo.jp/community/" + targetCommunity)

            # コミュニティTOPページを確認
            soup = BeautifulSoup(r.content, "html.parser")
            result = soup.find("section", "now_live")

            # もし放送が始まっていれば
            if result is not None:
                # 放送URL取得
                liveURL = result.find("a", "now_live_inner").get("href")

                # リスト内を検索してすでに処理済みの放送IDであれば処理しない
                if searchList(liveURL) is False:
                    # 放送タイトル取得
                    liveTitle = getLiveTitle(liveURL)
                    # 放送者名取得
                    liveName = getLiveName(liveURL)

                    # Discordへ送信
                    channel = client.get_channel(CHANNEL_ID)
                    await channel.send('@everyone ' + liveName + 'さんが配信を開始しました\n\n' + liveTitle + '\n' + liveURL)

                    # 放送ID追記
                    addList(liveURL)

        # 1分待つ
        await asyncio.sleep(60)

# Discordに接続
client.run(TOKEN)
