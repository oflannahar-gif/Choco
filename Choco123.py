# Petani.py

import os
import asyncio
import random
import logging
import datetime

from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ---------------- CONFIG ----------------
load_dotenv("kunci.env")
API_ID = int(os.getenv("API_ID_1") or 0)
API_HASH = os.getenv("API_HASH_1") or ""
PHONE = os.getenv("PHONE_1") or ""
BOT_USERNAME = (os.getenv("BOT_USERNAME") or "KampungMaifamBot").lstrip('@')
BOT_X = (os.getenv("BOT_X") or "KampungMaifamXBot").lstrip('@')
GROUP_DANAU = "@danaudalamhutan"
OWNER_ID = int(os.getenv("OWNER_ID") or 0)
GLOBAL_GROUP = "@KampungMaifamGlobal"

if not API_ID or not API_HASH or not PHONE:
    raise SystemExit("ERROR: Pastikan API_ID, API_HASH, PHONE ter-set di kunci.env")

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger("auto_game_bot")

# ---------------- CLIENT ----------------
SESSION_STRING = os.getenv("TELEGRAM_SESSION")
if SESSION_STRING:
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
else:
    client = TelegramClient("Choco", API_ID, API_HASH)

# ---------------- QUEUE ----------------
message_queue = asyncio.Queue()

PRIVATE_LOG_CHAT = -4650846540  # ID grup privat kamu

# === SAFE SEND Bot Alpha ===
async def safe_send(msg, to=None):
    if to == "me":
        to = PRIVATE_LOG_CHAT
    await message_queue.put((msg, to or BOT_USERNAME))

# === SAFE SEND Bot X ===
async def safe_send_x(msg, to=None):
    if to == "me":
        to = PRIVATE_LOG_CHAT
    await message_queue.put((msg, to or BOT_X))

# === SAFE SEND Grup Danau ===
async def safe_send_d(msg, to=None):
    if to == "me":
        to = PRIVATE_LOG_CHAT
    await message_queue.put((msg, to or GROUP_DANAU))


# === SAFE SEND CEPAT (langsung kirim tanpa antre) ===
async def safe_send_cepat(msg, to=None):
    if to == "me":
        to = PRIVATE_LOG_CHAT
    dest = to or BOT_USERNAME
    try:
        await client.send_message(dest, msg)
        print(f"[RESTORE] → {dest}: {msg}")
    except Exception as e:
        print(f"[!] Gagal kirim cepat {msg} ke {dest}: {e}")


async def message_worker():
    while True:
        msg, dest = await message_queue.get()
        try:
            await client.send_message(dest, msg)
            print(f"[SEND] → {dest}: {msg}")
        except Exception as e:
            print(f"[!] Gagal kirim {msg} ke {dest}: {e}")
        await asyncio.sleep(2)

async def human_sleep(min_s=1.0, max_s=1.5):
    await asyncio.sleep(random.uniform(min_s, max_s))

# ---------------- STATE ----------------
state = {
    "masak": {"aktif": False, "kode": None, "loops": 0, "count": 0, "pause": False, "menunggu_input": False},
    "masak_x": {"aktif": False, "kode": None, "loops": 0, "count": 0, "pause": False, "menunggu_input": False},
    "mancing": {"aktif": False, "lokasi": None, "pause": False, "last_click": 0},
    "mancing_x": {"aktif": False, "lokasi": None, "pause": False, "last_click": 0},
    "macul": {"aktif": False, "tanaman": None, "jumlah": 0, "durasi": 180, "target": BOT_USERNAME, "pause": False},
    "macul_guild": {"aktif": False, "tanaman": None, "jumlah": 0, "durasi": 180, "pause": False},
    "macul_global": {"aktif": False, "tanaman": None, "jumlah": 0, "durasi": 180, "pause": False},
    "skygarden": {"aktif": False, "interval": 420, "pause": False},
    "fishing": {"aktif": False, "interval": 270, "pause": False},
    "maling": {"aktif": False, "interval": 4, "pause": False},
    "ternak": {"aktif": False, "interval": 910, "pause": False},
    "ternakkhusus": {"aktif": False, "pause": False},
    "animalhouse": {"aktif": False, "interval": 610, "pause": False},
    "greenhouse": {"aktif": False, "tanaman": None, "jumlah": 0, "durasi": 180, "pause": False},
    "energi_habis": False
}


tanaman_data = {}

