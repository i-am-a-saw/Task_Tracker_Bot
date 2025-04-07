import telebot
import humanize
from pymongo import ReturnDocument
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
import pymongo
import datetime
import random
import secrets
import threading
import time
import pytz
from bson.objectid import ObjectId

"""
VARIABLES:
    time_zone - a string with required UTC timezone, standart is Europe/Moscow
    
    client - a client for local mongo database
    db - database, where tasks are stored
    tasks_collection - section of db, where tasks are stored
    
    token - a unique token for connection with bot
    bot - an interface, used to send messsages, edit them and proceed user input
    user_data - a global dictionary that carries task_name, task_description, deadline and the status (done/undone) of the task
    
    notification_mode - a flag, which defines whether to save task or to set a deadline for it. needed for function 'edit_calendar'
    notif_time - a global var, which carries the time of notification, which is going to be set
    notif_id - a global var, which carries the id of notification, which is going to be set
    
    message - an argument for reply functions that carry the message itself and its details: id, text
    chat_id - ID of the current chat with the specific user. It is used to send messages. (chat_id = message.chat.id)
    call - an argument for functions that are bound to inline buttons. works as message for commands
    
    review_hour - determines when to check if deadlines are missed
    review_minute - determines when to check if deadlines are missed
    
    stickers - list with stickers' IDs, which are sent when user completed all the tasks
"""

stickers = ['CAACAgIAAxkBAAIKgWfbO4oF66Obk9V2H8NPNE3VqZnzAAKCIgACCV4RSBYu-QxJ3nfYNgQ',
            'CAACAgIAAxkBAAIKomfbPyIL1IHeU2N7k8RBBRiaI6p8AAIoTAACkONYSRHIGo-6mVI-NgQ',
            'CAACAgQAAxkBAAIKoGfbPxs7GLQ7G-Pn7SUOanYxY-JEAAK5DwACunC5UzPSaKzENx21NgQ',
            'CAACAgQAAxkBAAIKnmfbPw5p1l6_ZenFBS1Oo0svcPH0AAJ8AAPOOQgNOaqHaFs-KMc2BA',
            'CAACAgQAAxkBAAIKpGfbP2XT1_fzmJgx28n_HBrzXW3oAAKJAAPOOQgNfn_UJplquP82BA',
            'CAACAgQAAxkBAAIKyGfbQKXEkpb6Dy-bsMos3IYicuktAAKFAAPOOQgNp5kUNNSibzw2BA',
            'CAACAgIAAxkBAAIKymfbQP8YnfUTVygOXj2yxvuQarf5AAIRGAAC_nrhS7KxvOu4KcSbNgQ',
            'CAACAgIAAxkBAAIKxmfbQJHorRMk2xHwJU8hkU0Yw909AAL5FgAC6L7hS3taBUpsIRT6NgQ']

vip_stickers = ['CAACAgIAAxkBAAI2sGfqtPxMuyCiVwteriLPxUbBc96XAAI0awACzZcZSC9V1WwNNiltNgQ',
                'CAACAgIAAxkBAAI2sWfqtQZqcx2chARsnfS4PsLFsjk7AAKgTgACM_ggSL6bd1sEzwmUNgQ',
                'CAACAgIAAxkBAAI2uGfqtVI7nvDNzcMGCOC8hU1rViadAAIKTQACCHIhSCFVFHEwhm3eNgQ',
                'CAACAgIAAxkBAAI2smfqtQs72pgz-iVQJyjwt1WKCJVxAAITTwACFooYSIwJBqfQPeC2NgQ',
                'CAACAgIAAxkBAAI2s2fqtRLSs8fV1LnG3JrqbkoMclGoAAIlTwACHzEZSNOZxl13FQGUNgQ',
                'CAACAgIAAxkBAAI2vmfqtVSG2gu_7xCMj2q-Zdnd3_SvAAJ7VwACm8sZSFCQCUnfktIAATYE',
                'CAACAgIAAxkBAAI2wGfqtVXKWI5WsltpG4vTJGoOXXmiAAIiZAACMOoYSK8twsfzGcaUNgQ',
                'CAACAgIAAxkBAAI2wmfqtVbJKxGY81NkHILAsaK913JtAALDXAACUT4ZSKX1czFgqao_NgQ',
                'CAACAgIAAxkBAAI2xGfqtVqZGSB4--9MiKawViKS7dM1AAKqWwACaasZSDACiV33IrbYNgQ',
                'CAACAgIAAxkBAAI2xmfqtV2oQ1ngFBbqkXXpLPH1d07QAAJzUAACZ0QgSA5-VlRHxPIYNgQ']

