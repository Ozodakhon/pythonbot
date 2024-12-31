import sqlite3
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    Application,
    CallbackContext,
    MessageHandler,
    filters
)
from telegram.error import BadRequest
import time

# Initialize the database
def init_db():
    conn = sqlite3.connect("bot_users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            referral_link TEXT,
            referred_by INTEGER,
            referral_count INTEGER DEFAULT 0,
            joined_channels INTEGER DEFAULT 0,
            invite_link TEXT
        )
    """)
    conn.commit()
    conn.close()

# Database utility function
def get_db_connection():
    return sqlite3.connect("bot_users.db")

# Start command handler
async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_first_name = update.effective_user.first_name
    referrer_id = None

    # Parse referral ID from the command arguments
    if context.args and context.args[0].isdigit():
        referrer_id = int(context.args[0])

    # Add or retrieve user information in the database
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        user_exists = c.fetchone()

        if not user_exists:
            referral_link = f"https://t.me/{context.bot.username}?start={user_id}"
            c.execute("""
                INSERT INTO users (user_id, referral_link, referred_by)
                VALUES (?, ?, ?)
            """, (user_id, referral_link, referrer_id))
            conn.commit()

    # Send greeting and ask to join channels
    keyboard = [
        [InlineKeyboardButton("Asadbek Abdurakhmonov | Channel", url="https://t.me/+GQewn1TDnxQ2ZWY9")],
        [InlineKeyboardButton("Super Articles", url="https://t.me/articleeeeeees")],
        [InlineKeyboardButton("MULTILEVEL PRACTICE - TOP Results", url="https://t.me/speaking_mashqlari")],
        [InlineKeyboardButton("A'zo bo'ldim ✅", callback_data="joined")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await update.message.reply_text(
        f"Assalomu alaykum *{user_first_name}*! \n\n"
        "🔥 Loyihada ishtirok etish uchun quyidagi kanallarga a'zo bo'ling 👇\n\n"
        "Keyin *\"A'zo bo'ldim ✅\"* tugmasini bosing.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
)
    except Exception as e:
      print(f"Failed to send message to user. Reason: {e}")

# Handle "I have joined" button
async def handle_joined(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    # List of required channels (use your channel usernames)
    required_channels = ["-1002081047677", "-1002426915343"]

    # Check if the user is a member of all the required channels
    for channel in required_channels:
        try:
            # Check if the user is a member of the channel
            chat_member = await context.bot.get_chat_member(channel, user_id)
            if chat_member.status not in ["member", "administrator", "creator"]:
                # If the user is not a member, ask them to join the channels
                await query.message.reply_text("Iltimos, barcha kanallarga a'zo bo'ling va keyin \"A'zo bo'ldim ✅\" tugmasini bosing.")
                return  # Exit the function early if the user is not a member of any channel
        except Exception as e:
            # Handle error if the bot cannot check the user status (e.g., bot doesn't have access to the channel)
            await query.message.reply_text(f"Xatolik: {str(e)}")
            return

    # Update database to mark user as joined
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("UPDATE users SET joined_channels=1 WHERE user_id=?", (user_id,))
        conn.commit()

        # Retrieve the referral link
        c.execute("SELECT referral_link FROM users WHERE user_id=?", (user_id,))
        referral_link = c.fetchone()[0]

    # Send referral link
    photo_path = "greeting.jpg" 
    message = (
    f"<b>Xush kelibsiz!</b>\n\n"
    "Men <b>Asadbek Abdurahmonov</b> (C1) Multilevel/IELTS instructorman.\n\n"
    "🚀 Ushbu loyiha orqali siz <b>15 ta jonli</b> darsdan iborat <b>FULL Multilevel January</b> "
    "(asl narxi 250,000 so'm) kursiga qo'shilishingiz va <b>FEVRAL IMTIHONI UCHUN 1 ta FREE SEAT</b> "
    "yutib olishingiz mumkin.\n\n"
    '<a href="https://t.me/speaking_mashqlari/375">Kurs haqida batafsil</a>\n\n'
    '<a href="https://t.me/speaking_mashqlari/375">Ustoz haqida</a>\n\n'
    "🌟 Kursga <b>BEPUL</b> qo'shilish va <b>FREE SEAT</b> yutib olish imkoniyati uchun 3 ta do'stingizni "
    "loyihaga taklif qiling.\n\n"
    f"<b>Sizning linkingiz:</b> {referral_link}"
)
    keyboard = [
        [InlineKeyboardButton("Do'stlarga yuborish", switch_inline_query=referral_link)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.message.reply_photo(
        photo=open(photo_path, "rb"),
        caption=message,
        parse_mode="HTML",
        reply_markup=reply_markup  
)   
    except Exception as e:
      print(f"Failed to send message to user. Reason: {e}")
    
    await track_referrals(update, context)

# Track referrals
async def track_referrals(update: Update, context: CallbackContext):
    user_id = update.callback_query.from_user.id

    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT referred_by FROM users WHERE user_id=?", (user_id,))
        referrer = c.fetchone()

        if referrer and referrer[0]:
            referrer_id = int(referrer[0])
            # Increment referral count
            c.execute("SELECT referral_count FROM users WHERE user_id=?", (referrer_id,))
            referrer_row = c.fetchone()
            if referrer_row:
                referral_count = referrer_row[0] + 1
                c.execute("UPDATE users SET referral_count = ? WHERE user_id=?", (referral_count, referrer_id))
                conn.commit()
            else:
                print(f"Referrer with user_id={referrer_id} not found in database.")
                return

            try:
                if referral_count == 3:  
                    try:
                        chat_id = "-1002328589211"  
                        # Generate a unique invite link
                        invite_link = await context.bot.create_chat_invite_link(
                            chat_id=chat_id,
                            member_limit=1,  # Allow only one user to join
                            expire_date=None 
                        )

                        # Save the link in the database
                        c.execute("UPDATE users SET invite_link = ? WHERE user_id = ?", (invite_link.invite_link, referrer_id))
                        conn.commit()

                        # Send the unique link to the user
                        await context.bot.send_message(
                            chat_id=referrer_id,
                            text=(
                                f"Tabriklaymiz! 🎉 Sizning havolangiz orqali 3 kishi ro'yxatdan o'tdi. "
                                f"Kursga qo'shilish uchun quyidagi link ustiga bosing:\n{invite_link.invite_link}\n"
                                "The link will expire after you join."
                            )
                        )
                    except BadRequest as e:
                        print(f"Failed to create invite link: {e}")
                else:
                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text=f"Sizning havolangiz orqali {referral_count} kishi ro'yxatdan o'tdi."
                    )
            except Exception as e:
                print(f"Error sending message to referrer {referrer_id}: {e}")

async def fallback(update: Update, context: CallbackContext):
    pass


# Main function
def main():
    init_db()

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

    application = Application.builder().token(bot_token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_joined, pattern="^joined$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
