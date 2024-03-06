from handlers.custom_handlers.history import scheduler
from loader import bot
from telebot.custom_filters import StateFilter
from utils.set_bot_commands import set_default_commands

if __name__ == '__main__':
    scheduler.start()
    bot.add_custom_filter(StateFilter(bot))
    set_default_commands(bot)
    bot.infinity_polling()
