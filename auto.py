import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message

# ------------------- Configuration -------------------
API_ID = 24344133
API_HASH = 'edbe7000baef13fa5a6c45c8edc4be66'
BOT_TOKEN = '7462968272:AAG0wqZYfc4jbxKOIzewSF27qn98twGbaN8'
# -----------------------------------------------------

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

app = Client(
    "auto_forwarder_bot",
    api_id=24344133,
    api_hash='edbe7000baef13fa5a6c45c8edc4be66',
    bot_token='7462968272:AAG0wqZYfc4jbxKOIzewSF27qn98twGbaN8'
)

# Global variables to store selected channels
user_channels = {}


# Command to start the bot and ask for channel IDs
@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    user_id = message.from_user.id
    user_channels[user_id] = {"step": "awaiting_source"}
    await message.reply_text("👋 Welcome! Please send the **Source Channel ID** (Example: -1001234567890).")


# Handle user's channel ID inputs
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
            user_data["target_channel"] = target_id
            user_data["step"] = "ready"
            await message.reply_text(
                f"✅ Target Channel saved!\n\n🔄 Now auto-forwarding messages from `{user_data['source_channel']}` to `{user_data['target_channel']}` with 2s delay."
            )
        except ValueError:
            await message.reply_text("❗ Please enter a valid numeric Channel ID.")


# Forward messages in real-time with user-defined channels
@app.on_message(filters.all)
async def forward_messages(client, message: Message):
    for user_id, user_data in user_channels.items():
        if user_data.get("step") == "ready":
            if message.chat.id == user_data["source_channel"]:
                try:
                    await asyncio.sleep(2)  # 2 second delay
                    await message.copy(chat_id=user_data["target_channel"])
                    logger.info(f"Forwarded message ID {message.id} for user {user_id}")
                except Exception as e:
                    logger.error(f"Error forwarding message ID {message.id}: {e}")


# Start the bot
if __name__ == "__main__":
    logger.info("Bot is starting...")
    app.run()
