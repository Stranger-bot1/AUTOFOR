import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot credentials
api_id = 24344133
api_hash = "edbe7000baef13fa5a6c45c8edc4be66"
bot_token = "7462968272:AAG0wqZYfc4jbxKOIzewSF27qn98twGbaN8"

# Admin chat ID (send logs here)
ADMIN_CHAT_ID = 123456789  # Replace with your Telegram user ID

# In-memory storage
user_channels = {}

app = Client("auto_forwarder_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)


@app.on_message(filters.private & filters.command("start"))
async def start_command(client, message: Message):
    await message.reply("👋 Welcome! Send me the source and target channel IDs (like: source_id target_id) to start forwarding.\nSend /stop to pause forwarding anytime.")


@app.on_message(filters.private & filters.command("stop"))
async def stop_command(client, message: Message):
    user_id = message.from_user.id
    if user_id in user_channels:
        user_channels[user_id]["active"] = False
        await message.reply("🚫 Forwarding stopped for you.")
        await app.send_message(ADMIN_CHAT_ID, f"User {user_id} stopped forwarding.")
    else:
        await message.reply("⚠️ No active forwarding found.")


@app.on_message(filters.private & filters.text & ~filters.command(["start", "stop"]))
async def get_channel_ids(client, message: Message):
    try:
        user_id = message.from_user.id
        ids = message.text.strip().split()

        if len(ids) != 2:
            await message.reply("⚙️ Please send exactly two channel IDs separated by space: `source_id target_id`")
            return

        source_channel = int(ids[0])
        target_channel = int(ids[1])

        if user_id not in user_channels:
            user_channels[user_id] = {"channels": [], "active": True}

        user_channels[user_id]["channels"].append({"source": source_channel, "target": target_channel})
        user_channels[user_id]["active"] = True

        await message.reply(f"✅ Channel pair saved!\nSource: `{source_channel}`\nTarget: `{target_channel}`")
        await app.send_message(ADMIN_CHAT_ID, f"User {user_id} started forwarding from {source_channel} to {target_channel}.")

    except Exception as e:
        logger.error(f"Error while saving target channel: {e}")
        await message.reply("❌ Error while processing your input.")


@app.on_message(filters.channel)
async def forward_messages(client, message: Message):
    for user_id, user_data in user_channels.items():
        if user_data.get("active"):
            for channel_pair in user_data.get("channels", []):
                if message.chat.id == channel_pair["source"]:
                    try:
                        await asyncio.sleep(2)  # 2-second delay
                        await message.copy(chat_id=channel_pair["target"])

                        log_msg = f"✅ Forwarded message ID {message.id} from {channel_pair['source']} to {channel_pair['target']} (User {user_id})"
                        logger.info(log_msg)
                        await app.send_message(ADMIN_CHAT_ID, log_msg)

                    except Exception as e:
                        error_msg = f"❌ Error forwarding message ID {message.id}: {e}"
                        logger.error(error_msg)
                        await app.send_message(ADMIN_CHAT_ID, error_msg)


if __name__ == "__main__":
    logger.info("Bot is starting...")
    app.run()
