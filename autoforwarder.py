import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, Chat
import os

# ------------------- Configuration -------------------
API_ID = 24344133
API_HASH = 'edbe7000baef13fa5a6c45c8edc4be66'
BOT_TOKEN = '7462968272:AAG0wqZYfc4jbxKOIzewSF27qn98twGbaN8'

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
user_channels = {}


# ------------------- Handlers -------------------
@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    user_id = message.from_user.id
    user_channels[user_id] = {"step": "awaiting_source"}
    await message.reply_text("👋 Welcome! Please send the **Source Channel ID** (Example: -1001234567890).")


@app.on_message(filters.text & ~filters.command(["start"]))
async def get_channel_ids(client, message: Message):
    user_id = message.from_user.id

    if user_id not in user_channels:
        await message.reply_text("❗ Please type /start first.")
        return

    user_data = user_channels[user_id]

    if user_data["step"] == "awaiting_source":
        try:
            source_id = int(message.text.strip())
            user_data["source_channel"] = source_id
            user_data["step"] = "awaiting_target"
            await message.reply_text("✅ Source Channel saved!\nNow, please send the **Target Channel ID**.")
        except ValueError:
            await message.reply_text("❗ Please enter a valid numeric Channel ID.")

    elif user_data["step"] == "awaiting_target":
        try:
            target_id = int(message.text.strip())
            # Check if bot can post in target channel
            chat: Chat = await client.get_chat(target_id)
            if not chat.permissions or not chat.permissions.can_send_messages:
                await message.reply_text("❗ Bot may not have permission to post in this channel. Please make sure the bot is an admin with post rights.")
                return

            user_data["target_channel"] = target_id
            user_data["step"] = "ready"

            await message.reply_text(
                f"✅ Target Channel saved!\n\n🔄 Now auto-forwarding messages from `{user_data['source_channel']}` to `{user_data['target_channel']}` with a 2s delay.\n\n👉 Make sure the bot is a **member in the source channel** and **admin in the target channel**."
            )
        except ValueError:
            await message.reply_text("❗ Please enter a valid numeric Channel ID.")
        except Exception as e:
            logger.error(f"Error while verifying target channel: {e}")
            await message.reply_text("❗ Could not access target channel. Make sure the bot is added and has permission.")


@app.on_message(filters.channel)
async def forward_messages(client, message: Message):
    for user_id, user_data in user_channels.items():
        if user_data.get("step") == "ready" and message.chat.id == user_data["source_channel"]:
            try:
                await asyncio.sleep(2)  # 2 second delay
                await message.copy(chat_id=user_data["target_channel"])
                logger.info(f"✅ Forwarded message ID {message.id} from {user_data['source_channel']} to {user_data['target_channel']}")
            except Exception as e:
                logger.error(f"❌ Error forwarding message ID {message.id}: {e}")


# ------------------- Start Bot -------------------
if __name__ == "__main__":
    logger.info("🚀 Bot is starting...")
    app.run()