time_zone = "Europe/Moscow"

client = pymongo.MongoClient("mongodb://nick_gay:g5e*(h.5Y@193.233.84.102:63852/mydatabase")  # mongodb://your_username:your_password@remote_server_ip:27017/your_database_name
db = client["mydatabase"]
tasks_collection = db["tasks4"]

token = secrets.TOKEN
bot = telebot.TeleBot(token)
user_data = {}

notification_mode = 0
notif_time = ""
notif_task = ""

review_hour = 0
review_minute = 5

IDs = ["1226646270", "1615057164", "897817045" ,"1948432640", "1638334330"]
       #julia

def check_missed_deadlines():
    '''once a day this func checks all deadlines. if deadline is skipped, the status is changed to "missed"'''

    while True:
        now = datetime.datetime.now(pytz.timezone(time_zone))
        if now.hour == review_hour and now.minute == review_minute:
            tasks = tasks_collection.find({})

            for task in tasks:
                print(task["task_name"])
                deadline = datetime.datetime.combine(task["deadline"], datetime.datetime.now(pytz.timezone(time_zone)).time())
                status = task["status"]

                if deadline < now and status == "not done":
                    tasks_collection.find_one_and_update({"_id": task["_id"]}, {"$set": {"status": "missed"}})
                    bot.send_message(task["chat_id"], f"You've missed your deadline for \"{task['task_name']}\" 😔\nTry to manage your time properly!")

            time.sleep(120)
        time.sleep(30)


def start_notification_thread():
    '''this func is called just after starting the bot. it goes through list of notifications and sets timers for them'''

    while True:
        now = datetime.datetime.now(pytz.timezone(time_zone))

        #bot.send_message("1638334330", "hello")

        for task in tasks_collection.find({}):
            temp_notif_list = task["notifications"]
            # bot.send_message("1638334330", task["task_name"])
            for notif in temp_notif_list:
                # bot.send_message("1638334330", "Time:\n"+
                # f"{notif.month}, {now.month}\n"+
                # f"{notif.day}, {now.day}\n"+
                # f"{notif.hour}, {now.hour}\n"+
                # f"{notif.minute}, {now.minute}")

                if (int(notif.month) == int(now.month) and
                        int(notif.day) == int(now.day) and
                        int(notif.hour) == int(now.hour) and
                        int(notif.minute) == int(now.minute)):

                    bot.send_message("1638334330", "THIS IS IT")
                    bot.send_message(task["chat_id"], f"\"{task["task_name"]}\" is waiting! It's time to complete it")

                    bot.send_message("1638334330",
                                     f"message has just been sent, text is about {task["task_name"]}")

                    notif_list = task["notifications"]
                    notif_list.pop(0)
                    tasks_collection.find_one_and_update({"_id": ObjectId(task["_id"])},
                                                         {'$set': {"notifications": notif_list}},
                                                         return_document=ReturnDocument.AFTER)

                    bot.send_message("1638334330",
                                     f"message has been sent to {task["chat_id"]}, text is about {task["task_name"]}")


        time.sleep(20)


    # for task in tasks_collection.find({}):
    #     # tasks_collection.find_one_and_update({"task_name": task["task_name"]}, {"$set": {"notifications": []}})
    #
    #     for notification in task["notifications"]:
    #         now = datetime.datetime.now(pytz.timezone(time_zone)).time()
    #         delay = (notification - datetime.datetime.combine(
    #             datetime.datetime.today(), now)).seconds
    #
    #
    #         threading.Timer(delay, send_notification, args=[task["chat_id"], task["_id"]]).start()


