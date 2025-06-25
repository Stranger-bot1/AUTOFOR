import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
import os

# ------------------- Configuration -------------------
API_ID = 24344133
API_HASH = 'edbe7000baef13fa5a6c45c8edc4be66'
BOT_TOKEN = '7462968272:AAG0wqZYfc4jbxKOIzewSF27qn98twGbaN8'
ADMIN_CHAT_ID = 1234567890  # Replace with your admin user ID or a private group/channel ID for logging

SESSION_DIR = "session"
os.makedirs(SESSION_DIR, exist_ok=True)

# ------------------- Logging -------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ------------------- Bot Client -------------------
app = Client(
    f"{SESSION_DIR}/auto_forwarder_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ------------------- User Data -------------------
user_channels = {}  # Structure: {user_id: {"channels": [{"source": id, "target": id}], "active": True, "step": ...}}


# ------------------- Start Command -------------------
@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    user_id = message.from_user.id
    user_channels[user_id] = {"channels": [], "step": "awaiting_source", "active": True}

    await message.reply_text("👋 Welcome! Please send the **Source Channel ID** (Example: -1001234567890).")


# ------------------- Stop Command -------------------
@app.on_message(filters.command("stop"))
async def stop_command(client, message: Message):
    user_id = message.from_user.id

    if user_id in user_channels:
        user_channels[user_id]["active"] = False
        await message.reply_text("⏸️ Forwarding stopped.")
        await app.send_message(ADMIN_CHAT_ID, f"🛑 User {user_id} has stopped forwarding.")
    else:
        await message.reply_text("❗ You haven't started yet. Please use /start first.")


# ------------------- Message Handler -------------------
@app.on_message(filters.text & ~filters.command(["start", "stop"]))
async def get_channel_ids(client, message: Message):
    user_id = message.from_user.id

    if user_id not in user_channels:
        await message.reply_text("❗ Please type /start first.")
        return

    user_data = user_channels[user_id]

    if user_data["step"] == "awaiting_source":
        try:
            source_id = int(message.text.strip())
            user_data["current_source"] = source_id
            user_data["step"] = "awaiting_target"
            await message.reply_text("✅ Source Channel saved!\nNow, please send the **Target Channel ID**.")
        except ValueError:
            await message.reply_text("❗ Please enter a valid numeric Channel ID.")

    elif user_data["step"] == "awaiting_target":
        try:
            target_id = int(message.text.strip())
            user_data["channels"].append({"source": user_data["current_source"], "target": target_id})
            user_data["step"] = "awaiting_source"  # Allow adding more channel pairs

            await message.reply_text(
                f"✅ Target Channel saved!\n\n🔄 Forwarding from `{user_data['current_source']}` to `{target_id}` with a 2s delay.\n\n👉 You can now add another source channel or type /stop to pause forwarding."
            )

            await app.send_message(
                ADMIN_CHAT_ID,
                f"✅ User {user_id} set forwarding:\nSource: `{user_data['current_source']}`\nTarget: `{target_id}`"
            )

        except ValueError:
            await message.reply_text("❗ Please enter a valid numeric Channel ID.")
        except Exception as e:
            logger.error(f"Error while saving target channel: {e}")
            await message.reply_text("❗ An unexpected error occurred. Please try again.")


# ------------------- Forwarding Handler -------------------
@app.on_message(filters.channel)
async def forward_messages(client, message: Message):
    for user_id, user_data in user_channels.items():
        if user_data.get("active"):
            for channel_pair in user_data.get("channels", []):
                if message.chat.id == channel_pair["source"]:
                    try:
                        await asyncio.sleep(2)
                        await message.copy(chat_id=channel_pair["target"])

                        log_msg = f"✅ Forwarded message ID {message.id} from {channel_pair['source']} to {channel_pair['target']} (User {user_id})"
                        logger.info(log_msg)

                        # Log to admin
                        await app.send_message(ADMIN_CHAT_ID, log_msg)

                    except Exception as e:
                        error_msg = f"❌ Error forwarding message ID {message.id}: {e}"
                        logger.error(error_msg)
                        await app.send_message(ADMIN_CHAT_ID, error_msg)


# ------------------- Start Bot -------------------
if __name__ == "__main__":
    logger.info("🚀 Bot is starting...")
    app.run()
