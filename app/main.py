import logging
import sys
import asyncio 
import uuid
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

import config
import database
import rag_service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! I am your friendly AI assistant for NIT Warangal. "
        "Ask me anything about the college, courses, events, etc., and I'll do my best to help based on the info I have."
    )
    logger.info(f"User {user.id} ({user.username}) started the bot.")



async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles incoming text messages (user queries)."""
    user = update.effective_user
    query = update.message.text

    if not query:
        await update.message.reply_text("Please send me a text message.")
        return

    logger.info(f"Received query from {user.id} ({user.username}): {query}")

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    db_connection = None
    try:
        answer = await rag_service.rag_pipeline(query)

        db_connection = database.connect_db()
        if db_connection:
            interaction_id = await asyncio.to_thread(
                database.insert_interaction,
                db_connection,
                user_id=user.id,
                username=user.username,
                query=query,
                answer=answer,
                message_id=update.message.message_id
            )
            logger.info(f"Interaction {interaction_id} stored for user {user.id}.")

            keyboard = [
                [
                    InlineKeyboardButton("👍 Good answer", callback_data=f"feedback_up_{interaction_id}"),
                    InlineKeyboardButton("👎 Poor answer", callback_data=f"feedback_down_{interaction_id}"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(answer, reply_markup=reply_markup)

        else:
             await update.message.reply_text("Sorry, I encountered an issue connecting to the database to log this interaction.")


    except Exception as e:
        logger.error(f"An error occurred during message handling for user {user.id}: {e}", exc_info=True)
        await update.message.reply_text("Sorry, I encountered an internal error while processing your request.")

    finally:
        if db_connection:
            db_connection.close()




async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles callback queries from inline feedback buttons."""
    query = update.callback_query
    user = update.effective_user

    await query.answer("Thanks for your feedback!")

    data = query.data.split('_')
    db_connection = None

    if len(data) == 3 and data[0] == 'feedback':
        feedback_type = data[1] 
        interaction_id_str = data[2]

        try:
            interaction_id = uuid.UUID(interaction_id_str)
            logger.info(f"Received '{feedback_type}' feedback for interaction {interaction_id} from user {user.id}.")

            db_connection = database.connect_db()
            if db_connection:
                await asyncio.to_thread(
                    database.update_feedback,
                    db_connection,
                    interaction_id,
                    feedback_type
                )
                logger.info(f"Database updated with '{feedback_type}' feedback for {interaction_id}.")

                try:
                    await query.edit_message_reply_markup(reply_markup=None)
                except Exception as edit_error:
                     logger.warning(f"Could not edit message after feedback: {edit_error}")

            else:
                 logger.error(f"Failed to connect to database for feedback update for interaction {interaction_id}.")


        except ValueError:
            logger.error(f"Invalid interaction_id format in callback data: {interaction_id_str}")
        except Exception as e:
            logger.error(f"An error occurred during feedback handling for interaction {interaction_id}: {e}", exc_info=True)

    else:
        logger.warning(f"Received unexpected callback data: {query.data}")

    # finally:
    #     if db_connection:
    #         db_connection.close()



if __name__ == '__main__':

    logger.info("Starting NITW CIA RAG Telegram Bot...")


    db_connection = None
    try:
        db_connection = database.connect_db()
        if db_connection:
            database.create_interactions_table(db_connection)
            db_connection.close()
            logger.info("Database initialization successful.")
        else:
            logger.error("Failed to connect to the database on startup. Bot may not function correctly.")
            # Decide if you want to exit here if DB is critical
            # sys.exit(1)
    except Exception as e:
        logger.error(f"Database initialization error: {e}", exc_info=True)
        # Decide if you want to exit here
        # sys.exit(1)


    
    if not config.BOT_TOKEN:
        logger.critical("Telegram bot token not found. Please set TELEGRAM_BOT_TOKEN in your .env file.")
        sys.exit(1)

    application = ApplicationBuilder().token(config.BOT_TOKEN).build()
    logger.info("Telegram Application built.")


    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_feedback))


    logger.info("Bot is polling for updates...")

    application.run_polling(poll_interval=3)

    logger.info("Bot has stopped.")