def not_too_late(message):
    '''checks if the message was sent at most 1 minute ago. needed to prevent bot from answering to messages, which were sent when
    bot was offline'''

    message_time = message.date
    current_time = int(time.time())
    if current_time - message_time < 60:
        return 1
    return 0


def create_menu_keyboard():
    '''creates 4 buttons in menu: "Create task", "List all tasks", "View actual deadlines","Manage notifications" '''

    menu_keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
    menu_keyboard.add(
        KeyboardButton("📝 Create Task"),
        KeyboardButton("📋 List All"),
        KeyboardButton("⏰ Deadlines"),
        KeyboardButton("🔔 Manage notifications")
    )
    return menu_keyboard


@bot.message_handler(commands=['start'])
def send_welcome(message):
    '''replies to the command "/start" and creates the menu with 4 buttons'''

    chat_id = message.chat.id
    bot.send_message(chat_id,
                     "🌟 *Welcome to your Task Manager Bot!*\n\nPlease choose an option:",
                     parse_mode="Markdown",
                     reply_markup=create_menu_keyboard()
                     )

@bot.message_handler(content_types=['sticker'])
def send_sticker_id(message):
    bot.send_message(message.chat.id, message.sticker.file_id)

@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    print(message.message_id, message.chat.id)
    now = datetime.datetime.now(pytz.timezone("Europe/Moscow"))
    #bot.send_message("1638334330", f"{now}")
    #bot.send_message("1638334330", f"{now.strftime("%Y:%m:%d %H:%M:%S %Z %z")}")
    #bot.delete_message(chat_id="1638334330", message_id="")
    '''replies to text commands, sent by user. if command is not recognizes, asks to select command from menu'''

    if not_too_late(message):
        if message.text == "/send":
            data = {}
            get_user(message, data)
        elif message.text == "/timur_govnoed":
            with open('timur.jpg', 'rb') as photo:
                bot.send_photo(message.chat.id, photo)
        elif message.text == "/maskot":
            with open('fuck.jpg', 'rb') as photo:
                bot.send_photo(message.chat.id, photo)
        elif message.text == "/jumpskare":
            with open('maks.jpg', 'rb') as photo:
                bot.send_photo(message.chat.id, photo)
        elif message.text == "/sex":
            bot.send_message(message.chat.id, "иди уроки учи не вырос еще")
        elif message.text == "/sexxx":
            bot.send_sticker(message.chat.id, vip_stickers[random.randint(0, len(vip_stickers)-1)])
        elif message.text == "📝 Create Task" or message.text == "/create_task":
            add_task(message)
        elif message.text == "📋 List All" or message.text == "/view_tasks":
            view_tasks(message, 0)
        elif message.text == "⏰ Deadlines" or message.text == "/deadlines":
            deadlines(message)
        elif message.text == "🔔 Manage notifications" or message.text == "/notifications":
            list_tasks_for_notification(message)
        else:
            bot.reply_to(message, "❌ Invalid option. Please select from the menu below:",
                         reply_markup=create_menu_keyboard())


def get_user(message, data):
    bot.send_message("1638334330", "Enter the user ID")
    bot.register_next_step_handler(message, get_msg, data)

def get_msg(message, data):
    data["user_id"] = message.text
    print("id:", data["user_id"])
    bot.send_message("1638334330", "Enter the message text")
    bot.register_next_step_handler(message, send_msg, data)

def send_msg(message, data):
    data["msg"] = message.text
    print("msg:", data["msg"])
    bot.send_message("1638334330", f"I send \"{data["msg"]}\" to {data["user_id"]}")
    bot.send_message(data["user_id"], data["msg"])


# ----------------------------------------
# Section for CREATING TASKS
# ----------------------------------------
@bot.message_handler(commands=['addtask'])
def add_task(message):
    '''asks the user for the name of the task and registers next function "save_task_name"'''

    chat_id = message.chat.id

    button_cancel = telebot.types.InlineKeyboardButton(text="Cancel creating",
                                                       callback_data=f'cancel_creation|{1}')
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(button_cancel)

    bot.send_message(chat_id, "What is the name of the task?", reply_markup=keyboard)
    bot.register_next_step_handler(message, save_task_name)


