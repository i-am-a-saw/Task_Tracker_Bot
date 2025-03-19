import telebot
import humanize
from django.db.models.fields import return_None
from pymongo import ReturnDocument
from telebot import types
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
import pymongo
import datetime
from bson.objectid import ObjectId
import schedule
import time
import threading
import logging
from telegram.ext import Updater
from telegram.ext import  CallbackQueryHandler
from telegram.ext import  CommandHandler
from telegram import  ReplyKeyboardRemove
import random



stickers = ['CAACAgIAAxkBAAIKgWfbO4oF66Obk9V2H8NPNE3VqZnzAAKCIgACCV4RSBYu-QxJ3nfYNgQ',
            'CAACAgIAAxkBAAIKomfbPyIL1IHeU2N7k8RBBRiaI6p8AAIoTAACkONYSRHIGo-6mVI-NgQ',
            'CAACAgQAAxkBAAIKoGfbPxs7GLQ7G-Pn7SUOanYxY-JEAAK5DwACunC5UzPSaKzENx21NgQ',
            'CAACAgQAAxkBAAIKnmfbPw5p1l6_ZenFBS1Oo0svcPH0AAJ8AAPOOQgNOaqHaFs-KMc2BA',
            'CAACAgQAAxkBAAIKpGfbP2XT1_fzmJgx28n_HBrzXW3oAAKJAAPOOQgNfn_UJplquP82BA',
            'CAACAgQAAxkBAAIKyGfbQKXEkpb6Dy-bsMos3IYicuktAAKFAAPOOQgNp5kUNNSibzw2BA',
            'CAACAgIAAxkBAAIKymfbQP8YnfUTVygOXj2yxvuQarf5AAIRGAAC_nrhS7KxvOu4KcSbNgQ',
            'CAACAgIAAxkBAAIKxmfbQJHorRMk2xHwJU8hkU0Yw909AAL5FgAC6L7hS3taBUpsIRT6NgQ']




client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["mydatabase"]
tasks_collection = db["tasks3"]

token = ('7505960440:AAF1VsEmvFSAFXE-40rzv7m4wUPX34tc3lI')
bot = telebot.TeleBot(token)
user_data = {}


def create_menu_keyboard():
    menu_keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
    menu_keyboard.add(
        KeyboardButton("📝 Create Task"),
        KeyboardButton("📋 List All"),
        KeyboardButton("⏰ Deadlines"),
        KeyboardButton("🔔 Manage notifications")
    )
    return menu_keyboard

@bot.message_handler(content_types=['sticker'])
def send_sticker_id(message):
    bot.send_message(message.chat.id, f'This sticker id: {message.sticker.file_id}')


# Start command handler
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "🌟 *Welcome to your Task Manager Bot!*\n\nPlease choose an option:",
        parse_mode="Markdown",
        reply_markup=create_menu_keyboard()
    )

# Handle menu button selections
@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    if message.text == "📝 Create Task" or message.text == "/create_task":
        button_calcel = telebot.types.InlineKeyboardButton(text="Cancel",
                                                           callback_data=f'cancel|{1}')
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(button_calcel)
        bot.send_message(message.chat.id, "What is the name of the task? 🚀", parse_mode="Markdown", reply_markup=keyboard)
        chat_id = message.chat.id
        user_data[chat_id] = {}
        bot.register_next_step_handler(message, get_task_name)
    elif message.text == "📋 List All" or message.text == "/view_tasks":
        view_tasks(message, 0)
    elif message.text == "⏰ Deadlines" or message.text == "/deadlines":
        deadlines(message)
    elif message.text == "🔔  Manage notifications" or message.text == "/notifications":
        bot.send_message(message.chat.id, ":", parse_mode="Markdown")
    elif message.text == "sr":
        set_reminder(message)
    else:
        bot.reply_to(message, "❌ Invalid option. Please select from the menu below:", reply_markup=create_menu_keyboard())


#Section for CREATING TASKS
@bot.message_handler(commands=['addtask'])
def add_task(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}

    button_calcel = telebot.types.InlineKeyboardButton(text="Cancel creating",
                                                       callback_data=f'cancel|{1}')
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(button_calcel)

    bot.send_message(chat_id, "What is the name of the task?", reply_markup=keyboard)
    bot.register_next_step_handler(message, get_task_name)

def get_task_name(message):
    chat_id = message.chat.id
    user_data[chat_id]['task_name'] = message.text

    button_calcel = telebot.types.InlineKeyboardButton(text="Cancel creating",
                                                       callback_data=f'cancel|{2}')
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(button_calcel)

    bot.send_message(chat_id, "Please describe the task.", reply_markup=keyboard)
    bot.register_next_step_handler(message, get_task_description)

