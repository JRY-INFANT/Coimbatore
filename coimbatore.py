import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import threading
import asyncio
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler_log = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is running')

    def do_POST(self):
        if self.path == '/send':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            data = json.loads(body)

            channel_id = int(data.get('channel_id'))
            message = data.get('message')

            async def send():
                channel = bot.get_channel(channel_id)
                if channel:
                    await channel.send(message)

            future = asyncio.run_coroutine_threadsafe(send(), bot.loop)
            future.result(timeout=10)  # wait for it to finish

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"success": true}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # suppress HTTP server logs

def run_server():
    server = HTTPServer(('0.0.0.0', 80), Handler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

@bot.event
async def on_ready():
    print(f"We are ready to go in, {bot.user.name}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if 'hello' in message.content.lower():
        await message.channel.send(f'Hello {message.author.mention}!')
    await bot.process_commands(message)

@bot.command()
async def say(ctx, channel: discord.TextChannel, *, message):
    await channel.send(message)

@bot.command()
async def dm(ctx, *, msg):
    await ctx.author.send(f"You said {msg}")

@bot.command()
async def reply(ctx):
    await ctx.reply("This is a reply to your message!")

bot.run(token, log_handler=handler_log, log_level=logging.DEBUG)
