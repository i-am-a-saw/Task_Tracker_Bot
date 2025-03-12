import telebot
from telebot import types
import pymongo
import datetime


client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["mydatabase"]

token = ('7505960440:AAF1VsEmvFSAFXE-40rzv7m4wUPX34tc3lI')
bot = telebot.TeleBot(token)

user_data = {}
tasks_collection = db["tasks"]

@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    create_button = types.KeyboardButton("Create task")
    edit_button = types.KeyboardButton("Edit task")
    list_button = types.KeyboardButton("List all")
    deadlines_button = types.KeyboardButton("Deadlines")
    markup.add(create_button, edit_button, list_button, deadlines_button)
    bot.send_message(message.chat.id, "Hello, {0.first_name} ✌️\nLet's begin working together!".format(message.from_user), reply_markup=markup)

@bot.message_handler(commands=['addtask'])
def add_task(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}  # Initialize a dictionary for the user
    bot.send_message(chat_id, "What is the name of the task?")
    bot.register_next_step_handler(message, get_task_name)

def get_task_name(message):
    chat_id = message.chat.id
    user_data[chat_id]['task_name'] = message.text
    bot.send_message(chat_id, "Please describe the task.")
    bot.register_next_step_handler(message, get_task_description)

def get_task_description(message):
    chat_id = message.chat.id
    user_data[chat_id]['description'] = message.text
    bot.send_message(chat_id, "What is the deadline for the task? (Format: YYYY-MM-DD)")
    bot.register_next_step_handler(message, get_task_deadline)

def get_task_deadline(message):
    chat_id = message.chat.id
    try:
        deadline = datetime.datetime.strptime(message.text, '%Y-%m-%d')
        user_data[chat_id]['deadline'] = deadline

        # Save the task to MongoDB
        task = {
            'chat_id': chat_id,
            'task_name': user_data[chat_id]['task_name'],
            'description': user_data[chat_id]['description'],
            'deadline': user_data[chat_id]['deadline'],
            'created_at': datetime.datetime.now()
        }
        tasks_collection.insert_one(task)

        bot.send_message(chat_id, "Task saved successfully!")
    except ValueError:
        bot.send_message(chat_id, "Invalid date format. Please use YYYY-MM-DD.")
    finally:
        user_data.pop(chat_id, None)  # Clear user data

@bot.message_handler(commands=['viewtasks'])
def view_tasks(message):
    chat_id = message.chat.id
    tasks = tasks_collection.find({'chat_id': chat_id})

    if tasks_collection.count_documents({'chat_id': chat_id}) == 0:
        bot.send_message(chat_id, "You have no tasks saved.")
    else:
        response = "Your tasks:\n\n"
        for task in tasks:
            task_name = task['task_name']
            description = task['description']
            deadline = task['deadline'].strftime('%Y-%m-%d')
            created_at = task['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            response += (
                f"📌 *Task Name*: {task_name}\n"
                f"📝 *Description*: {description}\n"
                f"⏰ *Deadline*: {deadline}\n"
                f"🕒 *Created At*: {created_at}\n\n"
            )
        bot.send_message(chat_id, response, parse_mode="Markdown")

bot.polling(none_stop=True, interval=0)