def get_task_description(message):
    chat_id = message.chat.id
    user_data[chat_id]['description'] = message.text

    button_calcel = telebot.types.InlineKeyboardButton(text="Cancel",
                                                       callback_data=f'cancel|{3}')
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(button_calcel)

    bot.send_message(chat_id, "Let's set up the deadline for your task", reply_markup=keyboard)
    get_task_deadline(message)

def get_task_deadline(message):
    now = datetime.datetime.now()
    calendar, step = DetailedTelegramCalendar(min_date=datetime.date(now.year, now.month, now.day)).build()
    bot.send_message(m.chat.id,
                     f"Select {LSTEP[step]}",
                     reply_markup=calendar)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func())
def cal(c):
    now = datetime.datetime.now()
    chat_id = c.message.chat.id

    result, key, step = DetailedTelegramCalendar(min_date=datetime.date(now.year, now.month, now.day)).process(c.data)
    if not result and key:
        bot.edit_message_text(f"Select {LSTEP[step]}",
                              c.message.chat.id,
                              c.message.message_id,
                              reply_markup=key)
    elif result:
        bot.delete_message(c.message.chat.id, c.message.message_id - 1)
        bot.delete_message(c.message.chat.id, c.message.message_id)


        deadline = datetime.datetime.strptime(str(result), '%Y-%m-%d')
        user_data[chat_id]['deadline'] = deadline

        task = {
            'user_id': c.from_user.id,
            'chat_id': chat_id,
            'task_name': user_data[chat_id]['task_name'],
            'description': user_data[chat_id]['description'],
            'deadline': user_data[chat_id]['deadline'],
            'created_at': datetime.datetime.now(),
            'done': False
        }
        tasks_collection.insert_one(task)

        bot.send_message(chat_id, "Task saved successfully!")

def get_task_deadline(message):
    now = datetime.datetime.now()
    calendar, step = DetailedTelegramCalendar(min_date=datetime.date(now.year, now.month, now.day)).build()
    bot.send_message(message.chat.id,
                     f"Select {LSTEP[step]}",
                     reply_markup=calendar)

@bot.callback_query_handler(func=lambda call: call.data.startswith('cancel'))
def cancel(call):

    _, edge = call.data.split("|")
    for i in range(int(edge)*2):

        bot.delete_message(call.message.chat.id, call.message.message_id - i)

    bot.clear_step_handler(call.message)



# Section for LISTING TASKS
@bot.message_handler(commands=['viewtasks'])
def view_tasks(message, today):
    chat_id = message.chat.id
    tasks = tasks_collection.find({'chat_id': chat_id})

    if tasks_collection.count_documents({'chat_id': chat_id}) == 0:
        bot.send_message(chat_id, "You have no tasks saved.")
    else:
        bot.send_message(message.chat.id, "📜 Here are all your tasks:", parse_mode="Markdown")

        button_done = telebot.types.InlineKeyboardButton(text="Mark as done",
                                                         callback_data=f'mark_as_done|{0}')
        button_undone = telebot.types.InlineKeyboardButton(text="Mark as undone",
                                                         callback_data=f'mark_as_undone|{0}')
        button_change = telebot.types.InlineKeyboardButton(text="Edit",
                                                           callback_data='edit_task')
        button_delete = telebot.types.InlineKeyboardButton(text="Delete",
                                                           callback_data='delete_task')
        for task in tasks:
            keyboard = telebot.types.InlineKeyboardMarkup()

            task_id = task["_id"]
            task_name = task['task_name']
            description = task['description']
            done = task['done']

            deadline = task['deadline']

            created_at = task['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            response = (
                f"📌 *{task_name}*\n"
                f"📝 {description}\n"
                f"⏰ {humanize.naturaldate(deadline).capitalize()}\n"
            )
            if not done:
                response += (f"✖ Not done\n")
                keyboard.add(button_done, button_change, button_delete)
            else:
                response += (f"✅ Done!\n")
                keyboard.add(button_undone, button_change, button_delete)
            bot.send_message(chat_id, response, parse_mode="Markdown", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith('mark_as_done'))
def mark_as_done(call):
    _, deadline_flag = call.data.split('|')  # Split by the delimiter
    deadline_flag = int(deadline_flag)  # Convert to integer


    message = call.message


    task_name = ""
    for item in message.text.split()[1:]:
        if item != "📝":
            task_name += item + " "
        else:
            task_name = task_name.rstrip()
            break

    tasks_collection.find_one_and_update({"task_name":task_name}, {'$set': {"done": True}}, return_document= ReturnDocument.AFTER)
    text = message.text[:-11]

    chat_id = message.chat.id
    message_id = message.message_id

    button_undone = telebot.types.InlineKeyboardButton(text="Mark as undone",
                                                       callback_data=f'mark_as_undone|{deadline_flag}')
    button_change = telebot.types.InlineKeyboardButton(text="Edit",
                                                       callback_data='edit_task')
    button_delete = telebot.types.InlineKeyboardButton(text="Delete",
                                                       callback_data='delete_task')
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(button_undone)
    if not deadline_flag:


        keyboard.add(button_change, button_delete)

    bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                         text=text + "\n✅ Done!", parse_mode="Markdown", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith('mark_as_undone'))