def save_task_name(message):
    '''saves tash name, then asks the user for description of the task and registers next function "sace_task_description"'''

    chat_id = message.chat.id
    user_data[chat_id] = {}  # in this dict the task will be saved

    if "." in message.text:
        bot.send_message(chat_id, "Sorry, try again")
        bot.register_next_step_handler(add_task(message))
        return

    user_data[chat_id]['task_name'] = message.text

    button_cancel = telebot.types.InlineKeyboardButton(text="Cancel creating",
                                                       callback_data=f'cancel_creation|{2}')
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(button_cancel)

    bot.send_message(chat_id, "Please describe the task.", reply_markup=keyboard)
    bot.register_next_step_handler(message, save_task_description)


def save_task_description(message):
    '''saves task description, then asks the user for deadline and registers next function "get_task_deadline"'''

    chat_id = message.chat.id
    user_data[chat_id]['description'] = message.text

    button_calcel = telebot.types.InlineKeyboardButton(text="Cancel",
                                                       callback_data=f'cancel_creation|{3}')
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(button_calcel)

    bot.send_message(chat_id, "Let's set up the deadline for your task", reply_markup=keyboard)
    get_task_deadline(message)


def get_task_deadline(message):
    '''creates a calendar for user to choose deadline. the calendar is edited 2 times for month and year selection'''

    global notification_mode
    notification_mode = 0

    chat_id = message.chat.id
    now = datetime.datetime.now(pytz.timezone(time_zone))
    calendar, step = DetailedTelegramCalendar(min_date=datetime.date(now.year, now.month, now.day)).build()

    bot.send_message(chat_id,
                     f"Select {LSTEP[step]}",
                     reply_markup=calendar, )


@bot.callback_query_handler(func=DetailedTelegramCalendar.func())
def edit_calendar(call):
    '''gets the deadline and saves the task to database'''

    now = datetime.datetime.now(pytz.timezone(time_zone))
    chat_id = call.message.chat.id

    result, key, step = DetailedTelegramCalendar(min_date=datetime.date(now.year, now.month, now.day)).process(
        call.data)
    if not result and key:
        bot.edit_message_text(f"Select {LSTEP[step]}",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key)
    elif result:
        bot.delete_message(call.message.chat.id, call.message.message_id - 1)
        bot.delete_message(call.message.chat.id, call.message.message_id)

        if notification_mode:

            notification_day = datetime.datetime.strptime(str(result), '%Y-%m-%d')
            try:
                if "." in notif_time:
                    notification_time = datetime.datetime.strptime(notif_time, "%H.%M").time()
                elif ":" in notif_time:
                    notification_time = datetime.datetime.strptime(notif_time, "%H:%M").time()
                else:
                    notification_time = datetime.datetime.strptime(notif_time, "%H %M").time()
            except:
                bot.send_message(chat_id, "Invalid time format😔 Please try setting notification again")
                return

            now = datetime.datetime.now(pytz.timezone(time_zone)).time()

            delay = (datetime.datetime.combine(notification_day, notification_time) - datetime.datetime.combine(
                datetime.datetime.today(), now)).seconds

            print("got an id:", notif_task)

            notification_list = tasks_collection.find_one({"_id": ObjectId(notif_task)})["notifications"]
            notification_list.append(datetime.datetime.combine(notification_day, notification_time))
            notification_list.sort()
            print(notification_list)
            tasks_collection.find_one_and_update({"_id": ObjectId(notif_task)},
                                                 {'$set': {"notifications": notification_list}},
                                                 return_document=ReturnDocument.AFTER)
            print(tasks_collection.find_one({"_id": ObjectId(notif_task)})["notifications"])

            # send_notification.apply_async(args=[chat_id, task_name], countdown=delay)
            # threading.Timer(delay, send_notification, args=[chat_id, notif_task]).start()

            bot.send_message(call.message.chat.id,
                             f"Notification scheduled. You will receive a message at {notification_time.hour:02d}:{notification_time.minute:02d}.")

        if not notification_mode:
            deadline = datetime.datetime.strptime(str(result), '%Y-%m-%d')
            user_data[chat_id]['deadline'] = deadline

            task = {
                'user_id': call.from_user.id,
                'chat_id': chat_id,
                'task_name': user_data[chat_id]['task_name'],
                'description': user_data[chat_id]['description'],
                'deadline': user_data[chat_id]['deadline'],
                'created_at': datetime.datetime.now(pytz.timezone(time_zone)),
                'status':'not done',
                'notifications': []
            }
            tasks_collection.insert_one(task)

            bot.send_message(chat_id, "Task saved successfully!")


@bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_creation'))
def cancel_creation(call):
    '''terminates the creation of a task and deletes related messages'''

    _, last_message_to_delete = call.data.split("|")
    for i in range(int(last_message_to_delete) * 2):
        bot.delete_message(call.message.chat.id, call.message.message_id - i)

    bot.clear_step_handler(call.message)


# ----------------------------------------
# Section for VIEWING TASKS
# ----------------------------------------
@bot.message_handler(commands=['viewtasks'])
def view_tasks(message, today):
    '''lists all saved task for current user'''

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

            # task_id = task["_id"]
            task_name = task['task_name']
            description = task['description']
            status = task['status']
            deadline = task['deadline']
            created_at = task['created_at'].strftime('%Y-%m-%d %H:%M:%S')

            response = (
                f"📌 *{task_name}*\n"
                f"📝 {description}\n"
                f"⏰ {humanize.naturaldate(deadline).capitalize()}\n"
            )

            if status == 'not done':
                response += (f"✖ Not done\n")
                keyboard.add(button_done, button_change, button_delete)
            elif status == 'done':
                response += (f"✅ Done!\n")
                keyboard.add(button_undone, button_change, button_delete)
            else:
                response += (f"❌ Missed\n")
                keyboard.add(button_change, button_delete)

            bot.send_message(chat_id, response, parse_mode="Markdown", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith('mark_as_done'))
def mark_as_done(call):
    '''changes the status of the task, from which the call was made, to "done"'''

    chat_id = call.message.chat.id
    message = call.message
    message_id = message.message_id

    _, deadline_flag = call.data.split('|')
    deadline_flag = int(deadline_flag)  # deadline_flag decides if buttons "edit" and "delete" should be added to keabord

    task_name = ""
    for item in message.text.split()[1:]:
        if item != "📝":
            task_name += item + " "
        else:
            task_name = task_name.rstrip()
            break

    tasks_collection.find_one_and_update({"task_name": task_name}, {'$set': {"status": "done"}},
                                         return_document=ReturnDocument.AFTER)

    button_undone = telebot.types.InlineKeyboardButton(text="Mark as undone",
                                                       callback_data=f'mark_as_undone|{deadline_flag}')

    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(button_undone)

    if not deadline_flag:
        button_change = telebot.types.InlineKeyboardButton(text="Edit",
                                                           callback_data='edit_task')
        button_delete = telebot.types.InlineKeyboardButton(text="Delete",
                                                           callback_data='delete_task')
        keyboard.add(button_change, button_delete)

    text = message.text[:-11]
    bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                          text=text + "\n✅ Done!", parse_mode="Markdown", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith('mark_as_undone'))
