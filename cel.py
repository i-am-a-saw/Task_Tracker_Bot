from celery import Celery
from main import bot

app = Celery(
    'tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

@app.task
def send_notification_(chat_id, task_name):
    bot.send_message(chat_id, f"Don't forget to complete your duties for today: \"{task_name}\" is waiting!")