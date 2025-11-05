# petani.py
import os
import re
import time
import asyncio
import logging
from telethon import TelegramClient, events
from dotenv import load_dotenv

# ---------------- CONFIG ----------------
load_dotenv("kunci.env")
API_ID = int(os.getenv("API_ID_1") or 0)
API_HASH = os.getenv("API_HASH_1") or ""
PHONE = os.getenv("PHONE_1") or ""
BOT_USERNAME = os.getenv("BOT_USERNAME") or ""
OWNER_ID = int(os.getenv("OWNER_ID_1") or 0)

if not API_ID or not API_HASH or not PHONE:
    raise SystemExit("ERROR: Pastikan API_ID, API_HASH, PHONE ter-set di kunci.env")

# ---------------- TELETHON ----------------
client = TelegramClient("Choco", API_ID, API_HASH)

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")
logger = logging.getLogger("petani")

# ---------------- VARIABEL ----------------
running_maling = False
running_kebun = False

last_sent = {}  # {kode: timestamp}
DELAY_BETWEEN_CODES = 120   # 2 menit
DELAY_REPEAT_CODE = 3600    # 1 jam

# EXP tracking
exp_current = 0
exp_max = None
exp_re = re.compile(r"EXP:\s*([\d,]+)\/([\d,]+)")
exp_gain_re = re.compile(r"EXP\+([\d,]+)")

# ---------------- QUEUE SYSTEM ----------------
message_queue = asyncio.Queue()

async def safe_send(msg: str):
    """Kirim pesan via queue"""
    await message_queue.put(msg)

async def message_worker():
    """Worker untuk kirim pesan satu per satu"""
    while True:
        msg = await message_queue.get()
        try:
            await client.send_message(BOT_USERNAME, msg)
            print(f"[SEND] {msg}")
        except Exception as e:
            print(f"[!] Gagal kirim {msg}: {e}")
        await asyncio.sleep(2)  # jeda aman antar pesan

# ---------------- HELPER ----------------
def parse_int(s: str) -> int:
    return int(s.replace(",", "").strip())

# ---------------- LOOP KEBUN ----------------
async def loop_kebun():
    global running_kebun
    while True:
        if running_kebun:
            # tanam wortel
            await safe_send("/tanam_Wortel_15")
            print("[KEBUN] Tanam wortel")
            await asyncio.sleep(2)

            # siram
            await safe_send("/siram")
            print("[KEBUN] Siram tanaman")
            await asyncio.sleep(2)

            # tunggu sampai panen
            wait_time = 185
            print(f"[KEBUN] Menunggu {wait_time} detik sampai panen...")
            await asyncio.sleep(wait_time)

            # panen
            await safe_send("/ambilPanen")
            print("[KEBUN] Panen wortel")

        else:
            await asyncio.sleep(3)

# ---------------- HANDLER PESAN BOT GAME ----------------
@client.on(events.NewMessage(from_users=BOT_USERNAME))
async def game_handler(event):
    global exp_current, exp_max

    text = event.raw_text or ""

    # Cek progress EXP
    m = exp_re.search(text)
    if m:
        exp_current = parse_int(m.group(1))
        exp_max = parse_int(m.group(2))
        print(f"[STATUS] EXP {exp_current}/{exp_max}")
        return

    # Cek EXP gain (+xxx)
    g = exp_gain_re.findall(text)
    if g:
        for val in g:
            gain = parse_int(val)
            exp_current += gain
            if exp_max:
                exp_current = min(exp_current, exp_max)
            print(f"[EXP] +{gain} → {exp_current}/{exp_max}")

            if exp_max and exp_current >= exp_max:
                print("[LEVELUP] EXP penuh, kirim /levelup")
                await safe_send("/levelup")
                await asyncio.sleep(3)
                await safe_send("/status")

# ---------------- HANDLER OWNER ----------------
@client.on(events.NewMessage(from_users=OWNER_ID))
async def owner_handler(event):
    global running_maling, running_kebun
    msg = (event.raw_text or "").strip().lower()

    if msg == "start kebun":
        running_kebun = True
        await event.reply("▶️ Kebun STARTED")
    elif msg == "stop kebun":
        running_kebun = False
        await event.reply("⏹ Kebun STOPPED")


# ---------------- MAIN ----------------
async def main():
    print(">> Bot siap jalan.")
    print("             'start kebun'  / 'stop kebun'")
    print("             'start all'    / 'stop all'")
    print("             'status'")

    # jalankan worker & loop
    asyncio.create_task(message_worker())
    asyncio.create_task(loop_kebun())

    # kirim /status awal
    await safe_send("/status")

    await client.run_until_disconnected()

with client:

    client.loop.run_until_complete(main())

