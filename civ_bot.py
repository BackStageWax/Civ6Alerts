import telebot
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.environ.get('TOKEN')
if not TOKEN:
    raise ValueError("Добавь TOKEN в переменные окружения на Railway!")

bot = telebot.TeleBot(TOKEN)

game = {
    'chat_id': None,
    'players': {},
    'active': False
}

def mention(uid):
    if uid not in game['players']:
        return 'Неизвестный игрок'
    name = game['players'][uid]['name']
    return f"[{name}](tg://user?id={uid})"

def done_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✅ Ход сделан", callback_data="done"))
    return kb

@bot.message_handler(commands=['new_game'])
def new_game(message):
    if message.chat.type not in ['group', 'supergroup']:
        return bot.reply_to(message, "❌ Только в группе!")
    
    game['chat_id'] = message.chat.id
    game['players'] = {}
    game['active'] = False
    
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✅ Я в игре", callback_data="join"))
    
    bot.send_message(message.chat.id,
                     "🌍 **Civ 6 — Облачная партия (3 игрока)**\n\n"
                     "Все трое нажмите кнопку ниже, чтобы бот мог вас тегать:",
                     parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "join")
def register(call):
    uid = call.from_user.id
    if uid in game['players']:
        return bot.answer_callback_query(call.id, "Ты уже зарегистрирован!")
    
    if len(game['players']) >= 3:
        return bot.answer_callback_query(call.id, "Уже 3 игрока!", show_alert=True)
    
    game['players'][uid] = {'name': call.from_user.first_name}
    
    if len(game['players']) == 3:
        game['active'] = True
        names = "\n".join(f"• {p['name']}" for p in game['players'].values())
        bot.send_message(call.message.chat.id,
                         f"🎉 **Все трое в игре!**\n\nИгроки:\n{names}\n\n"
                         "Теперь просто жмите кнопку когда закончите ход.\nБот сразу тегнет двух остальных.",
                         parse_mode="Markdown", reply_markup=done_keyboard())
    else:
        bot.answer_callback_query(call.id, f"✅ Зарегистрирован ({len(game['players'])}/3)")

@bot.callback_query_handler(func=lambda c: c.data == "done")
def player_done(call):
    if not game.get('active') or call.from_user.id not in game['players']:
        return bot.answer_callback_query(call.id, "Сначала напиши /new_game", show_alert=True)
    
    player = game['players'][call.from_user.id]
    others = [uid for uid in game['players'] if uid != call.from_user.id]
    
    text = (f"✅ **{player['name']}** закончил ход!\n\n"
            f"Теперь ходят:\n→ {mention(others[0])}\n→ {mention(others[1])}")
    
    bot.send_message(game['chat_id'], text, parse_mode="Markdown", reply_markup=done_keyboard())
    bot.answer_callback_query(call.id, "✅ Принято!")

@bot.message_handler(commands=['status'])
def status(message):
    if not game['players']:
        return bot.reply_to(message, "Напиши /new_game")
    names = "\n".join(f"• {p['name']}" for p in game['players'].values())
    bot.reply_to(message, f"**Игроки в игре:**\n{names}", parse_mode="Markdown")

if __name__ == '__main__':
    print("🚀 Бот работает 24/7 в облаке!")
    bot.infinity_polling()
