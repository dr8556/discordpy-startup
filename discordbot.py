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
import os, psycopg2
import json
from bs4 import BeautifulSoup

path = "PATH"
port = "5432"
dbname = "DB_NAME"
user = "USER"
password = "PASSWORD"
conText = "host={} port={} dbname={} user={} password={}"
conText = conText.format(path,port,dbname,user,password)
connection = psycopg2.connect(conText)

cur = connection.cursor()
sql = "select token,channel_id from settings"
cur.execute(sql)
result = cur.fetchone()

# トークン取得
TOKEN = result[0]
# チャンネルID取得
CHANNEL_ID = result[1]

# targetテーブルから確認したいコミュニティを取得
def getTarget():
    targetCommunitys = [co5061903]
    sql = "select community from target"
    cur.execute(sql)
    for row in cur:
        targetCommunitys.append(row[0])
    return targetCommunitys

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

# logsテーブル内検索 あればTrue 無ければFalseを返す
def searchList(liveURL):
    liveLV = liveIdExtraction(liveURL)
    cur = connection.cursor()
    sql = "SELECT count(*)  FROM logs WHERE live = '" + liveLV + "'"
    cur.execute(sql)
    result = cur.fetchone()
    if int(result[0]) > 0:
        return True
    else:
        return False

# logsテーブルに放送ID追記
def addList(liveURL):
    liveLV = liveIdExtraction(liveURL)
    cur = connection.cursor()
    sql = "insert into logs(live) values('"+ liveLV + "');"
    cur.execute(sql)
    connection.commit()

# 接続に必要なオブジェクトを生成
client = discord.Client()

# 起動時に動作する処理
@client.event
async def on_ready():

    while(True):
        # ターゲットコミュニティの数だけ繰り返す
        targetCommunitys = getTarget()
        for targetCommunity in targetCommunitys:
            # URLを設定
            r = requests.get("https://live.nicovideo.jp/watch/" + targetCommunity)

            # コミュニティTOPページを確認
            soup = BeautifulSoup(r.content, "html.parser")
            result = soup.find('meta', attrs={'property': 'og:url', 'content': True})
            # 放送URL取得
            liveURL = result['content']

            # リスト内を検索してすでに処理済みの放送IDであれば処理しない
            if searchList(liveURL) is False:
                # 放送タイトル取得
                liveTitle = getLiveTitle(liveURL)
                # 放送者名取得
                liveName = getLiveName(liveURL)

                # Discordへ送信
                channel = client.get_channel(int(CHANNEL_ID))
                await channel.send(liveName + 'さんが配信を開始しました\n\n' + liveTitle + '\n' + liveURL)

                # 放送ID追記
                addList(liveURL)

        # チャンネル検索
        url = 'https://api.search.nicovideo.jp/api/v2/live/contents/search'
        ua = 'Twitter rasirasirasi34'
        headers = {'User-Agent': ua}
        params = {
            'q': 'BoxTV',
            'targets': 'title,description,tags',
            '_sort': '-openTime',
            '_context': ua,
            'fields': 'contentId,channelId,liveStatus,title',
            'filters[channelId][0]': '2640777',
            'filters[liveStatus][0]': 'onair'
        }
        # リクエスト
        res = requests.get(url, headers=headers, params=params)
        # 取得したjsonをlists変数に格納
        lists = json.loads(res.text)

        if lists['meta']['totalCount'] > 0:
            for data in lists['data']:
                if searchList(data['contentId']) is False:
                    # Discordへ送信
                    channel = client.get_channel(int(CHANNEL_ID))
                    await channel.send('チャンネルで配信を開始しました\n\n' + data['title'] + '\nhttps://nico.ms/' + data['contentId'])

                    # 放送ID追記
                    addList(data['contentId'])

        # 1分待つ
        await asyncio.sleep(60)

# Discordに接続
client.run(TOKEN)