def mark_as_undone(call):
    '''changes the status of the task, from which the call was made, to "done"'''

    chat_id = call.message.chat.id
    message = call.message
    message_id = message.message_id

    _, deadline_flag = call.data.split('|')  # Split by the delimiter
    deadline_flag = int(deadline_flag)  # Convert to integer

    task_name = ""
    for item in message.text.split()[1:]:
        if item != "📝":
            task_name += item + " "
        else:
            task_name = task_name.rstrip()
            break

    tasks_collection.find_one_and_update({"task_name": task_name}, {'$set': {"status": "not done"}},
                                         return_document=ReturnDocument.AFTER)

    button_done = telebot.types.InlineKeyboardButton(text="Mark as done",
                                                     callback_data=f'mark_as_done|{deadline_flag}')

    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(button_done)

    if not deadline_flag:
        button_change = telebot.types.InlineKeyboardButton(text="Edit",
                                                           callback_data='edit_task')
        button_delete = telebot.types.InlineKeyboardButton(text="Delete",
                                                           callback_data='delete_task')
        keyboard.add(button_change, button_delete)

    text = message.text[:-8]
    bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                          text=text + "\n✖ Not done", parse_mode="Markdown", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data == 'edit_task')
def edit_task(call):
    '''asks the user, what would they like to change in task: name, description or deadline'''
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
    bot.send_message(chat_id, text=f"What would you like to change for the task __*{task_name}*__?",
                     parse_mode="MarkdownV2", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data == 'edit_name')
def edit_name(call):
    message = call.message
    task_name = message.text[43:-1]
    chat_id = message.chat.id

    bot.send_message(chat_id, text="Enter new name of the task:")
    bot.register_next_step_handler(message, update_task_name, task_name)


def update_task_name(message, task_name):
    new_name = message.text
    tasks_collection.find_one_and_update({"task_name": task_name}, {'$set': {"task_name": new_name}},
                                         return_document=ReturnDocument.AFTER)
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
    tasks_collection.find_one_and_update({"task_name": task_name}, {'$set': {"description": new_desc}},
                                         return_document=ReturnDocument.AFTER)
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
    tasks_collection.find_one_and_update({"task_name": task_name}, {'$set': {"deadline": new_deadline}},
                                         return_document=ReturnDocument.AFTER)
    bot.reply_to(message, f"Task updated: {task_name}")