def mark_as_undone(call):
    _, deadline_flag = call.data.split('|')  # Split by the delimiter
    deadline_flag = int(deadline_flag)  # Convert to integer
    message = call.message

    task_name = ""
    for item in message.text.split()[1:]:
        if item != "📝":
            task_name += item + " "
        else:
            task_name = task_name.rstrip()
            break
    tasks_collection.find_one_and_update({"task_name":task_name}, {'$set': {"done": False}}, return_document= ReturnDocument.AFTER)
    text = message.text[:-8]

    chat_id = message.chat.id
    message_id = message.message_id

    button_done = telebot.types.InlineKeyboardButton(text="Mark as done",
                                                     callback_data=f'mark_as_done|{deadline_flag}')
    button_change = telebot.types.InlineKeyboardButton(text="Edit",
                                                       callback_data='edit_task')
    button_delete = telebot.types.InlineKeyboardButton(text="Delete",
                                                       callback_data='delete_task')
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(button_done)

    if not deadline_flag:
        keyboard.add(button_change, button_delete)

    bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                         text=text + "\n✖ Not done", parse_mode="Markdown", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data == 'edit_task')
def save_btn(call):
    message = call.message
    chat_id = message.chat.id
    message_id = message.message_id
    task_name = ""
    for item in message.text.split()[1:]:
        if item != "📝":
            task_name += item + " "
        else:
            task_name = task_name.rstrip()
            break

    button_name = telebot.types.InlineKeyboardButton(text="Name",
                                                     callback_data='edit_name')
    button_desc = telebot.types.InlineKeyboardButton(text="Description",
                                                     callback_data='edit_desc')
    button_deadline = telebot.types.InlineKeyboardButton(text="Deadline",
                                                         callback_data='edit_deadline')
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(button_name, button_desc, button_deadline)
    bot.send_message(chat_id, text=f"What would you like to change for the task __*{task_name}*__?", parse_mode="MarkdownV2", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data == 'edit_name')
def edit_name(call):
    message = call.message
    task_name = message.text[43:-1]
    chat_id = message.chat.id

    bot.send_message(chat_id, text="Enter new name of the task:")
    bot.register_next_step_handler(message, update_task_name, task_name)

def update_task_name(message, task_name):
    new_name = message.text
    tasks_collection.find_one_and_update({"task_name":task_name}, {'$set': {"task_name": new_name}}, return_document= ReturnDocument.AFTER)
    bot.reply_to(message, f"Task updated: {new_name}")


@bot.callback_query_handler(func=lambda call: call.data == 'edit_desc')
def edit_desc(call):
    message = call.message
    task_name = message.text[43:-1]
    chat_id = message.chat.id

    bot.send_message(chat_id, text="Enter new description of the task:")
    bot.register_next_step_handler(message, update_task_desc, task_name)

def update_task_desc(message, task_name):
    new_desc = message.text
    tasks_collection.find_one_and_update({"task_name":task_name}, {'$set': {"description": new_desc}}, return_document= ReturnDocument.AFTER)
    bot.reply_to(message, f"Task updated: {task_name}")


@bot.callback_query_handler(func=lambda call: call.data == 'edit_deadline')
def edit_deadline(call):
    message = call.message
    task_name = message.text[43:-1]
    chat_id = message.chat.id

    bot.send_message(chat_id, text="Enter new deadline of the task:")
    bot.register_next_step_handler(message, update_task_deadline, task_name)

def update_task_deadline(message, task_name):
    new_deadline = datetime.datetime.strptime(message.text, '%Y-%m-%d')
    tasks_collection.find_one_and_update({"task_name":task_name}, {'$set': {"deadline": new_deadline}}, return_document= ReturnDocument.AFTER)
    bot.reply_to(message, f"Task updated: {task_name}")


@bot.callback_query_handler(func=lambda call: call.data == 'delete_task')
def delete_task(call):
        message = call.message

        task_name = ""
        for item in message.text.split()[1:]:
            if item != "📝":
                task_name += item + " "
            else:
                task_name = task_name.rstrip()
                break
        chat_id = message.chat.id

        button_yes = telebot.types.InlineKeyboardButton(text="Yes",
                                                           callback_data=f'yes|{call.message.message_id}')
        button_no = telebot.types.InlineKeyboardButton(text="No",
                                                           callback_data=f'no|{call.message.message_id}')
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(button_yes, button_no)

        bot.send_message(chat_id, text=f"Are you sure you want to delete the task __*{task_name}*__?", parse_mode="MarkdownV2", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith('yes'))