# ---------------- LOAD DATA TANAMAN ----------------
def load_tanaman():
    tanaman_data.clear()
    if not os.path.exists("tanaman.txt"):
        print("⚠️ File tanaman.txt tidak ditemukan.")
        return
    with open("tanaman.txt", "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                nama, waktu = line.split("=", 1)
                nama_k = nama.strip().lower()
                try:
                    tanaman_data[nama_k] = int(waktu.strip())
                except ValueError:
                    print(f"⚠️ Baris tanaman tidak valid dilewati: {line}")
    print(f"🌿 {len(tanaman_data)} tanaman dimuat: {', '.join(tanaman_data.keys())}")

# ---------------- LOAD DATA MALING ----------------
def load_maling():
    if not os.path.exists("maling.txt"):
        print("⚠️ File maling.txt tidak ditemukan.")
        return []
    lokasi_maling = []
    with open("maling.txt", "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if line and not line.startswith("#"):
                lokasi_maling.append(line)
    print(f"🦹‍♂️ {len(lokasi_maling)} lokasi maling dimuat.")
    return lokasi_maling




# =============== LOOPS ================

# === LOOP MALING ===
async def loop_maling():
    data = state["maling"]
    lokasi_list = load_maling()
    if not lokasi_list:
        print("⚠️ Tidak ada lokasi maling, loop maling dibatalkan.")
        return
    print(">> Loop Maling dimulai")
    await client.send_message(PRIVATE_LOG_CHAT, "🦹‍♂️ Auto Maling dimulai")
    while data["aktif"]:
        while data.get("pause", False):
            await asyncio.sleep(5)
        if "index" not in data:
            data["index"] = 0

        lokasi = lokasi_list[data["index"]]
        data["index"] = (data["index"] + 1) % len(lokasi_list)

        await safe_send_x(f"{lokasi}")
        print(f"[SEND] maling {lokasi}")
        await asyncio.sleep(data["interval"])
        for _ in range(10):  
            if not data["aktif"]:
                break
            await asyncio.sleep(0.5)
    print(">> Loop Maling berhenti")
    await client.send_message(PRIVATE_LOG_CHAT, "🦹‍♂️ Auto Maling dimatikan")

# === LOOP TERNAK KHUSUS ===
async def loop_ternakkhusus():
    data = state["ternakkhusus"]
    print(">> Loop Ternak Khusus dimulai")
    await client.send_message(PRIVATE_LOG_CHAT, "🐮 Auto Ternak Khusus dimulai")

    while data["aktif"]:
        while data.get("pause", False):
            await asyncio.sleep(5)
        await asyncio.sleep(2)
        await safe_send("/pelihara_AnakArwana_85")
        await asyncio.sleep(2)
        await safe_send("/beriMakanx")
        await asyncio.sleep(2)
        await safe_send("/ambilHewan")
        await asyncio.sleep(2)
        for _ in range(10):  
            if not data["aktif"]:
                break
            await asyncio.sleep(0.5)
    
    print(">> Loop Ternak Khusus berhenti")
    await client.send_message(PRIVATE_LOG_CHAT, "🐮 Auto Ternak Khusus dimatikan")

# === LOOP GRUP DANAU ===
async def loop_grup_danau():
    data = state["fishing"]
    print(">> Loop Grup Danau dimulai")
    await client.send_message(PRIVATE_LOG_CHAT, "🎣 Auto Mancing Grup Danau dimulai")
    while data["aktif"]:
        while data.get("pause", False):
            await asyncio.sleep(5)
        await safe_send_d("/fish")
        await asyncio.sleep(data["interval"])
        for _ in range(10):  
            if not data["aktif"]:
                break
            await asyncio.sleep(0.5)
    print(">> Loop Grup Danau berhenti")
    await client.send_message(PRIVATE_LOG_CHAT, "🎣 Auto Mancing Grup Danau berhenti.")

# === LOOP ANIMAL HOUSE ===
async def loop_animalhouse():
    data = state["animalhouse"]
    print(">> Loop Animal House dimulai")
    await client.send_message(PRIVATE_LOG_CHAT, "🏠 Auto Animal House dimulai")
    while data["aktif"]:
        while data.get("pause", False):
            await asyncio.sleep(5)
        await asyncio.sleep(2)
        await safe_send("/ah_1_AmbilHasil")
        await asyncio.sleep(data["interval"])
        for _ in range(10):  
            if not data["aktif"]:
                break
            await asyncio.sleep(0.5)
    print(">> Loop Animal House berhenti")
    await client.send_message(PRIVATE_LOG_CHAT, "🏠 Auto Animal House dimatikan")

# === LOOP SKY GARDEN ===
async def loop_skygarden():
    data = state["skygarden"]
    print(">> Loop Sky Garden dimulai")
    await client.send_message(PRIVATE_LOG_CHAT, "🌿 Auto Sky Garden dimulai")
    while data["aktif"]:
        while data.get("pause", False):
            await asyncio.sleep(5)
        await safe_send("/sg_panen")
        await asyncio.sleep(data["interval"])
        for _ in range(10):  
            if not data["aktif"]:
                break
            await asyncio.sleep(0.5)
    print(">> Loop Sky Garden berhenti")
    await client.send_message(PRIVATE_LOG_CHAT, "🌿 Auto Sky Garden dimatikan")

# === LOOP TERNAK ===
async def loop_ternak():
    data = state["ternak"]
    print(">> Loop ternak dimulai")
    await client.send_message(PRIVATE_LOG_CHAT, "🐓 Auto Ternak dimulai")
    while data["aktif"]:
        while data.get("pause", False):
            await asyncio.sleep(5)
        await safe_send("/ambilHasil")
        await asyncio.sleep(2)
        await safe_send("/beriMakan")
        await asyncio.sleep(data["interval"])
        for _ in range(10):  
            if not data["aktif"]:
                break
            await asyncio.sleep(0.5)
    print(">> Loop Ternak berhenti")
    await client.send_message(PRIVATE_LOG_CHAT, "🐓 Auto Ternak dimatikan")

# === LOOP MASAK ===
async def loop_masak():
    data = state["masak"]
    print(">> Loop Masak Alpha dimulai")
    while data["aktif"] and data["kode"] and (data["count"] < data["loops"] or data["loops"] == 0):
        while data.get("pause", False):
            await asyncio.sleep(5)
        await safe_send(data["kode"], BOT_USERNAME)
        data["count"] += 1
        print(f"🍳 Masak ke-{data['count']}")
        for _ in range(10):  
            if not data["aktif"]:
                break
            await asyncio.sleep(0.5)
    data["aktif"] = False
    await client.send_message(PRIVATE_LOG_CHAT, f"✅ Masak selesai ({data['count']}x)")
    print(">> Loop Masak berhenti")

# === LOOP MASAK X ===
async def loop_masak_x():
    data = state["masak_x"]
    print(">> Loop Masak X dimulai")
    while data["aktif"] and data["kode"] and (data["count"] < data["loops"] or data["loops"] == 0):
        while data.get("pause", False):
            await asyncio.sleep(5)
        await safe_send_x(data["kode"], BOT_X)
        data["count"] += 1
        print(f"🍳 Masak ke-{data['count']}")
        for _ in range(10):  
            if not data["aktif"]:
                break
            await asyncio.sleep(0.5)
    data["aktif"] = False
    await client.send_message(PRIVATE_LOG_CHAT, f"✅ Masak selesai ({data['count']}x)")
    print(">> Loop Masak berhenti")

# === LOOP MANCING ===
async def loop_mancing():
    data = state["mancing"]
    lokasi = data.get("lokasi")
    alat = data.get("alat", " Tarik Pancing")

    print(f">> Loop Mancing dimulai di {lokasi} pakai {alat.capitalize()} (Bot: {BOT_USERNAME})")

    # Kirim lokasi pertama kali
    await safe_send(lokasi, BOT_USERNAME)
    await asyncio.sleep(3)

    while data["aktif"]:
        # Kalau sedang di-pause, tunggu dulu
        while data.get("pause", False):
            await asyncio.sleep(5)
        
        now = asyncio.get_event_loop().time()

        # ⚠️ kalau tidak ada aktivitas selama 15 detik → kirim ulang lokasi
        if now - data.get("last_click", 0) > 15:
            print(f"⚠️ Tidak ada respons, kirim ulang lokasi: {lokasi}")
            await safe_send(lokasi, BOT_USERNAME)
            data["last_click"] = now

        for _ in range(10):  
            if not data["aktif"]:
                break
            await asyncio.sleep(0.5)

    print(">> Loop Mancing berhenti")
    await client.send_message(PRIVATE_LOG_CHAT, "🎣 Auto Mancing berhenti.")

# === LOOP MANCING X===
async def loop_mancing_x():
    data = state["mancing_x"]
    lokasi = data.get("lokasi")
    alat = data.get("alat", "pancing").lower()


    print(f">> Loop Mancing dimulai di {lokasi} pakai {alat.capitalize()} (Bot: {BOT_X})")

    # Kirim lokasi pertama kali
    await safe_send_x(lokasi, BOT_X)
    await asyncio.sleep(3)


    while data["aktif"]:
        # Kalau sedang di-pause, tunggu dulu
        while data.get("pause", False):
            await asyncio.sleep(5)
        
        now = asyncio.get_event_loop().time()

        # ⚠️ kalau tidak ada aktivitas selama 15 detik → kirim ulang lokasi
        if now - data.get("last_click", 0) > 15:
            print(f"⚠️ Tidak ada respons, kirim ulang lokasi: {lokasi}")
            await safe_send_x(lokasi, BOT_X)
            data["last_click"] = now

        for _ in range(10):  
            if not data["aktif"]:
                break
            await asyncio.sleep(0.5)


    print(">> Loop Mancing berhenti")
    await client.send_message(PRIVATE_LOG_CHAT, "🎣 Auto Mancing berhenti.")


# === LOOP MACUL (PRIBADI / GUILD / GLOBAL) ===
async def loop_macul(name="macul"):
    data = state[name]
    durasi = data.get("durasi", 180)
    target = data.get("target", BOT_USERNAME)
    print(f">> Mulai {name}: {data['tanaman']} ({data['jumlah']} pohon, {durasi}s)")
    await safe_send(f"🌱 Mulai {name}: {data['tanaman']} ({data['jumlah']} pohon, {durasi}s)", PRIVATE_LOG_CHAT)
    while data["aktif"]:
        while data.get("pause", False):
            await asyncio.sleep(5)
        if name == "macul_global":
            await safe_send_cepat(f"/tanam_{data['tanaman']}_{data['jumlah']}", GLOBAL_GROUP)
            await asyncio.sleep(durasi)
            await safe_send_cepat("/panen", GLOBAL_GROUP)
            await asyncio.sleep(305)
        elif name in ("macul", "macul_guild"):
            cmd_tanam = f"/tanam_{data['tanaman']}_{data['jumlah']}" if name=="macul" else f"/tanamGuild_{data['tanaman']}_{data['jumlah']}"
            cmd_siram = "/siram" if name=="macul" else "/KebunGuild_Siram"
            cmd_panen = "/ambilPanen" if name=="macul" else "/kebunGuild_AmbilPanen"
            await safe_send(cmd_tanam, target)
            await asyncio.sleep(2)
            await safe_send(cmd_siram, target)
            await asyncio.sleep(durasi)
            await safe_send(cmd_panen, target)
        for _ in range(10):  
            if not data["aktif"]:
                break
            await asyncio.sleep(0.5)
    print(f">> Loop {name} berhenti")


# === LOOP GREENHOUSE ===
async def loop_greenhouse():
    data = state["greenhouse"]
    durasi = data.get("durasi", 180)
    print(f">> Mulai Greenhouse: {data['tanaman']} ({data['jumlah']} pohon, {durasi}s)")
    
    while data["aktif"]:
        while data.get("pause", False):
            await asyncio.sleep(5)
        await safe_send(f"/gh_1_tanam_{data['tanaman']}_{data['jumlah']}", BOT_USERNAME)
        await asyncio.sleep(durasi)
        await safe_send("/gh_1_panen", BOT_USERNAME)
        for _ in range(10):  
            if not data["aktif"]:
                break
            await asyncio.sleep(0.5)
    print(">> Loop Greenhouse berhenti")






# ---------------- STOP ALL ----------------
def stop_all():
    for v in state.values():
        if isinstance(v, dict) and "aktif" in v:
            v["aktif"] = False


# ================= OWNER CMD / HANDLER ================
@client.on(events.NewMessage(from_users=OWNER_ID))
async def cmd_owner(event):
    msg = (event.raw_text or "").strip()
    lmsg = msg.lower()
    print(f">> INPUT OWNER: {msg}")

        # === SEMUA ON ===
    if lmsg in ("semua on", "/semua on"):
        # === SKY GARDEN ===
        if not state["skygarden"]["aktif"]:
            state["skygarden"]["aktif"] = True
            asyncio.create_task(loop_skygarden())
            

        # === TERNAK ===
        if not state["ternak"]["aktif"]:
            state["ternak"]["aktif"] = True
            asyncio.create_task(loop_ternak())
            

        # === TERNAK KHUSUS ===
        if not state["ternakkhusus"]["aktif"]:
            state["ternakkhusus"]["aktif"] = True
            asyncio.create_task(loop_ternakkhusus())
            

        # === FISHING GRUP DANAU ===
        if not state["fishing"]["aktif"]:
            state["fishing"]["aktif"] = True
            asyncio.create_task(loop_grup_danau())

        # === ANIMAL HOUSE ===
        if not state["animalhouse"]["aktif"]:
            state["animalhouse"]["aktif"] = True
            asyncio.create_task(loop_animalhouse())

            await event.reply("✅ Semua loop diaktifkan.")
            

        return


    # === SEMUA OFF ===
    if lmsg in ("semua off", "/semua off"):
        stop_msgs = []
        # === FISHING GRUP DANAU ===
        if state["fishing"]["aktif"]:
            state["fishing"]["aktif"] = False
            stop_msgs.append("🎣 Auto Mancing Grup Danau dimatikan.")

        # === SKY GARDEN ===
        if state["skygarden"]["aktif"]:
            state["skygarden"]["aktif"] = False
            stop_msgs.append("🌿 Auto Sky Garden dimatikan.")

        # === TERNAK ===
        if state["ternak"]["aktif"]:
            state["ternak"]["aktif"] = False
            stop_msgs.append("🐓 Auto Makan Ternak dimatikan.")

        # === TERNAK KHUSUS ===
        if state["ternakkhusus"]["aktif"]:
            state["ternakkhusus"]["aktif"] = False
            stop_msgs.append("🐮 Auto Ternak Khusus dimatikan.")

        # === ANIMAL HOUSE ===
        if state["animalhouse"]["aktif"]:
            state["animalhouse"]["aktif"] = False
            stop_msgs.append("🏠 Auto Animal House dimatikan.")

        if stop_msgs:
            await event.reply("\n".join(stop_msgs))
        else:
            await event.reply("❗ Tidak ada loop yang aktif untuk dimatikan.")

        return


    # === TERNAK KHUSUS ===
    if lmsg in ("tk on", "/tk on","semua on", "/semua on"):
        if not state["ternakkhusus"]["aktif"]:
            state["ternakkhusus"]["aktif"] = True
            await event.reply("🐮 Auto Ternak Khusus diaktifkan.")
            asyncio.create_task(loop_ternakkhusus())
        else:
            await event.reply("❗ Auto Ternak Khusus sudah aktif.")
        return

    if lmsg in ("tk off", "/tk off", "semua off", "/semua off"):
        if state["ternakkhusus"]["aktif"]:
            state["ternakkhusus"]["aktif"] = False
            await event.reply("⏹ Auto Ternak Khusus dimatikan.")
        else:
            await event.reply("❗ Auto Ternak Khusus belum aktif.")
        return

    # === TERNAK ===
    if lmsg in ("tr on", "/tr on", "semua on","/semua on"):
        if not state["ternak"]["aktif"]:
            state["ternak"]["aktif"] = True
            await event.reply("🐓 Auto Makan Ternak diaktifkan.")
            asyncio.create_task(loop_ternak())
        else:
            await event.reply("❗ Auto Makan Ternak sudah aktif.")
        return

    if lmsg in ("tr off", "/tr off", "semua off","/semua off"):
        if state["ternak"]["aktif"]:
            state["ternak"]["aktif"] = False
            await event.reply("⏹ Auto Makan Ternak dimatikan.")
        else:
            await event.reply("❗ Auto Makan Ternak belum aktif.")
        return

    # === Maling ===
    if lmsg in ("maling on", "/maling on", "semua on","/semua on"):
        if not state["maling"]["aktif"]:
            state["maling"]["aktif"] = True
            await event.reply("🦹‍♂️ Auto Maling diaktifkan.")
            asyncio.create_task(loop_maling())
        else:
            await event.reply("❗ Auto Maling sudah aktif.")
        return
    
    if lmsg in ("maling off", "/maling off", "semua off","/semua off"):
        if state["maling"]["aktif"]:
            state["maling"]["aktif"] = False
            await event.reply("⏹ Auto Maling dimatikan.")
        else:
            await event.reply("❗ Auto Maling belum aktif.")
        return

    # === FISHING GRUP DANAU ===
    if lmsg in ("fd on", "/fd on", "semua on","/semua on"):
        if not state["fishing"]["aktif"]:
            state["fishing"]["aktif"] = True
            await event.reply("🎣 Auto Mancing Grup Danau diaktifkan.")
            asyncio.create_task(loop_grup_danau())
        else:
            await event.reply("❗ Auto Mancing Grup Danau sudah aktif.")
        return
    
    if lmsg in ("fd off", "/fd off", "semua off","/semua off"):
        if state["fishing"]["aktif"]:
            state["fishing"]["aktif"] = False
            await event.reply("⏹ Auto Mancing Grup Danau dimatikan.")
        else:
            await event.reply("❗ Auto Mancing Grup Danau belum aktif.")
        return

    # === ANIMAL HOUSE ===
    if lmsg in ("ah on", "/ah on", "semua on","/semua on"):
        if not state["animalhouse"]["aktif"]:
            state["animalhouse"]["aktif"] = True
            await event.reply("🏠 Auto Animal House diaktifkan.")
            asyncio.create_task(loop_animalhouse())
        else:
            await event.reply("❗ Auto Animal House sudah aktif.")
        return
    
    if lmsg in ("ah off", "/ah off", "semua off","/semua off"):
        if state["animalhouse"]["aktif"]:
            state["animalhouse"]["aktif"] = False
            await event.reply("⏹ Auto Animal House dimatikan.")
        else:
            await event.reply("❗ Auto Animal House belum aktif.")
        return

    # === SKY GARDEN ===
    if lmsg in ("sg on", "/sg on", "semua on","/semua on"):
        if not state["skygarden"]["aktif"]:
            state["skygarden"]["aktif"] = True
            await event.reply("🌿 Auto Sky Garden diaktifkan.")
            asyncio.create_task(loop_skygarden())
        else:
            await event.reply("❗ Auto Sky Garden sudah aktif.")
        return

    if lmsg in ("sg off", "/sg off", "semua off","/semua off"):
        if state["skygarden"]["aktif"]:
            state["skygarden"]["aktif"] = False
            await event.reply("⏹ Auto Sky Garden dimatikan.")
        else:
            await event.reply("❗ Auto Sky Garden belum aktif.")
        return

    # === MASAK ===
    if lmsg == "masak":
        state["masak"].update({
            "aktif": False,
            "kode": None,
            "loops": 0,
            "count": 0,
            "menunggu_input": "kode"
        })
        await event.reply("🍳 Mau masak apa?")
        return

    # Jika sedang menunggu kode masakan
    if state["masak"].get("menunggu_input") == "kode":
        state["masak"]["kode"] = msg
        state["masak"]["menunggu_input"] = "jumlah"
        await event.reply("🔁 Mau masak berapa kali?")
        return

    # Jika sedang menunggu jumlah loop
    if state["masak"].get("menunggu_input") == "jumlah" and lmsg.isdigit():
        loops = int(lmsg)
        state["masak"].update({
            "aktif": True,
            "loops": loops,
            "count": 0,
            "menunggu_input": False
        })
        await event.reply(f"Mulai auto-masak {loops}x 🍳")
        asyncio.create_task(loop_masak())
        return

    # === MASAK X ===
    if lmsg == "masak x":
        state["masak_x"].update({
            "aktif": False,
            "kode": None,
            "loops": 0,
            "count": 0,
            "menunggu_input": "kode"
        })
        await event.reply("🍳 Mau masak apa?")
        return

    # Jika sedang menunggu kode masakan
    if state["masak_x"].get("menunggu_input") == "kode":
        state["masak_x"]["kode"] = msg
        state["masak_x"]["menunggu_input"] = "jumlah"
        await event.reply("🔁 Mau masak berapa kali?")
        return

    # Jika sedang menunggu jumlah loop
    if state["masak_x"].get("menunggu_input") == "jumlah" and lmsg.isdigit():
        loops = int(lmsg)
        state["masak_x"].update({
            "aktif": True,
            "loops": loops,
            "count": 0,
            "menunggu_input": False
        })
        await event.reply(f"Mulai auto-masak {loops}x 🍳")
        asyncio.create_task(loop_masak_x())
        return


    # === MANCING ===
    if lmsg == "mancing":
        state["mancing"].update({
            "aktif": False,
            "lokasi": None,
            "alat": None,
            "menunggu_lokasi": True,
            "menunggu_alat": False
        })

        await event.reply("🎣 Mancing dimana?")
        return
    
    # Tahap 1 → Pilih lokasi
    if state["mancing"].get("menunggu_lokasi", False) and not state["mancing"]["aktif"]:
        lokasi = msg.strip()
        state["mancing"]["lokasi"] = lokasi
        state["mancing"]["menunggu_lokasi"] = False
        state["mancing"]["menunggu_alat"] = True
        await event.reply(f"📍 Lokasi: {lokasi}\nPakai alat apa? (Ketik **Pancing** atau **Jala**)")
        return

    # Tahap 2 → Pilih alat
    if state["mancing"].get("menunggu_alat", False) and not state["mancing"]["aktif"]:
        alat = msg.strip().lower()
        if alat not in ("pancing", "jala"):
            await event.reply("⚠️ Pilihan tidak valid! Ketik **Pancing** atau **Jala**.")
            return
        
        state["mancing"]["alat"] = alat
        state["mancing"]["aktif"] = True
        state["mancing"]["menunggu_alat"] = False

        lokasi = state["mancing"]["lokasi"]
        await event.reply(f"🎣 Mulai auto-mancing di {lokasi} pakai {alat.capitalize()}...")
        asyncio.create_task(loop_mancing())
        return


    # === MANCING X ===
    if lmsg == "mancing x":
        state["mancing_x"].update({
            "aktif": False,
            "lokasi": None,
            "alat": None,
            "menunggu_lokasi": True,
            "menunggu_alat": False
        })

        await event.reply("🎣 Mancing dimana?")
        return
    
    # Tahap 1 → Pilih lokasi
    if state["mancing_x"].get("menunggu_lokasi", False) and not state["mancing_x"]["aktif"]:
        lokasi = msg.strip()
        state["mancing_x"]["lokasi"] = lokasi
        state["mancing_x"]["menunggu_lokasi"] = False
        state["mancing_x"]["menunggu_alat"] = True
        await event.reply(f"📍 Lokasi: {lokasi}\nPakai alat apa? (Ketik **Pancing** atau **Jala**)")
        return

    # Tahap 2 → Pilih alat
    if state["mancing_x"].get("menunggu_alat", False) and not state["mancing_x"]["aktif"]:
        alat = msg.strip().lower()
        if alat not in ("pancing", "jala"):
            await event.reply("⚠️ Pilihan tidak valid! Ketik **Pancing** atau **Jala**.")
            return
        state["mancing_x"]["alat"] = alat
        state["mancing_x"]["aktif"] = True
        state["mancing_x"]["menunggu_alat"] = False

        lokasi = state["mancing_x"]["lokasi"]
        await event.reply(f"🎣 Mulai auto-mancing di {lokasi} pakai {alat.capitalize()}...")
        asyncio.create_task(loop_mancing_x())
        return


    # === MACUL (PRIBADI / GUILD / GLOBAL) ===
    if lmsg in ("macul","macul_guild","macul_global"):
        load_tanaman()
        state[lmsg].update({"aktif": False, "tanaman": None, "jumlah": 0, "durasi": 180, "target": BOT_USERNAME})
        if lmsg=="macul_global":
            await event.reply(f"🌱 Mau tanam apa di Global? (macul_global <nama> <jumlah>)")
        else:
            await event.reply(f"🌱 Mau tanam apa di {lmsg.replace('_',' ')}? (macul/ macul_guild <nama> <jumlah>)")
        return

    # One-line format: macul <nama> <jumlah>
    for key in ["macul","macul_guild","macul_global"]:
        if lmsg.startswith(key+" ") or lmsg.startswith("/"+key+" "):
            parts = msg.replace("/","").split()
            if len(parts)>=3 and parts[1].strip() and parts[2].isdigit():
                tanaman = parts[1].strip().lower()
                jumlah = int(parts[2])
                durasi = tanaman_data.get(tanaman,180)
                state[key].update({"aktif": True,"tanaman":tanaman,"jumlah":jumlah,"durasi":durasi})
                if key!="macul_global":
                    target = BOT_USERNAME if key=="macul" else BOT_USERNAME
                    state[key]["target"] = target
                await event.reply(f"Mulai auto {key.replace('_',' ')} {parts[1]} ({jumlah} pohon, {durasi}s)")
                asyncio.create_task(loop_macul(key))
                return
            else:
                await event.reply(f"Format: {key} <nama> <jumlah>")
                return

    # === GREENHOUSE ===
    if lmsg == "gh":
        load_tanaman()
        state["greenhouse"].update({"aktif": False, "tanaman": None, "jumlah": 0, "durasi": 180, "menunggu_input": True})
        await event.reply("🌱 Mau tanam apa di Greenhouse? (gh <nama> <jumlah>)")
        return
    
    # One-line format: gh <nama> <jumlah>
    if lmsg.startswith("gh ") or lmsg.startswith("/gh "):
        parts = msg.replace("/","").split()
        if len(parts)>=3 and parts[1].strip() and parts[2].isdigit():
            tanaman = parts[1].strip().lower()
            jumlah = int(parts[2])
            durasi = tanaman_data.get(tanaman, 180)
            state["greenhouse"].update({
                "aktif": True,
                "tanaman": tanaman,
                "jumlah": jumlah,
                "durasi": durasi,
                "menunggu_input": False
            })
            await event.reply(f"🌱 Mulai Greenhouse {tanaman} ({jumlah} pohon, {durasi}s)")
            asyncio.create_task(loop_greenhouse())
            return
        else:
            await event.reply("Format: gh <nama> <jumlah>")
            return



    # === STOP ALL ===
    if lmsg.startswith("stop"):
        parts = lmsg.split()
        if len(parts) == 1 or parts[0] in ("stop_all", "/stop_all"):
            stop_all()
            await event.reply("⏹ Semua loop dihentikan.")
            return

        # contoh: stop mancing_x atau stop mancing x
        mode = parts[1] if len(parts) > 1 else None
        if len(parts) > 2:
            mode += f"_{parts[2]}"

        if mode and mode in state and state[mode]["aktif"]:
            state[mode]["aktif"] = False
            await event.reply(f"⏹ Loop {mode} dihentikan.")
        else:
            await event.reply("❗ Tidak ada loop aktif / format salah.")
        return

        
    print(f"❗ Perintah tidak dikenali: {msg}")



# ---------------- BOT HANDLER ----------------

# === EVENT HANDLER MANCING ===
@client.on(events.NewMessage(incoming=True, chats=BOT_USERNAME))
async def handle_mancing_final(event):
    msg = (event.raw_text or "").lower()
    data = state.get("mancing", {})
    if not data.get("aktif") or not data.get("lokasi"):
        return

    lokasi = data["lokasi"]
    alat = data.get("alat", "pancing").lower()

    # ✅ Klik tombol "Tarik" langsung kalau ada
    if event.buttons:
        for row in event.buttons:
            for button in row:
                teks = (button.text or "").lower()
                if alat == "pancing" and ("tarik alat pancing" in teks or "pull the rod" in teks):
                    await human_sleep()
                    await button.click()
                    data["last_click"] = asyncio.get_event_loop().time()
                    print("🎣 Klik 'Tarik Alat Pancing'")
                    return
                elif alat == "jala" and ("tarik jala" in teks or "pull the net" in teks):
                    await human_sleep()
                    await button.click()
                    data["last_click"] = asyncio.get_event_loop().time()
                    print("🎣 Klik 'Tarik Jala'")
                    return
                                

    # 🪝 Indikator memancing (hasil tangkap, skill, dsb)
    if any(x in msg for x in [
        "memancing", "fishing skill", "kamu mendapatkan", "berhasil menangkap",
        "energi berhasil dipulihkan", "restored", "kamu tidak sedang memancing"
    ]):
        await human_sleep(1, 2)
        await safe_send(lokasi, BOT_USERNAME)
        print(f"↻ Lanjut mancing di {lokasi}")

# === EVENT HANDLER RESTORE ===
@client.on(events.NewMessage(incoming=True, chats=BOT_USERNAME))
async def handle_restore(event):
    msg = (event.raw_text or "").lower()

    # Jika energi habis
    if "/tidur" in msg or "/sleep" in msg:
        print("⚠️ Energi habis, mencoba restore...")
        state["energi_habis"] = True
        for v in state.values():
            if isinstance(v, dict) and "pause" in v:
                v["pause"] = True
        for i in range(100):
            await asyncio.sleep(3)
            if not state.get("energi_habis", True):
                print("🛑 Energi sudah pulih, hentikan percobaan restore.")
                break
            await safe_send_cepat("restore", BOT_USERNAME)
            print(f"[RESTORE TRY] {i+1}/100")
            await asyncio.sleep(5)
        return

    # Jika sudah berhasil dipulihkan
    if "berhasil dipulihkan" in msg or "energi berhasil dipulihkan" in msg:
        print("✅ Energi berhasil dipulihkan (global)")
        state["energi_habis"] = False
        for v in state.values():
            if isinstance(v, dict) and "pause" in v:
                v["pause"] = False


# === BOT 2 HANDLER (untuk Mancing X) ===
@client.on(events.NewMessage(from_users=BOT_X))
async def bot_reply_x(event):
    text = (event.raw_text or "").lower()
    print(f"[BOT_X] {text[:120]}...")

    # ENERGI PULIH → RESUME SEMUA LOOP
    if "energi berhasil dipulihkan" in text:
        print("✅ Energi pulih, semua loop dilanjutkan.")
        state["energi_habis"] = False
        for v in state.values():
            if isinstance(v, dict) and "pause" in v:
                v["pause"] = False
        return

    # MANCING X
    s = state["mancing_x"]
    if s["aktif"] and event.buttons:
        alat = s.get("alat", "pancing")
        for row in event.buttons:
            for button in row:
                if alat == "pancing" and "Tarik Alat Pancing" in (button.text or ""):
                    await human_sleep()
                    await button.click()
                    print("🎣 Klik 'Tarik Alat Pancing'")
                    s["last_click"] = asyncio.get_event_loop().time()
                    return
                elif alat == "jala" and "Tarik Jala" in (button.text or ""):
                    await human_sleep()
                    await button.click()
                    print("🎣 Klik 'Tarik Jala'")
                    s["last_click"] = asyncio.get_event_loop().time()
                    return
        
        if "kamu mendapatkan" or "Kamu berhasil menangkap" in text:
            await human_sleep(1,2)
            await safe_send_x(s["lokasi"], BOT_X)
            print(f">> Kirim ulang lokasi: {s['lokasi']}, → Maifam X ")

# ---------------- MAIN ----------------
async def main():
    await client.start(phone=PHONE)
    logger.info("Client started")
    load_tanaman()
    asyncio.create_task(message_worker())
    msg_intro = ("Bot siap ✅\n\nCommand:\n"
                 "- masak → (Bot Alpha)\n"
                 "- masak x → (Bot X)\n"
                 "- mancing → (Bot Alpha)\n"
                 "- mancing x → (Bot X)\n"
                 "- macul <tanaman> <jumlah>\n"
                 "- macul_guild <tanaman> <jumlah>\n"
                 "- macul_global <tanaman> <jumlah>\n"
                 "- sg on / sg off (sky garden)\n"
                 "- tk on / tk off (ternak khusus)\n"
                 "- tr on / tr off (ternak biasa)\n"
                 "- fd on / fd off (fishing danau)\n"
                 "- maling on / maling off (auto maling)\n"
                 "- ah on / ah off (animal house)\n"
                 "- gh <tanaman> <jumlah> (greenhouse)\n"
                 "- semua on / semua off\n"
                 "- stop atau stop_[mode]")
    await safe_send(msg_intro, "me")
    await client.run_until_disconnected()

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