@bot.callback_query_handler(func=lambda call: call.data == 'delete_task')
def delete_task(call):
    '''asks the user whether they wanna delete the task and then proceeds to the choice'''
    message = call.message
    chat_id = message.chat.id

    task_name = ""
    for item in message.text.split()[1:]:
        if item != "📝":
            task_name += item + " "
        else:
            task_name = task_name.rstrip()
            break

    button_yes = telebot.types.InlineKeyboardButton(text="Yes",
                                                    callback_data=f'confirm_deletion|{call.message.message_id}')
    button_no = telebot.types.InlineKeyboardButton(text="No",
                                                   callback_data=f'cancel_deletion|{call.message.message_id}')
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(button_yes, button_no)

    bot.send_message(chat_id, text=f"Are you sure you want to delete the task __*{task_name}*__?",
                     parse_mode="MarkdownV2", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_deletion'))
def confirm_deletion(call):
    message = call.message
    chat_id = message.chat.id

    task_name = message.text[41:-1]
    _, message_id = call.data.split("|")

    tasks_collection.find_one_and_delete({"task_name": task_name})

    bot.delete_message(chat_id, message_id)
    bot.delete_message(chat_id, message.message_id)
    # bot.send_message(chat_id, f"Task deleted: {task_name}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_deletion'))
def cancel_deletion(call):
    chat_id = call.message.chat.id
    _, message_id = call.data.split("|")

    bot.delete_message(chat_id, call.message.message_id)


# ----------------------------------------
# Section for DEADLINES
# ----------------------------------------
@bot.message_handler(commands=['deadlines'])
def deadlines(message, choose_mode=0):
    '''lists all tasks with status "undone" and the deadline more or equal to today'''

    chat_id = message.chat.id
    tasks = tasks_collection.find({'chat_id': chat_id})

    if tasks_collection.count_documents({'chat_id': chat_id}) == 0:
        bot.send_message(chat_id, "You have no tasks saved.")

    elif tasks_collection.count_documents({'chat_id': chat_id, 'status': 'not done'}) == 0:
        if not choose_mode:
            bot.send_message(message.chat.id, "You've finished all your duties for today! Well done😎",
                             parse_mode="Markdown")
            sticker = stickers[random.randint(0, len(stickers) - 1)]
            bot.send_sticker(message.chat.id, sticker)
        else:
            bot.send_message(message.chat.id, "No undone tasks for now! Well done😎",
                             parse_mode="Markdown")
            sticker = stickers[random.randint(0, len(stickers) - 1)]
            bot.send_sticker(message.chat.id, sticker)

            return 0

    else:
        if not choose_mode:
            bot.send_message(message.chat.id, "⏳ Here are your upcoming deadlines!", parse_mode="Markdown")

        button_done = telebot.types.InlineKeyboardButton(text="Mark as done",
                                                         callback_data=f'mark_as_done|{1}')  # if deadline_flag = 1, buttons "edit" and "delete" won't be shown
        button_undone = telebot.types.InlineKeyboardButton(text="Mark as undone",
                                                           callback_data=f'mark_as_undone|{1}')

        for task in tasks:
            keyboard = telebot.types.InlineKeyboardMarkup()

            task_id = task["_id"]
            print("ID:", task_id)
            task_name = task['task_name']
            description = task['description']
            status = task['status']
            deadline = task['deadline']
            created_at = task['created_at'].strftime('%Y-%m-%d %H:%M:%S')

            now = datetime.datetime.now(pytz.timezone(time_zone))

            if (deadline >= datetime.datetime.today() - datetime.timedelta(hours=now.hour) - datetime.timedelta(
                    minutes=now.minute) - datetime.timedelta(minutes=1) and status == 'not done') or (message.chat.id == "1226646270" and status == "not done"):

                response = (
                    f"📌 *{task_name}*\n"
                    f"📝 {description}\n"
                    f"⏰ {humanize.naturaldate(deadline).capitalize()}\n"
                )
                if not choose_mode:
                    if status == "not done":
                        response += (f"✖ Not done\n")
                        keyboard.add(button_done)
                    elif status == "done":
                        response += (f"✅ Done!\n")
                        keyboard.add(button_undone)
                    else:
                        response += (f"❌ Missed\n")
                else:
                    button_choose = telebot.types.InlineKeyboardButton(text="Choose",
                                                                       callback_data=f'set_notif|{task_id}')
                    keyboard.add(button_choose)

                bot.send_message(chat_id, response, parse_mode="Markdown", reply_markup=keyboard)

        return 1


# ----------------------------------------
# Section for NOTIFICATIONS
# ----------------------------------------
@bot.message_handler(commands=['set_reminder'])
def list_tasks_for_notification(message):
    chat_id = message.chat.id

    tasks = deadlines(message, 1)
    if tasks:
        bot.send_message(chat_id, "Choose the task that needs a notification")


@bot.callback_query_handler(func=lambda call: call.data.startswith('set_notif'))
def get_notification_time(call):
    _, task_id = call.data.split("|")
    chat_id = call.message.chat.id
    bot.send_message(chat_id, "Enter the time in format <code>HH.MM</code>\ne.g. 12.35", parse_mode="HTML")
    bot.register_next_step_handler(call.message, get_notification_day, task_id)


def get_notification_day(message, task_id):
    '''creates calendar for user to choose notification time'''
    global notification_mode
    notification_mode = 1

    global notif_time
    notif_time = message.text

    global notif_task
    notif_task = task_id

    chat_id = message.chat.id
    now = datetime.datetime.now(pytz.timezone(time_zone))
    calendar, step = DetailedTelegramCalendar(current_date=datetime.date(now.year, now.month, now.day),
                                              min_date=datetime.date(now.year, now.month, now.day)).build()

    bot.send_message(chat_id,
                     f"Select {LSTEP[step]}",
                     reply_markup=calendar)

#start_notification_thread()

while True:
    try:
        thread_notifications = threading.Thread(target=start_notification_thread)
        thread_deadlines = threading.Thread(target=check_missed_deadlines)
        thread_deadlines.start()
        thread_notifications.start()
        bot.polling(none_stop=True, interval=0)
    except Exception as e:
        print("Exception occured at time:")
        now = datetime.datetime.now(pytz.timezone(time_zone))
        print(now)
        print("Message:", e)
