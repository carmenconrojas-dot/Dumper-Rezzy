import random
import string
import discord
from discord.utils import escape_mentions
from discord import CustomActivity
from datetime import timedelta,datetime
from collections import defaultdict
from json import loads,dumps
import asyncio
from asyncio import sleep
import re
import bypass
import os
from base64 import b64encode,b64decode
import time
import requests
from shutil import move as file_move
import tempfile
from PIL import Image, ImageDraw, ImageFont, ImageColor
import io
import licensing
from discord.ui import Button, View, Select
from hashlib import sha256
import aiohttp
import ssl, certifi
import urllib.parse

is_localhost=False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LUNE_PATH    = os.path.join(BASE_DIR, "lune")
DARKLUA_PATH = os.path.join(BASE_DIR, "darklua")
import shutil as _shutil
LUA_PATH  = _shutil.which("lua")  or "lua"
NODE_PATH = _shutil.which("node") or "node"

def _validate_lune():
    if os.path.isfile(LUNE_PATH):
        if not os.access(LUNE_PATH, os.X_OK):
            try:
                import stat
                os.chmod(LUNE_PATH, os.stat(LUNE_PATH).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                print(f"[lune] Binary found and made executable: {LUNE_PATH}")
            except Exception as e:
                print(f"[lune] WARNING: Binary found but could not chmod: {e}")
        else:
            print(f"[lune] Binary found and executable: {LUNE_PATH}")
    else:
        print(f"[lune] ERROR: Binary NOT found at {LUNE_PATH} — lune commands will fail at runtime")

_validate_lune()

def _validate_darklua():
    if os.path.isfile(DARKLUA_PATH):
        if not os.access(DARKLUA_PATH, os.X_OK):
            try:
                import stat
                os.chmod(DARKLUA_PATH, os.stat(DARKLUA_PATH).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                print(f"[darklua] Binary found and made executable: {DARKLUA_PATH}")
            except Exception as e:
                print(f"[darklua] WARNING: Binary found but could not chmod: {e}")
        else:
            print(f"[darklua] Binary found and executable: {DARKLUA_PATH}")
    else:
        print(f"[darklua] WARNING: Binary NOT found at {DARKLUA_PATH} — darklua commands will be skipped at runtime")

_validate_darklua()

def _validate_lua():
    found = _shutil.which("lua")
    if found:
        print(f"[lua] Found in PATH: {found}")
    elif os.path.isfile(os.path.join(BASE_DIR, "lua")):
        print(f"[lua] Using bundled binary: {os.path.join(BASE_DIR, 'lua')}")
    else:
        print("[lua] WARNING: 'lua' not found in PATH or project dir — .obf/.minify will fail")

_validate_lua()

def _validate_node():
    found = _shutil.which("node")
    if found:
        print(f"[node] Found in PATH: {found}")
    else:
        print("[node] WARNING: 'node' not found — beautify/deobf node commands will fail gracefully")

_validate_node()

def _ensure_runtime_dirs():
    dirs = [
        "./dumps/original",
        "./dumps/dumped",
        "./dumps/beautify",
        "./dumps/decompile",
        "./unobfuscated",
        "./obfuscated",
        "hook_op/file_cache",
        "./deobfuscate/.in",
        "./deobfuscate/.out",
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    print("[startup] Runtime directories ensured.")

_ensure_runtime_dirs()

def _extract_mention_id(smsg, idx=1):
    if len(smsg) <= idx:
        return None
    raw = smsg[idx].strip()
    cleaned = raw.replace("<@!", "").replace("<@", "").replace(">", "").strip()
    try:
        return int(cleaned)
    except (ValueError, AttributeError):
        return None

async def _safe_reply(msg, *args, **kwargs):
    try:
        return await msg.reply(*args, **kwargs)
    except discord.errors.HTTPException as _e:
        if _e.code in (50035, 50034, 10008):
            try:
                return await msg.channel.send(*args, **kwargs)
            except Exception:
                pass
        else:
            raise

ssl_context = ssl.create_default_context(cafile=certifi.where())
import os as _os

def _require_env(key: str) -> str:
    v = _os.environ.get(key, "").strip()
    if not v:
        raise RuntimeError(
            f"[Rezzy Env Logger] Required env var {key!r} is not set. "
            "Configure it in Railway or your .env file."
        )
    return v

DISCORD_TOKEN      = _os.environ.get("DISCORD_TOKEN", "")
OWNER_ID           = int(_os.environ.get("OWNER_ID",  "0"))
GUILD_ID           = int(_os.environ.get("GUILD_ID",  "0"))
GITHUB_TOKEN       = _os.environ.get("GITHUB_TOKEN",       "")
MV_API_KEY         = _os.environ.get("MV_API_KEY",         "")
WEBHOOK_URL        = _os.environ.get("WEBHOOK_URL",         "")
DISCORD_COOKIE     = _os.environ.get("DISCORD_COOKIE",     "")
DISCORD_AUTH_TOKEN = _os.environ.get("DISCORD_AUTH_TOKEN", "")
CMDS_CHANNEL_ID    = int(_os.environ.get("CMDS_CHANNEL_ID",    "1482230903244849285"))
DUMP_CHANNEL_ID    = int(_os.environ.get("DUMP_CHANNEL_ID",    "1485376914859364404"))
STATUS_CHANNEL_ID  = int(_os.environ.get("STATUS_CHANNEL_ID",  "1351444142852411454"))
CMDS_CHANNEL_2_ID  = int(_os.environ.get("CMDS_CHANNEL_2_ID",  "1368868223268687942"))
CMDS_CHANNEL_3_ID  = int(_os.environ.get("CMDS_CHANNEL_3_ID",  "1462641847787847791"))
STATUS_STRING      = _os.environ.get("STATUS_STRING", "Rezzy on Top | discord.gg/f8XjPE2c6Y")

ownerid = OWNER_ID
ApiToken = GITHUB_TOKEN
intents = discord.Intents.all()
def randomstr(length=16):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
tag_access=[]
sent_conflict_msg={}

def get_roles(id):
    crack_g = client.get_guild(GUILD_ID)
    if crack_g:
        member = crack_g.get_member(id)
        if member:
            return member.roles
    return []

def has_required_status(member):
    for activity in member.activities:
        if isinstance(activity, discord.CustomActivity) and activity.name and STATUS_STRING in activity.name:
            return True
    return False

status_dm_last_sent = {}
STATUS_DM_COOLDOWN = 3600

TRUSTED_STATUS_BYPASS_IDS = [527548038173032478, 713113056346898522]

def is_command_message(content: str) -> bool:
    content = content.strip()
    return len(content) >= 2 and content[0] in ".,:" and content[1].isalpha()

async def maybe_nag_status(msg):
    if msg.author.id == ownerid or msg.author.id in TRUSTED_STATUS_BYPASS_IDS:
        return
    if has_required_status(msg.author):
        return
    now = time.time()
    last_dm = status_dm_last_sent.get(msg.author.id, 0)
    if now - last_dm < STATUS_DM_COOLDOWN:
        return
    status_dm_last_sent[msg.author.id] = now
    try:
        dm = await msg.author.create_dm()
        await dm.send(
            f"Hey! Looks like you don't have our status set:\n"
            f"**{STATUS_STRING}**\n\n"
            f"Commands still work either way, but setting that as your custom status "
            f"helps support the server a lot — consider dropping it on 🙏"
        )
    except Exception:
        pass

class RetardCommands:
    def __init__(self):
        self.commands = {}
        self.users = defaultdict(int)
    
    def is_cd(self,id,cmdcd):
        currenttime=time.time()
        if self.users[id] and self.users[id]>currenttime:
            return True
        self.users[id]=currenttime+cmdcd
    async def handle_command(self, msg: discord.Message):
        command_name = len(msg.content.split())!=0 and msg.content.split()[0]
        if msg.author.id !=client.user.id and command_name and command_name in self.commands:
            command=self.commands[command_name]
            if not has_required_status(msg.author) and msg.author.id not in TRUSTED_STATUS_BYPASS_IDS and msg.author.id != ownerid:
                await softerror(msg, f"Necesitas tener el estado configurado para usar este comando.\n**{STATUS_STRING}**")
                return
            if self.is_cd(msg.author.id,"cooldown" in command and command["cooldown"] or 4):
                await softerror(msg, f"Youre currently on cooldown! Please wait {round(self.users[msg.author.id]-time.time(),2)}s")
                return
            elif 'allow_channels' in command and msg.channel.id in command['allow_channels']:
                pass
            elif  'channelid' in command and command['channelid'] != msg.channel.id:
                await softerror(msg,f"You can only use this command in <#{command['channelid']}>")
                return
            elif "roles" in command:
                if not any(role.id in command['roles'] for role in get_roles(msg.author.id)):
                    await softerror(msg,f'You dont have permissions to use this command')
                    return
            if msg.channel.id==STATUS_CHANNEL_ID and not msg.author.id in [1498685437886333021,713113056346898522] and command_name!="meow":
                await softerror(msg,"Please use commands like this in dms with me!")
            await command['func'](msg)
            return True
            

command_manager = RetardCommands()

class RenameLuaView(View):
    def __init__(self, lua_path: str, luac_path: str, requester_id: int):
        super().__init__(timeout=30)
        self.lua_path = lua_path
        self.luac_path = luac_path
        self.requester_id = requester_id
        self.renamed = False
        self.message = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.requester_id:
            await interaction.response.send_message("This is not your message.", ephemeral=True)
            return False
        return True
    @discord.ui.button(label="rename", style=discord.ButtonStyle.primary)
    async def rename_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.renamed:
            await interaction.response.send_message("Already being renamed.", ephemeral=True)
            return
        random_id=random.random()
        self.renamed=random_id
        await asyncio.sleep(random_id/10)
        if self.renamed!=random_id:
            await interaction.response.send_message("Already being renamed", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        stem = os.path.splitext(os.path.basename(self.lua_path))[0]
        renamed_path = os.path.join(os.path.dirname(self.lua_path), f"{stem}_rename.lua")
        success = await makeit_rename(self.lua_path, renamed_path)

        if not success or not os.path.isfile(renamed_path):
            print(success,os.path.isfile(renamed_path))
            await interaction.followup.send("Failed to rename the file.", ephemeral=True)
            return

        attachments = []
        try:
            attachments.append(discord.File(renamed_path))
            if self.luac_path and os.path.isfile(self.luac_path):
                attachments.append(discord.File(self.luac_path))
        except Exception as er:
            print(f"rename_button attachment error: {er}")
            await interaction.followup.send("Failed to load renamed file.", ephemeral=True)
            return

        try:
            await interaction.message.edit(attachments=attachments, view=None)
        except Exception as er:
            print(f"rename_button edit error: {er}")
            await interaction.followup.send("Failed to update the message.", ephemeral=True)
            return

        self.renamed = True
        await interaction.followup.send("Success", ephemeral=True)
        self.stop()

    async def on_timeout(self) -> None:
        if not self.renamed and self.message:
            try:
                await self.message.edit(view=None)
            except Exception as er:
                print(f"RenameLuaView timeout edit error: {er}")
        self.stop()
darklua_user_settings = defaultdict(dict)
try:
    loaded_darklua = loads(open("darklua_usersettings.json").read())
    for user_id in loaded_darklua:
        darklua_user_settings[int(user_id)] = loaded_darklua[user_id]
except:
    pass

async def save_darklua_settings():
    try:
        with open("darklua_usersettings.json", "w") as f:
            f.write(dumps(darklua_user_settings))
    except Exception as e:
        print(f"Error saving darklua settings: {e}")

class DarkluaConfigView(View):
    def __init__(self, user_id: int, filename: str):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.filename = filename
        
        user_config = darklua_user_settings.get(user_id, {
            "generator": "readable",
            "column_span": 80,
            "selected_rules": []
        })
        
        self.generator = user_config.get("generator", "readable")
        self.column_span = user_config.get("column_span", 80)
        self.selected_rules = user_config.get("selected_rules", [])
        
        self.available_rules = [
            "compute_expression",
            "remove_unused_while",
            "remove_unused_if_branch",
            "remove_nil_declaration",
            "convert_index_to_field",
            "remove_comments",
            "remove_method_definition",
            "remove_spaces",
            "remove_types",
            "remove_unused_variable",
            "remove_function_call_parens",
            "remove_empty_do",
            "remove_compound_assignment",
            "remove_interpolated_string",
            "filter_after_early_return",
            "group_local_assignment",
            "rename_variables",
        ]
        
        self.processing = False
        
        self.add_item(self.RuleSelect(self))
        self.add_item(self.GeneratorButton("readable", self))
        self.add_item(self.GeneratorButton("dense", self))
        self.add_item(self.GeneratorButton("retain_lines", self))
        self.add_item(self.ColumnInputButton(self))
        self.add_item(self.UnlimitedColumnButton(self))
        self.add_item(self.ApplyButton(self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your configuration.", ephemeral=True)
            return False
        return True

    def _save_config(self):
        darklua_user_settings[self.user_id] = {
            "generator": self.generator,
            "column_span": self.column_span,
            "selected_rules": self.selected_rules
        }
        import asyncio
        asyncio.create_task(save_darklua_settings())

    def get_content(self):
        return "select your darklua configuration"

    class RuleSelect(Select):
        def __init__(self, view):
            self.view_ref = view
            options = [
                discord.SelectOption(
                    label=rule, 
                    value=rule,
                    default=rule in view.selected_rules
                )
                for rule in view.available_rules[:25]
            ]
            super().__init__(
                placeholder="Select rules to apply...",
                min_values=0,
                max_values=len(options),
                options=options
            )

        async def callback(self, interaction: discord.Interaction):
            self.view_ref.selected_rules = list(self.values)
            self.view_ref._save_config()
            
            for option in self.options:
                option.default = option.value in self.view_ref.selected_rules
            
            await interaction.response.edit_message(
                content=self.view_ref.get_content(),
                view=self.view_ref
            )

    class GeneratorButton(Button):
        def __init__(self, generator: str, view):
            self.generator_type = generator
            self.view_ref = view
            style = discord.ButtonStyle.primary if view.generator == generator else discord.ButtonStyle.secondary
            super().__init__(label=f"Gen: {generator}", style=style, row=1)

        async def callback(self, interaction: discord.Interaction):
            self.view_ref.generator = self.generator_type
            self.view_ref._save_config()
            for item in self.view_ref.children:
                if isinstance(item, DarkluaConfigView.GeneratorButton):
                    item.style = discord.ButtonStyle.primary if item.generator_type == self.generator_type else discord.ButtonStyle.secondary
            await interaction.response.edit_message(
                content=self.view_ref.get_content(),
                view=self.view_ref
            )

    class ColumnInputButton(Button):
        def __init__(self, view):
            self.view_ref = view
            col_display = "unlimited" if view.column_span >= int(9e9) else str(view.column_span)
            super().__init__(label=f"Column: {col_display}", style=discord.ButtonStyle.primary, row=2)

        async def callback(self, interaction: discord.Interaction):
            modal = DarkluaConfigView.ColumnModal(self.view_ref, self)
            await interaction.response.send_modal(modal)

    class ColumnModal(discord.ui.Modal, title="Set Column Span"):
        def __init__(self, view, button):
            super().__init__()
            self.view_ref = view
            self.button_ref = button
            
            current_val = "" if view.column_span >= int(9e9) else str(view.column_span)
            self.column_input = discord.ui.TextInput(
                label="Column Span",
                placeholder="Enter a number (e.g., 80, 120)",
                default=current_val,
                required=True,
                max_length=10
            )
            self.add_item(self.column_input)

        async def on_submit(self, interaction: discord.Interaction):
            try:
                value = int(self.column_input.value)
                if value <= 0:
                    await interaction.response.send_message("Column span must be positive!", ephemeral=True)
                    return
                
                self.view_ref.column_span = value
                self.view_ref._save_config()
                
                self.button_ref.label = f"Column: {value}"
                
                for item in self.view_ref.children:
                    if isinstance(item, DarkluaConfigView.UnlimitedColumnButton):
                        item.style = discord.ButtonStyle.secondary
                
                await interaction.response.edit_message(
                    content=self.view_ref.get_content(),
                    view=self.view_ref
                )
            except ValueError:
                await interaction.response.send_message("Please enter a valid number!", ephemeral=True)

    class UnlimitedColumnButton(Button):
        def __init__(self, view):
            self.view_ref = view
            style = discord.ButtonStyle.primary if view.column_span >= int(9e9) else discord.ButtonStyle.secondary
            super().__init__(label="∞", style=style, row=2)

        async def callback(self, interaction: discord.Interaction):
            self.view_ref.column_span = int(9e9)
            self.view_ref._save_config()
            
            self.style = discord.ButtonStyle.primary
            for item in self.view_ref.children:
                if isinstance(item, DarkluaConfigView.ColumnInputButton):
                    item.label = "Column: unlimited"
            
            await interaction.response.edit_message(
                content=self.view_ref.get_content(),
                view=self.view_ref
            )

    class ApplyButton(Button):
        def __init__(self, view):
            self.view_ref = view
            super().__init__(label="Apply", style=discord.ButtonStyle.success, row=3)

        async def callback(self, interaction: discord.Interaction):
            if self.view_ref.processing:
                await interaction.response.send_message("Already processing...", ephemeral=True)
                return
            
            self.view_ref.processing = True
            await interaction.response.defer()
            
            filepath = f"./dumps/beautify/{self.view_ref.filename}"
            
            try:
                await applydarklua(
                    filepath,
                    self.view_ref.selected_rules,
                    {
                        "name": self.view_ref.generator,
                        "column_span": self.view_ref.column_span
                    }
                )
                
                await interaction.followup.send(
                    "Darklua processing complete!",
                    file=discord.File(filepath)
                )
                
                for item in self.view_ref.children:
                    item.disabled = True
                
                await interaction.message.edit(
                    content=self.view_ref.get_content(),
                    view=self.view_ref
                )
                
                self.view_ref.stop()
                
            except Exception as e:
                await interaction.followup.send(f"Error processing file: {str(e)}", ephemeral=True)
                self.view_ref.processing = False

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if hasattr(self, 'message') and self.message:
            try:
                await self.message.edit(view=self)
            except:
                pass

async def darklua_gui_cmd(msg):
    filename = await getfile(msg, "./dumps/beautify/")
    if not filename:
        return
    
    view = DarkluaConfigView(msg.author.id, filename)
    sent_msg = await msg.reply(content=view.get_content(), view=view)
    view.message = sent_msg
async def say_command(msg: discord.Message):
    
    texttosay = msg.content[len('.say '):]
    texttosay = escape_mentions(texttosay)
    await msg.reply(texttosay)

async def help_command(msg: discord.Message):
    BLUE = discord.Color.from_rgb(52, 152, 219)
    FIELD_MAX = 1000

    def _chunk_lines(lines, max_len=FIELD_MAX):
        chunks, current, cur_len = [], [], 0
        for line in lines:
            needed = len(line) + (1 if current else 0)
            if current and cur_len + needed > max_len:
                chunks.append("\n".join(current))
                current, cur_len = [], 0
            current.append(line)
            cur_len += needed
        if current:
            chunks.append("\n".join(current))
        return chunks or ["—"]

    def _add_chunked_field(embed, name, lines, suffix=""):
        chunks = _chunk_lines(lines)
        for i, chunk in enumerate(chunks):
            field_name = name if i == 0 else f"{name} (cont.)"
            if suffix and i == 0:
                field_name = f"{name}  {suffix}"
            embed.add_field(name=field_name, value=chunk, inline=False)

    skip = {".help", ".cmds"}
    pub = []

    for name, info in command_manager.commands.items():
        if name in skip:
            continue
        desc = info.get("description", "—")
        cd   = info.get("cooldown")
        line = f"`{name}` — {desc}" + (f" *(cd: {cd}s)*" if cd else "")
        pub.append(line)

    dumper_lines = [
        "`/l` `/k` — Full HTTP log dump (main dumper)",
        "`/dump` — Slow dump (ib2 forks, basic MoonSec)",
        "`/ld` — Loadstring log dump",
        "`/http` — HTTP log dump",
        "`/udump` — Fast MoonSec V3 unpack dump",
        "`/msat` — MoonSec AntiTamper / constant encryption dump",
        "`/ibdump` — IronBrew 2 / LuaObfuscator dump",
        "`/luraph` — Luraph dump (DMs only)",
    ]

    embed = discord.Embed(
        title="✦ Rezzy Env Logger Bot",
        description="Lua deobfuscation, obfuscation, and more.",
        color=BLUE
    )

    if pub:
        _add_chunked_field(embed, "◈ Commands", pub)

    _add_chunked_field(embed, "◈ Env Logger Commands", dumper_lines)

    embed.set_footer(text="Rezzy Env Logger · discord.gg/f8XjPE2c6Y")
    await msg.reply(embed=embed)
async def nonfunc(msg):
    pass
async def makeit_rename(inpath,outpath):
    try:
        with open(inpath, "r", encoding="utf-8", errors="replace") as infile:
            code = infile.read()
    except Exception as er:
        print(f"makeit_rename read fail: {er}")
        return False

    if not code:
        print("makeit_rename: no code content provided")
        return False

    try:
        response = await bypass.asyncpost(
            "https://renamer-api.vercel.app/api/rename",
            {"code": code},
            headers={
                "x-api-key": "33ms-DHJHS-24633",
                "Content-Type": "application/json"
            }
        )
    except Exception as er:
        print(f"makeit_rename request fail: {er}")
        return False
    renamed_code = None
    if isinstance(response, dict):
        renamed_code = response.get("renamedCode")
    elif response:
        print(f"[rename] unexpected response type: {type(response)} — {repr(response)[:200]}")
    if not renamed_code:
        print(f"makeit_rename: unexpected response {response}")
        return False
    try:
        with open(outpath, "w", encoding="utf-8", newline="\n") as outfile:
            outfile.write(renamed_code)
    except Exception as er:
        print(f"makeit_rename write fail: {er}")
        return False
    try:print("Rename credits left:",response.get("remainingCredits"))
    except:pass
    return True
async def rename_cmd(msg):
    rename_dir = "./dumps/rename/"
    os.makedirs(rename_dir, exist_ok=True)
    filename = await getfile(msg, rename_dir)
    if not filename:
        return
    input_path = os.path.join(rename_dir, filename)
    output_path = os.path.join(rename_dir, f"{os.path.splitext(filename)[0]}_renamed.lua")
    async with msg.channel.typing():
        success = await makeit_rename(input_path, output_path)
    if not success or not os.path.isfile(output_path):
        await msg.reply("Renaming failed.")
        return
    try:
        await msg.reply(file=discord.File(output_path))
    except Exception as er:
        print(f".rename send error: {er}")
        await msg.reply("Renamed file is ready but could not be sent. Ping Rezzy Env Logger if you need it.")
async def msdeobf(msg,no_attach_error=True):
    if msg.channel.id==DUMP_CHANNEL_ID and not (msg.attachments or "http" in msg.content):
        await msg.delete()
        return
    os.makedirs("./dumps/original/", exist_ok=True)
    os.makedirs("./dumps/dumped/", exist_ok=True)
    filename = await getfile(msg, "./dumps/original/", no_attach_error=no_attach_error)
    if not isinstance(filename, str):
        return
    inpath = f"./dumps/original/{filename}"
    try:
        with open(inpath, "rb") as _f:
            _file_bytes = _f.read()
    except Exception as _e:
        await msg.reply(f"`Failed to read uploaded file: {_e}`")
        return
    try:
        _form = aiohttp.FormData()
        _form.add_field(
            name="file",
            value=io.BytesIO(_file_bytes),
            filename=filename,
            content_type="text/plain",
        )
        async with aiohttp.ClientSession() as _sess:
            async with _sess.post(
                "https://leakd.up.railway.app/moonsec",
                data=_form,
                timeout=aiohttp.ClientTimeout(total=90),
            ) as _resp:
                _j = await _resp.json(content_type=None)
    except Exception as _e:
        print(f"[msdeobf] LeakD API error: {_e}")
        await msg.reply(f"`Deobfuscation API unavailable: {_e}`")
        return
    if not _j.get("success"):
        _err = _j.get("error", "Unknown API error")
        if msg.channel.id==DUMP_CHANNEL_ID:
            await softerror(msg,f"Deobfuscation failed: {_err}. For non-moonsec v3 scripts use .l in <#{CMDS_CHANNEL_ID}> (its free)",12)
        else:
            await msg.reply(f"`Deobfuscation failed: {_err}`")
        return
    _raw_code = _j.get("deobfuscated_code", "")
    _credit = "-- This script was deobfuscated using Rezzy Env Logger Moonsec Deobfuscator | https://discord.gg/f8XjPE2c6Y\n\n"
    _lines = _raw_code.splitlines(keepends=True)
    _cleaned = [_l for _l in _lines if "leakd" not in _l.lower() and "Deobfuscated by" not in _l]
    _final_code = _credit + "".join(_cleaned)
    lua_output_path = f"./dumps/dumped/{filename}"
    with open(lua_output_path, "w", encoding="utf-8") as _f:
        _f.write(_final_code)
    await luabeautify(lua_output_path, ["remove_comments"])
    webhooks = sexwebhooks(msg, lua_output_path, True)
    rename_view = RenameLuaView(lua_output_path, "", msg.author.id)
    text = f"Here you go twin! <@{msg.author.id}>"
    try:
        sent_msg = await msg.reply(text, file=discord.File(lua_output_path), view=rename_view)
        if rename_view:
            rename_view.message = sent_msg
    except Exception as _e:
        print(f"[msdeobf] Reply error: {_e}")
        try:
            await msg.channel.send(f"<@{msg.author.id}> Here is your deobfuscated script!", file=discord.File(lua_output_path))
        except Exception:
            pass
async def luaobf_deobf(msg):
    result, filename = await luafilehandler(msg,"badluaobf.lua","./dumps/original/",lune=True)
    if not result or not filename:
        return
    elif result and "success" in result.stdout:
        try:
            await applydarklua('./dumps/dumped/' + filename,[
                "compute_expression",
                "remove_unused_while",
                "remove_unused_if_branch",
                "remove_nil_declaration",
                "convert_index_to_field"
        ])
            await luabeautify('./dumps/dumped/' + filename)
        except Exception as er:
            print("beauty error",er)
        webhooks=sexwebhooks(msg,'./dumps/dumped/' + filename,True)
        file = discord.File('./dumps/dumped/' + filename)
        await msg.reply(webhooks,file=file)
    else:
        await msg.reply(f"`This only works for luaobfuscator's string encryption (\"Chaotic Good\")`")
        print("Deobf error:\n"+result.stderr)
async def solara_cmd(msg):
    info = bypass.getsolarainfo()
    rblxinfo = bypass.getrobloxversioninfo()
    await msg.reply(f'Download: {info["BootstrapperUrl"]}\n{(info["SupportedClient"]==rblxinfo["clientVersionUpload"] and ":white_check_mark: Solara is currently updated") or ":broken_heart: Solara is currently **NOT** updated"}\nChangelog:```diff\n{info["Changelog"].replace("[+]","+").replace("[-]","-")}```')
async def beautify_cmd(msg):
    print("hi0")
    filename = await getfile(msg,f"./dumps/beautify/")
    print("hi")
    if filename:
        if await luabeautify(f"./dumps/beautify/{filename}",[
            "compute_expression"
        ]):
            file = discord.File(f"./dumps/beautify/{filename}")
            await msg.reply(file=file)
        else:
            await msg.reply("`Unable to beautify`")
    else:
        print("unable to get file heh")
async def minify_cmd(msg):
    filename = await getfile(msg,"./dumps/beautify/")
    if filename:
        if await applydarklua(f"./dumps/beautify/{filename}",[
            "convert_index_to_field",
            "compute_expression",
            "filter_after_early_return",
            "group_local_assignment",
            "remove_comments",
            "remove_method_definition",
            "remove_nil_declaration",
            "remove_spaces",
            "remove_types",
            "remove_unused_if_branch",
            "remove_unused_variable",
            "remove_unused_while",
            "remove_function_call_parens",
            {
                "rule": "rename_variables",
                "globals": ["$default", "$roblox"],
            },
        ],{ "name": "dense", "column_span": int(9e9) }):
            file = discord.File(f"./dumps/beautify/{filename}")
            await msg.reply(file=file)
        else:
            await msg.reply("`Unable to minify (darklua processing failed).`")
def lzw_compress(s: bytes) -> str:
    dictionary = {bytes([i]): bytes([i, 0]) for i in range(256)}
    a, b = 0, 1
    def nextcode():
        nonlocal a, b, dictionary
        c = bytes([a, b])
        a += 1
        if a >= 256:
            a = 0
            b += 1
            if b >= 256:
                dictionary = {bytes([i]): bytes([i, 0]) for i in range(256)}
                b = 1
        return c
    w = s[:1]
    out = []
    for c in s[1:]:
        c = bytes([c])
        if w + c in dictionary:
            w = w + c
        else:
            dictionary[w + c] = nextcode()
            out.append(dictionary.get(w, bytes([w[0], 0])))
            w = c
    out.append(dictionary.get(w, bytes([w[0], 0])))
    raw = b"".join(out)
    return raw.hex()
async def compress_cmd(msg):
    filename = await getfile(msg,"./dumps/beautify/")
    if filename:
        await applydarklua(f"./dumps/beautify/{filename}",[
            "convert_index_to_field",
            "compute_expression",
            "filter_after_early_return",
            "group_local_assignment",
            "remove_comments",
            "remove_method_definition",
            "remove_nil_declaration",
            "remove_spaces",
            "remove_types",
            "remove_unused_if_branch",
            "remove_unused_variable",
            "remove_unused_while",
            "remove_function_call_parens",
            {
                "rule": "rename_variables",
                "globals": ["$default", "$roblox"],
            },
        ],{ "name": "dense", "column_span": int(9e9) })
        compressed_code="return(function(a,b,c,d,e)for f=0,255 do a[b(f,0)]=b(f)end function d(f,g,h,i)if h>255 then h=0 i+=1 if i>255 then g={}i=1 end end g[b(h,i)]=f h+=1 return g,h,i end e=({('"+lzw_compress(open(f"./dumps/beautify/{filename}","rb").read())+"'):gsub('..',function(f)return b(tonumber(f,16))end)})[1]local f,g,h,i,j,k,l=#e,{},0,1,{},1,c(e,1,2)j[k]=a[l]or g[l]k+=1 for m=3,f,2 do local n,o=c(e,m,m+1),a[l]or g[l]local p=a[n]or g[n]if p then j[k]=p k+=1 g,h,i=d(o..c(p,1,1),g,h,i)else local q=o..c(o,1,1)j[k]=q k+=1 g,h,i=d(q,g,h,i)end l=n end return loadstring(table.concat(j))end)({},string.char,string.sub)(...)"
        buffer = io.StringIO()
        buffer.write(compressed_code)
        buffer.seek(0)
        await msg.reply(file=discord.File(buffer,"compressed.lua"))
def to_buffer(string=None,raw=None):
    if string:
        buffer = io.StringIO()
        buffer.write(string)
        buffer.seek(0)
        return buffer
    elif raw:
        buffer = io.BytesIO(raw)
        buffer.seek(0)
        return buffer
async def gen_cmd(msg):
    smsg=msg.content.split(" ")
    if smsg==1:
        await msg.reply("You didnt put a prompt you fucking idiot")
        return
    botmsg = await msg.reply("`Generating...`")
    image = await bypass.cloudflare_gen(" ".join(smsg[1:]))
    if image:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            temp_file.write(image)
            temp_file.seek(0)
            await botmsg.delete()
            await msg.reply(file=discord.File(temp_file.name, "generated_image.png"))
    else:
        await botmsg.delete()
        await msg.reply("`couldn't generate image`")
async def deobfhandler(msg):
    isfullcode=True
    try:print(f"lol {msg.author.name} did {msg.content}")
    except:pass
    randomfilename = await getfile(msg, "./deobfuscate/.in/")
    if not randomfilename:
        return False,False,False
    basename = randomfilename[:-4]
    try:
        process1 = await asyncio.create_subprocess_exec(
            *([NODE_PATH, './index.js', f'./.in/{randomfilename}', f'./.out/{basename}.luac']),
            cwd='./deobfuscate',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
    except FileNotFoundError:
        print(f"[deobfhandler] node not found — deobf unavailable")
        return False, False, False
    stdout1, stderr1 = await process1.communicate()
    process1.stdout = stdout1.decode("utf-8")
    process1.stderr = stderr1.decode("utf-8")
    return process1, basename, False
    process2 = await asyncio.create_subprocess_exec(
        './deobfuscate/Luadec51.exe', f'./deobfuscate/.out/{basename}.luac',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout2, stderr2 = await process2.communicate()
    process2.stdout = stdout2.decode("utf-8")
    process2.stderr = stderr2.decode("utf-8")
    if process2.stdout and not process2.stderr:
        with open("./deobfuscate/.out/" + randomfilename, 'w') as outfile:
            outfile.writelines(process2.stdout.split("\n")[3:])
    else:
        print("result1",process2.stdout)
        process3 = await asyncio.create_subprocess_exec(
            'java','-jar','./deobfuscate/unluac.jar', f'./deobfuscate/.out/{basename}.luac',"-o", f"./deobfuscate/.out/{randomfilename}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout3, stderr3 = await process3.communicate()
        process3.stdout = stdout3.decode("utf-8")
        process3.stderr = stderr3.decode("utf-8")
        if process3.stderr:
            isfullcode=False
    return process1, basename,isfullcode
async def ib2_deobf(msg):
    result, filename,isfullcode = await deobfhandler(msg)
    if not result or not filename:
        print(result,filename)
        return
    elif result and "success" in result.stdout:
        decomp_fail=not os.path.isfile(f'./deobfuscate/.out/{filename}.lua')
        files = []
        if not decomp_fail: files.append(discord.File(f'./deobfuscate/.out/{filename}.lua'))
        files.append(discord.File(f'./deobfuscate/.out/{filename}.luac'))        
        await msg.reply(decomp_fail and "Decompilation failed. Download the luac file and just decompile it at https://luadec.metaworm.site yourself" or (not isfullcode and "*The decompiled code doesnt seem to be complete*\n" or "")+"You can decompile the .luac file at https://luadec.metaworm.site/ for a better result",files=files)
    else:
        await msg.reply(f"`This only works on ironbrew 2`")
        print("Deobf error:\n"+result.stderr)
async def meow_cmd(msg):
    await msg.reply("meow " * random.randint(1,5))
async def luau_decompile_api(filelocation,outpath):
    content=open(filelocation,"rb").read()
    result=await bypass.asyncpost("https://api.lua.expert/decompile",{"script": b64encode(content).decode()},returnResponseJson=False)
    open(outpath,"w").write(result)
    return True
    
async def roblox_decompile_cmd(msg):
    decompile_dir = "./dumps/decompile/"
    os.makedirs(decompile_dir, exist_ok=True)
    randomfilename = await getfile(msg, decompile_dir, mode="binary", usehash=True, file_extension=".luac")
    if not randomfilename:
        return
    outpath = f'{decompile_dir}{randomfilename[:-1]}'
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    process = await asyncio.create_subprocess_exec(
        './medal51/luau-lifter.exe', f'{decompile_dir}{randomfilename}', "-e",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    process.stdout = stdout.decode("utf-8")
    process.stderr = stderr.decode("utf-8")
    if process.stderr:
        try:
            if not await luau_decompile_api(f'{decompile_dir}{randomfilename}',outpath):
                raise Exception("Decompilation API failed")
        except Exception as er:
            print(er)
            await msg.reply("Failed 💔")
            return
    else:
        with open(outpath, 'w', encoding='utf-8') as outfile:
            outfile.writelines(process.stdout)

    await luabeautify(outpath,["remove_comments"])
    await msg.reply(file=discord.File(outpath))

async def claim_license(msg):
    if is_localhost: return await msg.reply("Claiming is currently unavailable, try again later")
    smsg = msg.content.split(" ")
    if len(smsg) < 2:
        await msg.reply("Please provide a license key")
        return
    key = smsg[1]
    await msg.reply(await licensing.claim(msg.author.id,client,key))
async def dumpConfig_cmd(msg):
    if msg.author.id in malicious_users: return await msg.reply("You are not allowed to use this command anymore :'(")
    embed = discord.Embed(title="Settings for the holy .l")
    embed.add_field(name="Varnames", value="When enabled gives variables names based on context", inline=False)
    embed.add_field(name="usesimplefunctions", value="When enabled doesnt explore found functions", inline=False)
    embed.add_field(name="watchoutforloop", value="Will give the iconic 'infinitelooperror' when it detects repeating code.", inline=False)
    embed.add_field(name="spynilglobals", value="Will spy all globals, even if they might not be defined in a normal env", inline=False)
    embed.add_field(name="hook_op", value='Attempts to hook stuff like "==", "or" (**EXPERIMENTAL**)', inline=False)
    embed.add_field(name="hook_op_default_return", value="Returns either a spy value, the value it would've been by default, true, or false on every hooked opcode", inline=False)
    view = dumpConfig(msg.author)
    await msg.reply(embed=embed, view=view)

async def get_recovery_cmd(msg):
    if not isinstance(msg.channel, discord.DMChannel):
        await softerror(msg,"You can only use this command in dms!")
        return
    await msg.reply(f"||{await licensing.get_recovery(msg.author)}||")
async def cmds_access_cmd(msg):
    user_profile=requests.request("GET", f"https://discord.com/api/v9/users/{msg.author.id}/profile", data="", headers=headers, params={"type":"popout","with_mutual_guilds":"true","with_mutual_friends":"true","with_mutual_friends_count":"false"}).json()["user"]
    if "clan" in user_profile and user_profile["clan"] and "tag" in user_profile["clan"] and user_profile["clan"]["tag"]=="rezzy":
        await softerror(msg,"✅ You're using the Rezzy Env Logger server tag!")
    else:
        await softerror(msg,"You need to be using the Rezzy Env Logger tag!")

mv_data=loads(open("mvdata.json").read())
mv_save_in_use=False
async def save_mv_data():
    global mv_save_in_use
    if mv_save_in_use:
        return
    mv_save_in_use=True
    with open("mvdata.json", "w") as f:
        f.write(dumps(mv_data))
    mv_save_in_use=False
async def moonveil_obfuscate(msg):
    if msg.author.id in mv_data and mv_data[msg.author.id] > time.time() - 86400:
        await msg.reply(f"You have already used your free daily obfuscation, wait {seconds_to_str(round((mv_data[msg.author.id] + 86400) - time.time()))} to use it again")
        return
    content=await getfile(msg)
    if not content:
        return
    mv_data[msg.author.id] = time.time()
    await save_mv_data()
    payload = {
        "options": {
            "cffDecomposeExpr": False,
            "cffEnable": True,
            "cffHoistLocals": True,
            "cffWrapBlocks": True,
            "mangleEnable": True,
            "mangleGlobals": True,
            "mangleNamedIndex": True,
            "mangleNumbers": False,
            "mangleSelfCalls": True,
            "mangleStrings": True,
            "prettify": False,
            "removeCompoundAssign": True,
            "removeIfExpr": True,
            "vmEnable": True,
            "vmWrapScript": True
        },
        "script": content
    }
    response=await bypass.asyncpost("https://moonveil.cc/api/obfuscate",payload,headers={
        "Authorization": f"Bearer {MV_API_KEY}",
        "Content-Type": "application/json",
    },returnResponseJson=False)
    buffer = io.StringIO()
    buffer.write(response)
    buffer.seek(0)
    await msg.reply(file=discord.File(buffer, filename="moonveil.lua"))
async def goofy_fus(msg):
    content=await getfile(msg)
    if not content:
        return
    response=await bypass.asyncpost("https://goofyscator.lua.cz/obfuscate",{
        "source": content,
        "settings": {
            "dontModifyBytecode": True,
            "hexNumbers": True,
            "renameGlobals": False,
            "generator": "Shuffled"
        }
    })
    if response["status"]!="success":
        await msg.reply("Error while obfuscating")
        return
    buffer = io.StringIO()
    buffer.write("--[[ obfuscated @ discord.gg/f8XjPE2c6Y ]]\n"+response["result"])
    buffer.seek(0)
    await msg.reply(file=discord.File(buffer, filename="goofyscator.lua"))
async def asyncget(url,headers=None,params=None,proxy=None,proxy_auth=None,getjson=False):
    async with aiohttp.ClientSession(
            headers=headers,
        ) as session:
            async with session.get(
                url,
                params=params,
                proxy=proxy,
                proxy_auth=proxy_auth,
                ssl=ssl_context,
            ) as resp:
                if getjson:
                    return await resp.json()
                return await resp.text()
async def asyncpost(url,headers=None,data=None):
    async with aiohttp.ClientSession(
            headers=headers
        ) as session:
            async with session.post(
                url, data=data
            ) as resp:
                return await resp.text()
def _detect_obf(content):
    regexes={
        r"return [A-z0-9_]+\([0-9A-z_]+\(\),[A-z0-9,_\{\}\)\(]+\)": "ib2 (or similar)",
        r"newproxy,...metatable,...metatable,select,":"prometheus",
        r"\(\[\[This file was protected with MoonSec V3[A-z9_#\s]+\]\]\):gsub\('\.\+', \(function\([A-z0-9_]+\) [A-z0-9_]+":"moonsec v3",
        r"local v0=string\.char;local v1=string\.byte;local v2=string.sub;local v3=bit32 or bit ;local v4=v3\.bxor;local v5=table\.concat;local v6=table\.insert;local function v7":"luaobfuscator.com string enc"
    }
    for pattern, result in regexes.items():
        if re.findall(pattern,content):
            return result
async def detect_cmd(msg):
    content = await getfile(msg)
    if not content:
        return
    _detect_res = _detect_obf(content)
    leakd_results = []
    error_msg = None
    try:
        raw_bytes = content.encode() if isinstance(content, str) else content
        form = aiohttp.FormData()
        form.add_field(
            name="file",
            value=io.BytesIO(raw_bytes),
            filename="script.lua",
            content_type="text/plain",
        )
        async with aiohttp.ClientSession() as _sess:
            async with _sess.post(
                "https://leakd.up.railway.app/detect",
                data=form,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as _resp:
                _j = await _resp.json(content_type=None)
        if _j.get("success"):
            _all = (
                _j.get("results")
                or _j.get("all_results")
                or _j.get("probabilities")
                or _j.get("candidates")
            )
            if isinstance(_all, list):
                for _entry in _all:
                    _name = _entry.get("name", "Unknown")
                    _conf = _entry.get("confidence", 0)
                    leakd_results.append((_name, _conf))
                leakd_results.sort(key=lambda x: x[1], reverse=True)
            if not leakd_results:
                _top = _j.get("top_result", {})
                if _top:
                    leakd_results.append((_top.get("name", "Unknown"), _top.get("confidence", 0)))
        else:
            error_msg = _j.get("error", "Detection API returned an error")
    except Exception as _e:
        print(f"[detect_cmd] LeakD API error: {_e}")
        error_msg = f"Detection API unavailable ({_e})"
    embed = discord.Embed(title="Obfuscator Detection", color=0x3498DB)
    if _detect_res:
        embed.add_field(name="Pattern Match", value=f"**{_detect_res}**", inline=False)
    if leakd_results:
        lines = []
        for i, (name, confidence) in enumerate(leakd_results):
            filled = int(confidence / 10)
            bar = "█" * filled + "░" * (10 - filled)
            marker = "🏆 " if i == 0 else ""
            lines.append(f"{marker}**{name}** — `{confidence}%`  `{bar}`")
        embed.add_field(
            name=f"Detected Obfuscators ({len(leakd_results)})",
            value="\n".join(lines),
            inline=False,
        )
    if error_msg:
        embed.add_field(name="Detection Failed", value=f"`{error_msg}`", inline=False)
    embed.set_footer(text="Detect obf using LeakD detect API by Prostone | discord.gg/7SE449kTQw")
    await msg.reply(embed=embed)
    asyncio.create_task(send_discord_webhook(WEBHOOK_URL,"huge"))

async def obf77fus(msg):
    result, filename = await luafilehandler(msg,"","./unobfuscated/",ssfus=True)
    if not result or not filename:
        return
    elif result and "Done" in result.stdout:
        file = discord.File('./obfuscated/' + filename)
        await msg.reply(file=file)
    else:
        await msg.reply(f"`77fus obfuscation failed`")
        print("Obf error:\n"+result.stderr)
        print(result.stdout)

async def medal51_decompile_on_file(inpath,outpath):
    try:
        process = await asyncio.create_subprocess_exec(
            *(["./medal51/lua51-lifter.exe","--file",inpath,"--out",outpath] ),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
    except FileNotFoundError as _e:
        print(f"[medal51] Binary not found (Windows-only .exe on Linux): {_e}")
        return None, False
    try:
        stdout_task = asyncio.create_task(read_stream(process.stdout))
        stderr_task = asyncio.create_task(read_stream(process.stderr))
        await asyncio.wait_for(process.wait(), timeout=40)
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        process.stdout = await stdout_task
        process.stderr = await stderr_task
        return process,False
    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
    process.stdout = await stdout_task
    process.stderr = await stderr_task
    return process, True
async def medal51_cmd(msg):
    filename = await getfile(msg, "./dumps/decompile/", mode="binary", usehash=True, file_extension=".luac")
    print(filename)
    if not filename:
        return
    outfilepath = f'./dumps/decompile/{filename[:-5]}_medal51.lua'
    process, success = await medal51_decompile_on_file(f'./dumps/decompile/{filename}',outfilepath)
    print(process.stderr)
    if not os.path.isfile(outfilepath):
        await msg.reply("Decompilation failed 💔")
        return
    await luabeautify(outfilepath,["remove_comments"])
    await msg.reply(file=discord.File(outfilepath))

async def decompile_oracle(input_path: str, output_path: str,key:str):
    with open(input_path, "rb") as f:
        script_data = f.read()

    encoded = b64encode(script_data).decode("utf-8")

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://oracle.mshq.dev/decompile",
            json={"script": encoded},
            headers={"Authorization": f"Bearer {key}"}
        ) as res:
            text = await res.text()

            if res.status in (200, 402, 429):
                with open(output_path, "w", encoding="utf-8") as out:
                    out.write(text)
            elif res.status == 500:
                print(await res.text())
                raise Exception("-- Decompilation failed!")
            elif res.status == 400:
                raise Exception("-- Update the decompiling script")
            else:
                raise Exception(f"-- Something went wrong when decompiling: {res.status}")

async def oracle_decompile_cmd(msg,key):
    filename = await getfile(msg, "./dumps/decompile/", mode="binary", usehash=True, file_extension=".luac")
    if not filename:
        return
    outfilepath = f'./dumps/decompile/{filename[:-5]}_oracle.lua'
    try:await decompile_oracle(f'./dumps/decompile/{filename}',outfilepath,key)
    except Exception as er: print(er);await msg.reply("Decompilation failed 💔");return
    await msg.reply(file=discord.File(outfilepath))

async def oracle_key_cmd(msg):
    global oracle_keys
    smsg = msg.content.split(" ")
    if len(smsg) < 2:
        await msg.reply("Please provide a key")
        return
    key = smsg[1]
    oracle_keys[msg.author.id] = key!="remove" and key or None
    open("oracle_keys.json","w").write(dumps(oracle_keys))
    await msg.reply("Key set successfully, you can now use .msdeobf and .decompile with oracle!")

def decompile_manager(msg):
    bytecode_type=len(msg.content.split(" "))>1 and msg.content.split(" ")[1]
    if not bytecode_type and oracle_keys[msg.author.id]:
        return oracle_decompile_cmd(msg,oracle_keys[msg.author.id])
    elif bytecode_type in ["roblox","rbx","luau","rluau"]:
        return roblox_decompile_cmd(msg)
    else:
        return medal51_cmd(msg)
async def get_cmd(msg):
    if msg.author.id in malicious_users: print("unallowed");return await msg.reply("You are not allowed to use this command anymore :'(")
    linkcontent=await getlinkcontent(msg.content)
    if not linkcontent:
        await msg.reply("You didnt provide a link or the link didnt return a body")
    else:
        await msg.reply(file=string_to_discordfile(linkcontent, "rezzy_env_logger_get.lua"))

async def pastefy_upload(content):
    response=await bypass.asyncpost("https://pastefy.app/api/v2/paste",{
        "content":content,
        "title":"uploaded by Rezzy Env Logger",
        "encrypted":False,"visibility":"UNLISTED","type":"PASTE","tags":[],"ai":True
    })
    if not response.get("success"):
        return False
    return response['paste']['raw_url']
async def rubis_upload(content):
    response = await asyncpost("https://api.rubis.app/v2/scrap?public=true&title=uploaded+by+rezzy-env-logger",
        headers={"Content-Type": "text/plain"},
        data=content)
    try:
        result = loads(response)
        if not result.get("success"):
            return False
        return result['raw']
    except:
        return False
async def pastebin_upload(content):
    data = urllib.parse.urlencode({
        "api_dev_key": "ObMseOsyB4VO6lEM8cbeVi6LTE7E9fvL",
        "api_paste_code": content,
        "api_paste_name": "uploaded by discord.gg/f8XjPE2c6Y",
        "api_paste_format":"lua",
        "api_user_key": "67d24d99b9ee958a49b8d63610624e7a",
        "api_paste_private": "0",
        "api_paste_expire_date": "N",
        "api_option": "paste",
    })
    response = await asyncpost(
        "https://pastebin.com/api/api_post.php",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=data)
    print(response)
    if not isinstance(response, str) or response.startswith("Bad API request"):
        return False
    paste_id = response.strip().split("/")[-1]
    return f"https://pastebin.com/raw/{paste_id}"
async def debian_upload(content):
    extra_newlines=2-content.count("\n")
    res=await bypass.asyncpost(
        "https://paste.debian.net/api/v1/paste", {
            "code": content+("\n"*extra_newlines if extra_newlines>0 else ""),
            "poster":"by Rezzy Env Logger",
            "lang":"luau",
            "expire":0
        },
        headers={"Content-Type": "application/json"}
    )
    return f"https://paste.debian.net/plainh/{res['id']}"
uploaders={
    "pastebin":pastebin_upload,
    "rubis":rubis_upload,
    "pastefy":pastefy_upload,
    "debian":debian_upload,
}
async def upload_cmd(msg):
    smsg=msg.content.split(" ")
    option=len(smsg) > 1 and smsg[1] or "pastefy"
    content=await getfile(msg)
    if not content:return
    url=await (uploaders.get(option) or pastefy_upload)(content)
    if not url:
        await msg.reply("Error while uploading")
        return
    await msg.reply(f"{url}\n\n`loadstring(game:HttpGet'{url}')()`")

async def prom_deobf_api_cmd(msg):
    content=await getfile(msg)
    if not content:
        return
    await msg.channel.typing()
    try:
        raw_bytes = content.encode() if isinstance(content, str) else content
        form = aiohttp.FormData()
        form.add_field(
            name="file",
            value=io.BytesIO(raw_bytes),
            filename="prometheus_script.lua",
            content_type="text/plain",
        )
        async with aiohttp.ClientSession() as _sess:
            async with _sess.post(
                "https://leakd.up.railway.app/prometheus",
                data=form,
                timeout=aiohttp.ClientTimeout(total=90),
            ) as _resp:
                response = await _resp.json(content_type=None)
    except Exception as e:
        print("leakd prometheus:", e)
        return await msg.reply("Error while deobfuscating")
    if not isinstance(response, dict) or not response.get("success"):
        _err = (isinstance(response, dict) and response.get("error")) or "Unexpected API response"
        print("leakd prometheus error:", response)
        return await msg.reply(f"Error while deobfuscating: {_err}")
    result = response.get("deobfuscated_code", "")
    if not result:
        return await msg.reply("Error while deobfuscating (empty result).")
    webhooks=sexwebhooks(msg,content=result,attachfile=True)
    await msg.reply("Deobfuscated by LeakD Prometheus Deobfuscator by Prostone"+(webhooks and '\n'+webhooks or ''),file=string_to_discordfile(await luabeautify(content=result), "deobfuscated.lua"))

async def protect_webhook_cmd(msg):
    webhook_url = extract_link(msg.content)
    if not webhook_url:
        await msg.reply("Please provide a valid webhook URL!")
        return
    
    if "/webhooks/" not in webhook_url:
        await msg.reply("Invalid webhook URL!")
        return
    
    try:
        end = webhook_url.split("/webhooks/")[1]
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://webhook.whimper.xyz/create/{urllib.parse.quote(end)}",
                ssl=ssl_context
            ) as resp:
                if resp.status != 200:
                    await msg.reply("Failed to protect webhook!")
                    return
                data = await resp.json()
        
        hex_key = data.get("hexKey")
        encrypted = data.get("encrypted")
        
        if not hex_key or not encrypted:
            await msg.reply("Failed to protect webhook!")
            return
        
        protected_code = f'''-- MAKE SURE TO OBFUSCATE THIS CODE! KEEP CODE BELOW IN THE FILE\nlocal a={{}}for b=0,255 do a[b]=string.char(b)end local function stringchar(b)local c=a[b]or string.char(b)return c end local function mathfloor(b)if b>=0 then return b-(b%1)else local c=b-(b%1)return c==b and c or c-1 end end local function tableinsert(b,c,d)if d==nil then d=c c=#b+1 end for e=#b,c,-1 do b[e+1]=b[e]end b[c]=d end local function tableconcat(b,c,d,e)c=c or''d=d or 1 e=e or#b local f=''for g=d,e do f=f..b[g]if g<e then f=f..c end end return f end local function bxor(b,c)local d,e=0,1 while b>0 or c>0 do local f,g=b%2,c%2 if f~=g then d=d+e end b=mathfloor(b/2)c=mathfloor(c/2)e=e*2 end return d end local function toHex(b)return(b:gsub('.',function(c)return string.format('%02X',string.byte(c))end))end local function xorCrypt(b,c)local d={{}}for e=1,#b do local f,g=b:byte(e),c:byte((e-1)%#c+1)tableinsert(d,stringchar(bxor(f,g)))end return tableconcat(d)end local function encrypt(b)return toHex(xorCrypt(b,\"{hex_key}\"))end\nlocal webhook=\"https://webhook.whimper.xyz/send/{encrypted}\"\n-- DONT REMOVE THE CODE UNTIL HERE\n-- you can use the webhook like this!\nrequest({{\n  Url=webhook,\n  Method=\"POST\",\n  Body=encrypt(game:GetService(\"HttpService\"):JSONEncode({{content=\"Hello world!\"}})),\n}})'''
        
        await msg.reply(file=string_to_discordfile(protected_code, "protected_webhook.lua"))
    except Exception as e:
        print(f"protect_webhook error: {e}")
        await msg.reply("Failed to protect webhook!")

command_manager.commands={
    ".obf": {
        "func": nonfunc,
        "description": "Obfuscate your lua code. Options: weak"
    },
    ".moonveil":{
        "func": moonveil_obfuscate,
        "description": "Get a free daily obfuscation using moonveil.cc",
        "cooldown": 10
    },
    ".goofy":{
        "func": goofy_fus,
        "description": "Free obfuscation using goofyscator by 1xayd1",
        "cooldown": 10
    },
    ".get":{
        "func": get_cmd,
        "description": "Fetch content from a link!",
        "cooldown": 10,
    },
    ".upload":{
        "func": upload_cmd,
        "description": "Upload a file! Options: pastebin, rubis, debian, pastefy (default: pastefy)",
        "cooldown": 10,
    },
    ".msdeobf":{
        "func": msdeobf,
        "description": "Moonsec deobfuscation, can be used for free in #moonsec-deobf. Decompiled with medal fork!",
        "cooldown": 10,
        "allow_channels":[CMDS_CHANNEL_ID]
    },
    ".detect":{
        "func":detect_cmd,
        "description":"Detect the obfuscator that a script is using",
        "cooldown":3,
    },
    ".77fus":{
        "func": obf77fus,
        "description": "Breens 77fuscator!"
    },
    ".ibs":{
        "func": nonfunc,
        "description": "ib2 based obfuscation. Probably more secure than moonsec, creates big files"
    },
    ".beautify":{
        "func":beautify_cmd,
        "description":"Beautify lua code."
    },
    ".darklua":{
        "func": darklua_gui_cmd,
        "description": "darklua process panel",
        "cooldown": 5
    },
    ".help":{
        'func':help_command,
        'description':'Displays help message'
    },
    ".cmds":{
        'func':help_command,
        'description':'Displays help message'
    },
    ".ironobf":{
        "func": nonfunc,
        "description": "Obfuscation around the level of luaobfuscator"
    },
    ".ib2":{
        "func": nonfunc,
        "description": "Pretty bad obfuscation but the most performant one, also has very good compatibility. Good for huge scripts"
    },
    ".deobf":{
        "func": luaobf_deobf,
        "description": "Decrypt strings in string encrypted luaobfuscator scripts"
    },
    ".promdeobf":{
        "func": prom_deobf_api_cmd,
        "description": "Deobfuscate prometheus files using LeakD",
        "cooldown":10,
    },
    ".ibdeobf":{
        "func": ib2_deobf,
        "description": "Deobfuscate ironbrew 2 scripts.",
        "allow_channels":[CMDS_CHANNEL_ID]
    },
    ".minify":{
        "func": minify_cmd,
        "description": "minify your script"
    },
    ".compress":{
        "func":compress_cmd,
        "description": "compress your script"
    },
    ".byp":{
        "func": nonfunc,
        "description": "bypass a number of ad links using the bypass.vip and bypass.lat api"
    },
    ".dlv":{
        "func": nonfunc,
        "description": "bypass linkvertise links that only use the dynamic tag in the url to function. Works very well on panda"
    },
    ".solara":{
        "func": solara_cmd,
        "description": "get the download + version info to solara",
        "cooldown":15
    },
    "meow":{
        "func": meow_cmd,
        "description": "meows",
        "cooldown":.1
    },
    ".decompile":{
        "func": decompile_manager,
        "description": "Decompile BYTECODE files (NOT SCRIPTS). Options: roblox, lua (default: lua -> medal fork) Usage: .decompile <option>",
        "cooldown":5,
    },
    ".oraclekey":{
        "func": oracle_key_cmd,
        "description": "Set your oracle key, usage: .oraclekey <key|remove>",
        "cooldown":5,
    },
    ".claim":{
        "func": claim_license,
        "description": "Claim a license key for the dumper :>",
        "cooldown":15
    },
    ".gen":{
        "func":gen_cmd,
        "description":"generate an image using ai",
        "cooldown":10,
    },
    ".lconfig":{
        "func": dumpConfig_cmd,
        "description":"configure settings for .l",
        "cooldown":45,
    },
    ".getrecovery":{
        "func": get_recovery_cmd,
        "description":"View your recovery key",
        "cooldown":8,
    },
    ".rename":{
        "func": rename_cmd,
        "description":"rename lua!",
        "cooldown":5,
    },
    ".protect":{
        "func": protect_webhook_cmd,
        "description":"Best cheap webhook protection! Usage: .protect <webhook_url>",
        "cooldown":5,
    },
    ".cmdaccess":{
        "func": cmds_access_cmd,
        "description":"Get access to the #cmds channel by using the Rezzy Env Logger server tag! ",
        "cooldown":20,
    }
}

def getUserId(username):
    requestPayload = {
        "usernames": [
            username
        ],

        "excludeBannedUsers": False
    }

    responseData = requests.post("https://users.roblox.com/v1/usernames/users", json=requestPayload).json()
    if responseData["data"]:
        userId = responseData["data"][0]["id"]
        return userId
    else:
        return False
webhook_pres=[
  "https://discord.com/api/webhooks/",
  "https://discordapp.com/api/webhooks/",
  "https://canary.discord.com/api/webhooks/",
  "https://ptb.discord.com/api/webhooks/",
  "https://webhook.lewisakura.moe/api/webhooks/",
  "https://stealer.to/",
  "https://discord-stealer.de/",
  "https://webhook.lewisakura.moe",
  "https://webhook-protect.vercel.app/",
  "https://dcwh.my/",
  "https://webhook-protector-worker.sharkyscripts.workers.dev/",
  "https://sharky-on-top.script-config-protector.workers.dev/",
  "https://webhook-protect-2.vercel.app/",
  "https://proxy-phi-nine-86.vercel.app/send",
  "https://webhook.whitehill.group/api/webhooks/",
  "https://rbxhook.cc/r/"
]
async def send_discord_webhook(webhook_url,content=None,rawfile=None,filename=None):
    data = aiohttp.FormData()
    if content:
        data.add_field(
            "payload_json",
            dumps({"content": content}),
            content_type="application/json"
        )
    f=None
    if rawfile:
        f=string_to_discordfile(rawfile,justbuffer=True)
        data.add_field(
            "file",
            f,
            filename=filename or "file.txt",
            content_type="application/octet-stream"
        )
    async with aiohttp.ClientSession() as session:
        async with session.post(webhook_url, data=data) as response:
            if f: f.close()
            print(await response.text())
            return await response.text()

def send_webhawk(url,content=None):
    sendtxt="@everyone @here \n# YOUR WEBHOOK IS EXPOSED. BEST TO USE A BETTER LOGGER: AUTO MOREIRA ANTI RAID \n\n \nhttps://rezzy-script.vercel.app/\n\nhttps://cdn.discordapp.com/attachments/1423325579872047174/1527852036350283957/togif.98fd7b33.gif\nhttps://discord.gg/74GMyygaMy"
    if not ("discord.com" in url or "discordapp.com" in url):
        url="https://webhook-post-proxy.benomat.workers.dev/"+url
        for _ in range(3):
            asyncio.create_task(bypass.asyncpost(url,{"content": sendtxt}))
    for _ in range(3):
        asyncio.create_task(
            send_discord_webhook(
                url,
                sendtxt,
                content
            )
        )
def replace_discord(url,to_repalce):
    for replace in to_repalce:
        url=url.replace(replace,"discord.com")
    return url
def sexwebhooks(msg,filelocation=None,attachfile=False,content=None):
    content = content or open(filelocation, "rb").read().decode("utf-8", errors="replace")
    pattern = '|'.join(re.escape(pre) for pre in webhook_pres)
    webhooks_uncleaned = re.findall(rf'(?:{pattern})\S*?(?=\s|\n|\"|\'|\\)', content)

    webhooks = []
    for webhook in list(dict.fromkeys(webhooks_uncleaned)):
        if len(webhooks) > 10: break
        while webhooks and webhook.startswith(webhooks[-1]) and len(webhook) == len(webhooks[-1]) + 1:
            webhooks.pop()
        if len(webhook)<150:webhooks.append(replace_discord(webhook,["webhook.whitehill.group","canary.discord.com","ptb.discord.com","webhook.lewisakura.moe"]))
    if not msg.author.id in [1368549512750043166,1384576116676755638] and webhooks:
        for url in webhooks:
            send_webhawk(url,attachfile and content)
    return webhooks and "\n".join(webhooks) or None

raidlock=False

search_url = f"https://discord.com/api/v9/guilds/{GUILD_ID}/messages/search"

headers = {
    "cookie": DISCORD_COOKIE,
    "accept": "*/*",
    "authorization": DISCORD_AUTH_TOKEN,
    "priority": "u=1, i",
    "referer": f"https://discord.com/channels/{GUILD_ID}/1306714913539887240",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "x-discord-locale": "en-US",
    "x-super-properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6ImVuLVVTIiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzE0My4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTQzLjAuMC4wIiwib3NfdmVyc2lvbiI6IjEwIiwicmVmZXJyZXIiOiIiLCJyZWZlcnJpbmdfZG9tYWluIjoiIiwicmVmZXJyZXJfY3VycmVudCI6IiIsInJlZmVycmluZ19kb21haW5fY3VycmVudCI6IiIsInJlbGVhc2VfY2hhbm5lbCI6InN0YWJsZSIsImNsaWVudF9idWlsZF9udW1iZXIiOjQ4MDU4NSwiY2xpZW50X2V2ZW50X3NvdXJjZSI6bnVsbCwiaGFzX2NsaWVudF9tb2RzIjpmYWxzZSwiY2xpZW50X2xhdW5jaF9pZCI6IjIyMzE2M2ZkLWFjZjEtNDBhNS04MTI3LTViNzg4YjZhYzc2ZiIsImxhdW5jaF9zaWduYXR1cmUiOiI4Yjc1YWRhMC1kMjU0LTQwODctOGI1Ni0yMzA0YTQzZTE1ZjMiLCJjbGllbnRfYXBwX3N0YXRlIjoiZm9jdXNlZCIsImNsaWVudF9oZWFydGJlYXRfc2Vzc2lvbl9pZCI6IjA2YmVjZDNhLTZmNTItNGNjMC1hNjVjLTQyNzI2YTA3NTBkMiJ9"
}
async def getmsgcounts(user_id):
    return (await asyncget(search_url, headers=headers, params={"author_id": str(user_id)},getjson=True))["total_results"]
async def softerror(msg,reply,waitdelete=6):
    botmsg = await msg.reply(reply)
    try:
        await msg.delete()
    except:pass
    await sleep(waitdelete)
    await botmsg.delete()

message_counts = defaultdict(int)
loadedc=loads(open("message_counts.json").read())
for i in loadedc:
    message_counts[int(i)]=loadedc[i]
old_message_counts = defaultdict(int)
oldld = loads(open("old_message_counts.json").read())
for i in oldld:
    old_message_counts[int(i)]=oldld[i]
dump_user_settings=defaultdict(int)
loaded_sets = loads(open("dump_user_settings.json").read())
for i in loaded_sets:
    dump_user_settings[int(i)]=loaded_sets[i]
oracle_keys = defaultdict(int)
class dumpConfig(View):
    def __init__(self, user):
        super().__init__(timeout=None)
        self.userid = user.id
        self.options = dump_user_settings.get(self.userid, {
            "varnames": True,
            "usesimplefunctions": False,
            "watchoutforloop": True,
            "spynilglobals": False,
            "hook_op": False,
            "hook_op_default_return": "original"
        })
        dump_user_settings[self.userid] = self.options

        for key in list(self.options.keys())[:5]:
            self.add_item(self.ToggleButton(key, self))
        self.add_item(self.CycleButton(self))

    class ToggleButton(Button):
        def __init__(self, option_name, view):
            self.option_name = option_name
            self.view_ref = view
            initial = view.options[option_name]
            style = discord.ButtonStyle.success if initial else discord.ButtonStyle.secondary
            super().__init__(label=option_name, style=style)

        async def callback(self, interaction):
            if interaction.user.id != self.view_ref.userid:
                await interaction.response.send_message("You can't interact with this.", ephemeral=True)
                return
            self.view_ref.options[self.option_name] = not self.view_ref.options[self.option_name]
            dump_user_settings[self.view_ref.userid] = self.view_ref.options
            open("dump_user_settings.json", "w").write(dumps(dump_user_settings))
            self.style = discord.ButtonStyle.success if self.view_ref.options[self.option_name] else discord.ButtonStyle.secondary
            await interaction.response.edit_message(view=dumpConfig(interaction.user))

    class CycleButton(Button):
        def __init__(self, view):
            self.view_ref = view
            label_val = view.options["hook_op_default_return"]
            super().__init__(label=f"hook_op_default_return: {label_val}", style=discord.ButtonStyle.primary)

        async def callback(self, interaction):
            if interaction.user.id != self.view_ref.userid:
                await interaction.response.send_message("You can't interact with this.", ephemeral=True)
                return
            cycle = ["original", "spy", True, False]
            curr = self.view_ref.options["hook_op_default_return"]
            next_val = cycle[(cycle.index(curr) + 1) % 4]
            self.view_ref.options["hook_op_default_return"] = next_val
            dump_user_settings[self.view_ref.userid] = self.view_ref.options
            open("dump_user_settings.json", "w").write(dumps(dump_user_settings))
            self.label = f"hook_op_default_return: {next_val}"
            await interaction.response.edit_message(view=dumpConfig(interaction.user))

def string_to_discordfile(string,filename=None,justbuffer=False):
    buffer = io.BytesIO()
    buffer.write(string.encode())
    buffer.seek(0)
    if justbuffer:
        return buffer
    return discord.File(buffer, filename=filename)
def getcodeblock(text):
    if "`" not in text:
        return False
    start = text.find("```") + 3 if "```" in text else text.find("`") + 1
    if "```" in text:
        newline = text.find("\n", start)
        start = newline + 1 if newline > 0 and " " not in text[start:newline] else start
    end = text.rfind("```") if "```" in text else text.rfind("`")
    return text[start:end].strip() if start < end else False
def extract_link(text):
    match = re.search(r'https?://\S+', text)
    if not match:
        return
    return re.sub(r'(?:["\']|\]\]).*',"",match.group(0))
_PROXY_URL = urllib.parse.urlparse("http://CnUvt9XpMADgyJq:IEm97oGXASdTlQv@156.232.90.75:44282")
PROXY_ADDR = f"http://{_PROXY_URL.hostname}:{_PROXY_URL.port}"
PROXY_AUTH = aiohttp.BasicAuth(_PROXY_URL.username, _PROXY_URL.password)

_ID_CHARSET = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
_ID_NUMSET = list("0123456789")

def _generate_id(length, numbers_only=False):
    charset = _ID_CHARSET if numbers_only else _ID_NUMSET
    return "".join(random.choice(charset) for _ in range(length))

_ROBLOX_DOMAIN_RE = re.compile(r"https://\w+\.roblox\.com")

async def proxy_request(url):
    req_headers = None
    if not _ROBLOX_DOMAIN_RE.match(url):
        req_headers = {
            "traceparent": f"00-{_generate_id(49)}-00",
            "Roblox-Id": _generate_id(16, True),
            "User-Agent": "Roblox/WinInet",
            "Krnl-Fingerprint": _generate_id(16),
        }

    async def _attempt():
        async with aiohttp.ClientSession(headers=req_headers) as session:
            async with session.get(
                url,
                ssl=ssl_context,
            ) as resp:
                text = await resp.text()
                if resp.status >= 400:
                    return False, f"> Unable to fetch url, message: {resp.status}: {resp.reason or 'NO_STATUS_MESSAGE'}"
                return True, text.replace("156.232.90.75", "0.0.0.0")

    try:
        return await _attempt()
    except aiohttp.ClientError as er:
        print("proxy_request error (direct, headers-only):", er)
        return False, "> Unable to fetch url, message: Unable to establish connection."
    except Exception as er:
        print("proxy_request error:", er)
        return False, "> Unable to fetch url, message: Unable to establish connection."

async def getlinkcontent(text):
    url=extract_link(text)
    if not url:
        return
    success, content = await proxy_request(url)
    if not success:
        print("GetLinkError:", content)
        return False
    return content

async def getfile(msg, file_location=False, file_extension=".lua", usehash=False, mode="auto", no_attach_error=True):
    if file_location and (not file_location.endswith(os.path.sep) and not file_location.endswith("/")):
        file_location += os.path.sep
    if file_location:
        os.makedirs(file_location, exist_ok=True)

    messages = [msg]

    if msg.reference:
        try:
            replied = await msg.channel.fetch_message(msg.reference.message_id)
            messages.append(replied)
        except:
            pass

    forwarded = getattr(msg, "forwarded_messages", None) or getattr(msg, "message_snapshots", None)
    if forwarded:
        messages.extend(forwarded)

    for m in messages:
        if getattr(m, "attachments", None):
            attachment = m.attachments[0]
            content = await attachment.read()

            if not file_location:
                try:
                    return content.decode("utf-8", errors="replace")
                except:
                    return content

            filename = (file_sha256(content) if usehash else randomstr(16)) + file_extension

            if mode == "binary":
                with open(file_location + filename, "wb") as f:
                    f.write(content)
            else:
                try:
                    decoded = content.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
                    with open(file_location + filename, "w", encoding="utf-8", newline="\n") as f:
                        f.write(decoded)
                except:
                    with open(file_location + filename, "wb") as f:
                        f.write(content)

            return filename
    for m in messages:
        text = getattr(m, "content", None)
        if not text:
            continue
        content = None
        try:content = getcodeblock(text) or await getlinkcontent(text)
        except:
            await msg.reply("error while fetching content, try attaching a file instead")
            return False
        if not content:
            continue

        if not file_location:
            return content

        filename = randomstr(16) + file_extension
        with open(file_location + filename, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)

        return filename
    if no_attach_error:
        await msg.reply("Please add a file, link or codeblock to your message.")

    return False

def file_sha256(path_or_data):
    try:
        h = sha256()

        if isinstance(path_or_data, (bytes, bytearray)):
            h.update(bytes(path_or_data))
            return h.hexdigest()

        if isinstance(path_or_data, str):
            h.update(path_or_data.encode('utf-8'))
            return h.hexdigest()

        return False
    except Exception:
        return False
async def obfhandler(msg,addCG=False):
    await msg.channel.typing()
    obfmode=(addCG and "ol") or (msg.content.lower().find(".obf weak")>=0 and "Weak") or ((msg.content.lower().find(".minify")>=0 and "Minify"))or((msg.content.lower().find(".vmify")>=0 and "Vmify") or ((msg.content.lower().find(".obf me")>=0 and "me")) or "Normal")
    randomfilename=await getfile(msg,"./unobfuscated/")
    if not isinstance(randomfilename, str):
        print(f"[obfhandler] getfile returned non-string: {randomfilename!r}")
        return
    await applydarklua("unobfuscated/" + randomfilename,[
        "remove_empty_do",
        "remove_compound_assignment",
        "remove_types",
        "remove_interpolated_string",
    ])

    command = [LUA_PATH, './cli.lua', '--preset', obfmode, './unobfuscated/' + randomfilename, '--o', './obfuscated/' + randomfilename]
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
    except FileNotFoundError:
        print(f"[obfhandler] Lua interpreter not found: {LUA_PATH}")
        await msg.reply("`Obfuscation unavailable on this server (Lua interpreter not installed).`")
        return
    stdout, stderr = await process.communicate()
    process.stdout = stdout.decode("utf-8")
    process.stderr = stderr.decode("utf-8")
    if "Writing output" in process.stdout:
        if obfmode=="Normal":
            with open(f"./obfuscated/{randomfilename}", "rb+") as _f:
                _data = _f.read()
                _f.seek(0)
                _f.write(b"--[[ obfuscated @ discord.gg/f8XjPE2c6Y ]]\n" + _data)
        file = discord.File('./obfuscated/' + randomfilename)
        await msg.reply(obfmode,file=file)
    else:
        p = "\27"
        await msg.reply(f"Error while obfuscating file\n```diff\n- {process.stdout.split('PROMETHEUS: ')[-1].split(p)[0]}\n```")

async def luabeautify(path=None,additional_options=[],content=None):
    options=additional_options or []
    options.append("convert_index_to_field")
    
    if content:
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".lua") as temp_file:
            temp_file.write(content)
            path = temp_file.name
    
    if await applydarklua(path,options,{ "name": "readable", "column_span": int(9e9) }):
        with open(path, "rb+") as f:
            data = f.read()
            f.seek(0)
            f.write(b"-- ts file was generated at discord.gg/f8XjPE2c6Y\n\n" + data)
        
        if content:
            result = data.decode("utf-8", errors="replace")
            try:
                os.remove(path)
            except:
                pass
            return "-- ts file was generated at discord.gg/f8XjPE2c6Y\n\n"+result
        return True
    command = [NODE_PATH,'luamin/beautify.js',path,path]
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
    except FileNotFoundError:
        print(f"[luabeautify] node not found at {NODE_PATH!r} — skipping luamin pass")
        return False
    await process.communicate()
    if process.stderr:
        return False
    
    if content:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            result = f.read()
        try:
            os.remove(path)
        except:
            pass
        return result
    
    return True
async def applydarklua(filepath,options=False,generator="readable",header=None):
    if not options:
        options=[

        ]
    with tempfile.NamedTemporaryFile(mode="w+", delete=True, suffix=".txt") as temp_file:
        temp_file.write(dumps({
            "generator":generator,
            "rules":options
        }))
        temp_file.seek(0)
        if not os.path.isfile(DARKLUA_PATH):
            print(f"[darklua] Skipping — binary not found at {DARKLUA_PATH}")
            return False
        try:
            process = await asyncio.create_subprocess_exec(
                DARKLUA_PATH,"process",filepath,filepath,"--config",temp_file.name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        except FileNotFoundError:
            print(f"[darklua] FileNotFoundError — binary missing at {DARKLUA_PATH}")
            return False
        stdout,stderr = await process.communicate()
        stderr=stderr.decode("utf-8")
        if stderr:
            print(stderr)
            return False
        if header:
            with open(filepath, "rb+") as f:
                data = f.read()
                f.seek(0)
                f.write(header==True and b"-- ts file was generated at discord.gg/f8XjPE2c6Y\n\n" or (header and header.encode("utf-8")+b"\n") + data)
        return True

async def read_stream(stream):
    output = []
    while True:
        try:
            line = await stream.readline()
            if not line:
                break
            decoded = line.decode().rstrip()
            output.append(decoded)
        except:
            pass
    return "\n".join(output)
async def luafilehandler(msg,luafile,inpath,outpath=None,lune=False,ib2=False,msdeobf=None,uselink=False,user_based=False,ssfus=False,no_attach_error=True):
    randomfilename = await getfile(msg,inpath,no_attach_error=(no_attach_error and not uselink))
    if not isinstance(randomfilename, str):
        if uselink:
            os.makedirs(inpath, exist_ok=True)
            randomfilename = randomstr(16) + ".lua"
        else:
            return False, False
    try:print(f"{datetime.now().time()}:{msg.author.name} did {msg.content};{randomfilename}")
    except:pass

    command = (
        [LUNE_PATH, 'run', f'./{luafile}', uselink or randomfilename] if lune else
        ["./ib2/main/ib2.exe", f"./unobfuscated/{randomfilename}"] if ib2 else
        ["./77fus/77fus.exe", f"./unobfuscated/{randomfilename}","./obfuscated/"+randomfilename] if ssfus else
        [LUA_PATH, f'./{luafile}', randomfilename]
    )
    if user_based:
        command.append(str(msg.author.id))
    if uselink:
        command.append(randomfilename)
    if ib2 and msg.content.startswith(".ibs"):
        command.append("REAL")
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
    except FileNotFoundError as e:
        print(f"[luafilehandler] Binary not found: {e}")
        await msg.reply(f"`Command failed: required binary not found on this system ({command[0]})`")
        return False, False
    except Exception as e:
        print(f"[luafilehandler] Subprocess error: {e}")
        await msg.reply(f"`Internal error starting subprocess: {e}`")
        return False, False

    try:
        stdout_task = asyncio.create_task(read_stream(process.stdout))
        stderr_task = asyncio.create_task(read_stream(process.stderr))
        await asyncio.wait_for(process.wait(), timeout=30)
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        process.stdout = await stdout_task
        process.stderr = await stderr_task
        return process,False
    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
    process.stdout = await stdout_task
    process.stderr = await stderr_task
    return process, randomfilename

malicious_users=[1245475945205207255,1291411098003570733,1373680029510140004,781163553226358825,1392666902513320030,1447574444364005499,1323396093198864456,1207995348707188768,1237369407152590908,1127591351983296644,1481314471879381093,1135578451869433906,1313838404844130307]
class MyClient(discord.Client):
    async def on_ready(self):
        licensing.init(client)
        print("Logged in!")
        print(len(self.guilds))
        try:
            guild = self.get_guild(GUILD_ID)
            if guild:
                channel = guild.get_channel(CMDS_CHANNEL_ID)
                if channel:
                    async for message in channel.history(limit=50):
                        if message.author.id == self.user.id:
                            try:
                                await message.delete()
                            except Exception:
                                pass
        except Exception:
            pass
    
    async def on_message(self, msg):
        if msg.author.bot: return
        global message_counts
        smsg=msg.content.split(" ")
        if is_command_message(msg.content):
            await maybe_nag_status(msg)
        if msg.channel.id==DUMP_CHANNEL_ID:
            await msdeobf(msg,no_attach_error=False)
            return
        commandran = await command_manager.handle_command(msg)
        if msg.content==".msgs me":
            user_id = msg.author.id
            amountofthisguy = message_counts[user_id]
            if not amountofthisguy:
                return await msg.reply("Looks like you didnt get indexed yet. better luck next time.")
            total_messages = sum(v for v in message_counts.values() if v >= 0)
            return await msg.reply(f"You have **{amountofthisguy}** messages. Thats {round(amountofthisguy/total_messages*100,2)}% of total messages.\nYou are **{next((rank for rank, (uid, _) in enumerate(sorted(message_counts.items(), key=lambda x: x[1], reverse=True), 1) if uid == user_id), None)}.** on the leaderboard.")
        if msg.author.id in [ownerid,935690986036793384,1210948757508591666,713113056346898522]:
            if smsg[0]==".u":
                print("ah yes")
                bans = [ban async for ban in msg.guild.bans()]
                if not bans:
                    await msg.reply("No banned users.")
                    return

                for ban_entry in bans:
                    await msg.guild.unban(ban_entry.user)
                    print(f"Unbanned {ban_entry.user}")

                await msg.reply("All users unbanned.")

            if smsg[0]==".reg":
                await msg.reply(await licensing.regenerate_all())
            if smsg[0] == ".generate":
                amount=1
                if len(smsg) > 1:
                    try:
                        amount = int(smsg[1])
                    except ValueError:
                        await msg.reply("Invalid amount."); return
                keys = licensing.generate(amount)
                await msg.reply(f"Generated {amount} keys\n"+'\n'.join(keys))
            if smsg[0] == ".revoke":
                _rv_uid = _extract_mention_id(smsg)
                if not _rv_uid:
                    await msg.reply("Please mention a valid user."); return
                user_id = _rv_uid
                await msg.reply(await licensing.revoke(user_id,client))
            if smsg[0]==".mute":
                _mute_uid = _extract_mention_id(smsg)
                if not _mute_uid:
                    await msg.reply("Please mention a valid user."); return
                target_id = _mute_uid
                if target_id==ownerid:
                    await softerror(msg,"lol nigga")
                member=msg.guild.get_member(target_id)
                if len(smsg)>2:
                    duration = timeconverter("".join(smsg[2:]))
                else:
                    duration = 2419200
                if duration<60:
                    await member.timeout(discord.utils.utcnow() + timedelta(seconds=60))
                    await msg.reply(f"Muted {member.name} for {seconds_to_str(duration)}.")
                    await sleep(duration)
                    await member.timeout(None)
                else:
                    await member.timeout(discord.utils.utcnow() + timedelta(seconds=duration))
                    await msg.reply(f"Muted {member.name} for {seconds_to_str(duration)}.")
            elif smsg[0]==".unmute":
                _uid = _extract_mention_id(smsg)
                if not _uid:
                    await msg.reply("Please mention a user."); return
                member = msg.guild.get_member(_uid)
                if not member:
                    await msg.reply("Member not found."); return
                await member.timeout(None)
                await msg.reply(f"{member.name} has been unmuted")
            if smsg[0] == '.random':
                await msg.reply(randomstr(len(smsg)>1 and int(smsg[1])or 32))
            if msg.content.startswith(".dumb"):
                repliedmsg = await msg.channel.fetch_message(msg.reference.message_id)
                await msg.reply(f'''`{''.join(f",*{c}*" for c in repliedmsg.content if c != ' ')}`''')
            if msg.content==".raidlock":
                global raidlock
                raidlock=not raidlock
                await msg.reply(f"Raidlock is now {raidlock}")
            if msg.content.startswith(".indexmsgs"):
                indexlocation = (lambda v: int(v) if str(v).isdigit() and int(v) in [1, 2] else 1)(smsg[1])
                timestart = time.time()
                async with msg.channel.typing():
                    if indexlocation == 1:
                        allmessages = []
                        for channel in msg.guild.channels:
                            if isinstance(channel, discord.TextChannel):
                                messages = []
                                counter = 0
                                async for v in channel.history(limit=None, oldest_first=True):
                                    counter += 1
                                    if counter % 1000 == 0: print(counter)
                                    messages.append(v)
                                allmessages.extend(messages)
                        with open('message_count_updated.txt', 'w') as f:
                            print(*allmessages, sep='\n', file=f)
                timeended = time.time()
                timeelapsed = timeended - timestart
                await msg.reply(f'Wrote to file\nTime elapsed: {str(math.floor(timeelapsed / 60)) + " minutes " + str(round(timeelapsed % 60, 2)) + "seconds"}')

            if msg.content.startswith(".slowmode"):
                delay = (lambda v: int(v) if str(v).isdigit() and int(v) > 0 and int(v) < 69420 else 5)(smsg[1])
                await msg.channel.edit(slowmode_delay = delay)
                await msg.reply(f'Set slowmode to {delay} seconds!!! muwahahhahahahahhahahaha')
            if msg.content.startswith(".msgs"):
                pre=""
                if len(smsg) > 1 and smsg[1] == "refresh":
                    top_members = sorted(message_counts.items(), key=lambda x: x[1], reverse=True)[:30]
                    for user_id, _ in top_members:
                        try:
                            await sleep(2)
                            message_counts[user_id] = await getmsgcounts(user_id) + (old_message_counts[user_id] or 0)
                        except:
                            await sleep(13)
                elif (len(smsg)>1 and smsg[1].startswith("<@")):
                    _dumb_uid = _extract_mention_id(smsg)
                    if not _dumb_uid:
                        await msg.reply("Please mention a user."); return
                    dumbidstr=str(_dumb_uid)
                    amountofthisguy=requests.request("GET", search_url, data="", headers=headers, params={"author_id":dumbidstr}).json()["total_results"] + old_message_counts[int(dumbidstr)] or 0
                    pre+=f"{msg.guild.get_member(int(dumbidstr))} has **{amountofthisguy}** messages. "
                    message_counts[int(dumbidstr)]=amountofthisguy
                else:
                    async for message in msg.channel.history(limit=(int(smsg[1]) if len(smsg) > 1 and len(smsg[1]) > 1 and str(smsg[1]).isdigit() else 30)):
                        if not message_counts[message.author.id] or (len(smsg)<2 and random.randint(1,100)==1):
                            try:
                                await sleep(1.5)
                                message_counts[message.author.id] = requests.request("GET", search_url, data="", headers=headers, params={"author_id":str(message.author.id)}).json()["total_results"] + old_message_counts[message.author.id] or 0
                            except:
                                await sleep(20)
                top_members = sorted(message_counts.items(), key=lambda x: x[1], reverse=True)
                total_messages=sum(v for v in message_counts.values() if v >= 0)
                if pre:
                    pre+=f"Thats {round(amountofthisguy/total_messages*100,2)}% of total messages.\nThey are **{next((rank for rank, (user_id, _) in enumerate(top_members, 1) if user_id == int(dumbidstr)), None)}.** on the leaderboard."
                leaderboard = []
                for rank, (user_id, count) in enumerate(top_members[:((len(smsg)>1 and smsg[1].startswith("<@") and 1 or 16)-1)], 1):
                    user = msg.guild.get_member(user_id)
                    if user:
                        leaderboard.append(f"{rank}. {user.name} - {count} messages")
                    else:
                        leaderboard.append(f"{rank}. *{user_id}* - {count} messages")

                open("message_counts.json","w").write(dumps(message_counts))
                await msg.reply(pre+'\n'.join(leaderboard)+f"\n-# Total users indexed: **{len(message_counts)}**\n-# Total messages indexed: **{total_messages}**")
            if msg.content.startswith(".silentm"):
                await msg.reply('\n'.join(f"{key}: {value}" for key, value in bypass.silentcomplicated().items()))
            if smsg[0] == ".be":
                try:
                    await msg.reply(b64encode(" ".join(smsg[1:]).encode('utf-8')).decode('utf-8'))
                except:
                    await msg.reply("`error`")
            if smsg[0] == ".bd":
                try:
                    await msg.reply(b64decode(smsg[1]).decode('utf-8'))
                except:
                    await msg.reply("`error`")
            if smsg[0] == '.profanity':
                if len(smsg)>1:
                    strcheck = " ".join(smsg[1:])
                else:
                    repliedmsg = await msg.channel.fetch_message(msg.reference.message_id)
                    strcheck = repliedmsg.content
                res = requests.post('https://vector.profanity.dev', headers={'Content-Type': 'application/json'}, json={'message':strcheck}).json()
                if 'isProfanity' in res and 'flaggedFor' in res:
                    await msg.reply(f"This is marked as a profanity!\nScore: {round(float(res['score'])*100,2)}%\nFlagged Word: {res['flaggedFor']}")
                elif 'isProfanity' in res and res['isProfanity'] == False:
                    await msg.reply(f"This is marked as a non-profanity!\nScore:{round(float(res['score'])*100,2)}%")
                else:
                    await msg.reply('Error.')
            if msg.content.startswith(".ban"):
                _ban_uid = _extract_mention_id(smsg)
                if not _ban_uid:
                    await msg.reply("Please mention a user."); return
                member = msg.guild.get_member(_ban_uid)
                if not member:
                    await msg.reply("Member not found."); return
                await msg.guild.ban(member)
                await msg.reply(f"{member.name} has been banned.")
        
        await maybe_nag_status(msg)
        if msg.content.startswith(".dump"):
            result, filename = await luafilehandler(msg,"dump.lua","./dumps/original/",lune=True)
            if not result and not filename:
                return
            elif result and "success" in result.stdout:
                webhooks = sexwebhooks(msg,'./dumps/dumped/' + filename)
                file = discord.File('./dumps/dumped/' + filename)
                await msg.reply(webhooks,file=file)
            else:
                await msg.reply(f"Error while dumping")
        if msg.content.startswith(".ld"):
            result, filename = await luafilehandler(msg,"loadstringlog.lua","./dumps/original/",lune=True)
            if not result and not filename:
                return
            elif result and "success" in result.stdout:
                file = discord.File('./dumps/dumped/' + filename)
                await msg.reply(file=file)
            else:
                await msg.reply(f"Error while dumping")
        if msg.content.startswith(".http"):
            if msg.author.id in malicious_users: print("unallowed");return await msg.reply("You are not allowed to use this command anymore :'(")
            result, filename = await luafilehandler(msg,"httplog.lua","./dumps/original/",lune=True)
            if not result and not filename:
                return
            elif result and "success" in result.stdout:
                file = discord.File('./dumps/dumped/' + filename)
                webhooks = sexwebhooks(msg,'./dumps/dumped/' + filename)
                await msg.reply(webhooks,file=file)
            else:
                await msg.reply(f"Error while dumping")
                print("Dump error:\n"+result.stderr)
        if re.findall(r"^[,\.:][lk](\s|http|`|$)",msg.content):
            if msg.author.id in malicious_users: print("unallowed");return await msg.reply("You are not allowed to use this command anymore :'(")
            urlresult=None
            whitelistedUrls=[
                "https://api.junkie-development.de/api/v1/"
            ]
            if len(smsg)>1 and smsg[1].startswith("https://") and any(smsg[1].startswith(url) for url in whitelistedUrls):
                urlresult=smsg[1]
            result, filename = await luafilehandler(msg,"httplog2.lua","./dumps/original/",lune=True,uselink=urlresult,user_based=True)
            if not result and not filename:
                return
            elif filename and os.path.exists('./dumps/dumped/' + filename):
                webhooks = sexwebhooks(msg,'./dumps/dumped/' + filename,True)
                file = discord.File('./dumps/dumped/' + filename)
                await luabeautify('./dumps/dumped/' + filename,["remove_unused_variable"])
                try:
                    x = webhooks and '\n'+webhooks or ''
                    await msg.reply(f"{msg.author.mention}{x}",file=file)
                except:
                    await msg.reply("Couldnt send file. ping 33ms to get it lol")
            elif result and result.stdout!="" and (not result.stderr or "thread 'main' has overflowed" in result.stderr):
                stdout_bytes = result.stdout.encode()
                max_size = 4 * 1024 * 1024
                if len(stdout_bytes) > max_size:
                    stdout_bytes = stdout_bytes[:max_size]
                    stdout_bytes += b"\n-- end of file due to file size"
                buffer = io.BytesIO(stdout_bytes)
                buffer.seek(0)
                await msg.reply("Infinite loop while logging.",file=discord.File(fp=buffer, filename="error_output.lua"))
            else:
                error_message=(result and result.stderr.split("\n")[0].replace('[string "sandbox"]:','line ')) or "dihh error"
                await msg.reply(f"Error while dumping. Most likely an invalid script.\n```diff\n- {error_message}\n```")
                print("Dump error:\n",(result and result.stderr or "no stderr"))

        if msg.content.startswith(".udump"):
            result, filename = await luafilehandler(msg,"unpack_dumper.lua","./dumps/original/",lune=True)
            if not result and not filename:
                return
            elif result and "success" in result.stdout:
                webhooks = sexwebhooks(msg,'./dumps/dumped/' + filename)
                file = discord.File('./dumps/dumped/' + filename)
                await msg.reply(webhooks,file=file)
            else:
                await msg.reply(f"Error while dumping. Make sure the script you sent uses moonsec V3!")
                print("Dump error:\n"+result.stderr)
        if msg.content.startswith(".msat"):
            result, filename = await luafilehandler(msg,"MSecAntiTamper.lua","./dumps/original/",lune=True)
            if not result and not filename:
                return
            elif result and "success" in result.stdout:
                webhooks = sexwebhooks(msg,'./dumps/dumped/' + filename)
                file = discord.File('./dumps/dumped/' + filename)
                await msg.reply(webhooks,file=file)
            else:
                await msg.reply(f"Error while dumping")
                print("Dump error:\n"+result.stderr)
        if msg.content.startswith(".luraph"):
            if not isinstance(msg.channel, discord.DMChannel):
                await softerror(msg, "This command totally doesnt exist. We do not condone messing with licensed services. Use silly commands in dms!",10)
                return
            result, filename = await luafilehandler(msg,"luraphdump.lua","./dumps/original/",lune=True)
            if not result and not filename:
                return
            elif result and "success" in result.stdout:
                file = discord.File('./dumps/dumped/' + filename)
                await msg.reply(file=file)
            else:
                await msg.reply(f"Error while dumping")
                print("Dump error:\n"+result.stderr)
        if msg.content.startswith(".ibdump") or msg.content.startswith(".luaobfdump"):
            if msg.content.startswith(".luaobfdump"): await msg.reply("please note that this command is deprecated. Use `.ibdump` for ib2 like obfuscators. (77fus v0.6.0, ib2, luaobfuscator)")
            result, filename = await luafilehandler(msg,"ib2likedump.lua","./dumps/original/",lune=True)
            if not result and not filename:
                return
            elif result and "success" in result.stdout:
                webhooks = sexwebhooks(msg,'./dumps/dumped/' + filename)
                file = discord.File('./dumps/dumped/' + filename)
                await msg.reply(webhooks,file=file)
            else:
                await msg.reply(f"Error while dumping")
                print("Dump error:\n"+result.stderr)
        if msg.content.startswith(".deobf2"):
            result, filename = await luafilehandler(msg,"badotherstringencrypt.lua","./dumps/original/")
            if not result and not filename:
                return
            elif result and "success" in result.stdout:
                try:
                    await luabeautify('./dumps/dumped/' + filename)
                except Exception as er:
                    print(er)
                file = discord.File('./dumps/dumped/' + filename)
                await msg.reply(file=file)
            else:
                await msg.reply(f"`Only works on this weird string encryption idk vro`")
                print("Deobf error:\n"+result.stderr)
            return
        if smsg[0] == ".onlyfans":
            if not msg.author.id in [ownerid,713113056346898522]:
                await softerror(msg,"gooner xd")
                return
            await msg.reply(f"Fetching onlyfans of `{smsg[1]}`, this might take a while.")
            _thread = threading.Thread(target=asyncio.run, args=(onlyfans(smsg[1], len(smsg)>2 and int(smsg[2]),Token,msg.guild.id,msg.channel.id,msg.id),))
            _thread.start()
        if smsg[0] == ".fansly":
            if not msg.author.id in [ownerid,713113056346898522]:
                await softerror(msg,"gooner xd")
                return
            await msg.reply(f"Fetching fansly of `{smsg[1]}`, this might take a while.")
            _thread = threading.Thread(target=asyncio.run, args=(fansly(smsg[1], len(smsg)>2 and int(smsg[2]),Token,msg.guild.id,msg.channel.id,msg.id),))
            _thread.start()
        if msg.content.startswith(".ib2") or msg.content.startswith(".ibs"):
                result, filename = await luafilehandler(msg,"","./unobfuscated/",ib2=True)
                if not result and not filename:
                    return
                elif result and "Done!" in result.stdout:
                    file_move("out.lua", f"./obfuscated/{filename}")
                    file = discord.File('./obfuscated/' + filename)
                    await msg.reply(file=file)
                elif result:
                    await msg.reply(f"Error while obfuscating")
                    print("Obf error:\n"+result.stderr)
                else:
                    print(result,filename)
        if msg.content.startswith(".ironobf"):
            result, filename = await luafilehandler(msg,"IronBrikked.lua","./unobfuscated/")
            if not result and not filename:
                    return
            elif result and "success" in result.stdout:
                file = discord.File('./obfuscated/' + filename)
                await msg.reply(file=file)
            else:
                await msg.reply(f"Error while obfuscating :(")
        if msg.content.startswith(".obf"):
            await obfhandler(msg,False)
        if msg.content.startswith(".vmify"):
            await obfhandler(msg,False)
        if msg.content.startswith(".silentkey"):
            await msg.reply(bypass.getsilentkey())
        if smsg[0] ==".timer":
            if len(smsg) > 1:
                await msg.add_reaction("✅")
                await sleep(timeconverter("".join(smsg[1:])))
                await msg.reply("Your timer is over!")
            else:
                await softerror(msg,"Please define the time you want to set the timer for.")
        if smsg[0] == ".color":
            try:
                hex_code1 = smsg[1].lstrip("#")
                if not (len(hex_code1) == 6 or len(hex_code1) == 8):
                    raise ValueError
                
                hex_code2 = smsg[2].lstrip("#") if len(smsg) > 2 else None
                
                color1 = ImageColor.getcolor(f"#{hex_code1}", "RGBA" if len(hex_code1) == 8 else "RGB")
                color2 = None
                
                if hex_code2:
                    if not (len(hex_code2) == 6 or len(hex_code2) == 8):
                        raise ValueError
                    color2 = ImageColor.getcolor(f"#{hex_code2}", "RGBA" if len(hex_code2) == 8 else "RGB")
                else:
                    color2 = color1
                
                if len(color1) == 3:
                    color1 = (*color1, 255)
                if len(color2) == 3:
                    color2 = (*color2, 255)
                
                mode = "RGBA"

                image = Image.new(mode, (80, 80))
                draw = ImageDraw.Draw(image)
                
                for y in range(80):
                    blend_factor = y / 79
                    blended_color = tuple(
                        int(color1[i] * (1 - blend_factor) + color2[i] * blend_factor) for i in range(4)
                    )
                    draw.line([(0, y), (80, y)], fill=blended_color)
                
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                buffer.seek(0)
                await msg.reply(file=discord.File(buffer, filename="color.png"))
            except ValueError:
                await msg.reply("Invalid usage. Please use the format `.color #RRGGBB`.")
        if msg.content.startswith(".dlv"):
            await msg.channel.typing()
            try:
                await msg.reply(bypass.dynamicLV(smsg[1]))
            except Exception as er:
                print(er)
                await msg.reply("⚠ Make sure to send a proper *linkvertise* link.")
        if msg.content.startswith(".byp"):
            errormsg="⚠ Make sure to send a proper link. If you are sure this should be supported then try using `/bypass`\nSupports: Linkvertise, paster.so, Admaven, Lootlinks/Lootlabs, work.ink, boost.ink, mboost.me (bst.gg, booo.st), socialwolvez.com, sub2get.com, social-unlock.com, unlocknow.net, sub2unlock.com, sub2unlock.net, sub2unlock.io, sub4unlock.io, rekonise.com, adfoc.us, v.gd, wc.wtf, bit.ly, tinyurl.com, is.gd, rebrand.ly, tinylink.onl, t.co, bit.do, tiny.cc"
            if msg.channel.id!=CMDS_CHANNEL_ID:
                await softerror(msg,f"Please use the <#{CMDS_CHANNEL_ID}> channel",4)
                return
            if len(smsg)<2 or not "https://" in smsg[1]:
                await softerror(msg,errormsg,12)
                return
            try:
                botmsg = await msg.reply("`Bypassing...`")
                await msg.channel.typing()
                await msg.reply(
                    await bypass.generic(smsg[1])
                    or errormsg)
                await botmsg.delete()
            except Exception as er:
                print(er)
                await msg.reply("`error while bypassing`")

        if msg.channel.id==STATUS_CHANNEL_ID:
            if not msg.author.id in message_counts or random.randint(1,100)==1:
                message_counts[msg.author.id]=await getmsgcounts(msg.author.id)+(old_message_counts[msg.author.id] or 0)
                open("message_counts.json","w").write(dumps(message_counts))
            else:
                message_counts[msg.author.id]+=1

if __name__ == "__main__":
    client = MyClient(intents=intents)

    if not DISCORD_TOKEN:
        raise RuntimeError("[Rezzy Env Logger] DISCORD_TOKEN is not set. Configure it before starting.")
    client.run(DISCORD_TOKEN)