def yes(call):
    message = call.message
    chat_id = message.chat.id
    task_name = message.text[41:-1]
    _, message_id = call.data.split("|")
    tasks_collection.find_one_and_delete({"task_name": task_name})
    bot.delete_message(chat_id, message_id)
    bot.delete_message(chat_id, message.message_id)
    #bot.send_message(chat_id, f"Task deleted: {task_name}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('no'))
def no(call):
    chat_id = call.message.chat.id
    _, message_id = call.data.split("|")
    bot.delete_message(chat_id, call.message.message_id)





#Section for DEADLINES
@bot.message_handler(commands=['deadlines'])
def deadlines(message):
    chat_id = message.chat.id
    tasks = tasks_collection.find({'chat_id': chat_id})

    if tasks_collection.count_documents({'chat_id': chat_id}) == 0:
        bot.send_message(chat_id, "You have no tasks saved.")
    elif tasks_collection.count_documents({'chat_id': chat_id, "done": False}) == 0:
        bot.send_message(message.chat.id, "You've finished all your duties for today! Well done😎", parse_mode="Markdown")
        t = stickers[random.randint(0, len(stickers)-1)]

        bot.send_sticker(message.chat.id, t)
    else:
        bot.send_message(message.chat.id, "⏳ Here are your upcoming deadlines!", parse_mode="Markdown")

        button_done = telebot.types.InlineKeyboardButton(text="Mark as done",
                                                         callback_data=f'mark_as_done|{1}')
        button_undone = telebot.types.InlineKeyboardButton(text="Mark as undone",
                                                           callback_data=f'mark_as_undone|{1}') #1 is a deadline flag (used for deadlines func)

        for task in tasks:
            keyboard = telebot.types.InlineKeyboardMarkup()

            task_id = task["_id"]
            task_name = task['task_name']
            description = task['description']
            done = task['done']
            deadline = task['deadline']
            created_at = task['created_at'].strftime('%Y-%m-%d %H:%M:%S')

            now = datetime.datetime.now()

            if deadline >= datetime.datetime.today() - datetime.timedelta(hours=now.hour) - datetime.timedelta(minutes=now.minute) - datetime.timedelta(minutes=1) and not done:

                response = (
                    f"📌 *{task_name}*\n"
                    f"📝 {description}\n"
                    f"⏰ {humanize.naturaldate(deadline).capitalize()}\n"
                )
                if not done:
                    response += (f"✖ Not done\n")
                    keyboard.add(button_done)
                else:
                    response += (f"✅ Done!\n")
                    keyboard.add(button_undone)
                bot.send_message(chat_id, response, parse_mode="Markdown", reply_markup=keyboard)





#Section for NOTIFICATIONS
@bot.message_handler(commands=["setreminder"])
def set_reminder(message):
    bot.reply_to(message, "Please enter the task ID for which you want to set a reminder:")
    bot.register_next_step_handler(message, ask_for_reminder_time)

def ask_for_reminder_time(message):
    try:
        task_name = message.text
        user_id = message.from_user.id
        task = tasks_collection.find_one({"task_name": task_name, "user_id": user_id})
        if task:
            bot.reply_to(message, "Please enter the reminder time in the format HH:MM (24-hour format):")

            bot.register_next_step_handler(message, save_reminder, task_name)

        else:
            bot.reply_to(message, "Task not found or you don't have permission to set a reminder.")
    except:
        bot.reply_to(message, "Invalid task ID. Please try again.")

def save_reminder(message, task_name):
    reminder_time = message.text
    try:
        # Validate the time format
        time.strptime(reminder_time, "%H:%M")
        tasks_collection.update_one({"task_name": task_name}, {"$set": {"reminder": reminder_time}})
        bot.reply_to(message, f"Reminder set for {reminder_time}.")

        # Schedule the notification
        schedule_notification(task_name, reminder_time, message.chat.id)

    except ValueError:
        bot.reply_to(message, "Invalid time format. Please use HH:MM (24-hour format).")

def schedule_notification(task_name, reminder_time, chat_id):

    def send_reminder():
        task = tasks_collection.find_one({"task_name": task_name})


        if task:

            bot.send_message(chat_id, f"Reminder: Don't forget to complete your task: {task['description']}")

    # Schedule the reminder

    schedule.every().day.at(reminder_time).do(send_reminder)




bot.polling(none_stop=True, interval=0)