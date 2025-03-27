## Task Tracker Bot

This is a Telegram bot aimed to help you manage your duties effectively and comfortably! \n
It is created with **telebot** library, using datetime, threading, and MongoDB as a database.\n
You can test it via this [link](https://web.telegram.org/k/#@TTTaskTTTracker_bot) and write me in [Telegram](https://t.me/asfedoriako) if you have any suggestions or ideas!

## Creating tasks

You can create a task and set 4 parameters for it:
<ul>
  <li>Name</li>
  <li>Description</li>
  <li>Deadline</li>
  <li>Status (it is automatically set to *Undone*)</li>
</ul>

## Viewing tasks

If you want to see all the tasks you have saved, the button **List all** serves for it. It lists all tasks, no matter if they are done or not, in a sequence of messages

## Deadlines

This tab shows only those tasks which have *Undone* status, and which have a deadline no earlier then current time. It serves for listing actual tasks that need to be done.

## Notifications 

It this section you choose a task for which you want to set a notification, then you type the time and select the day. The message will be sent to you at specified time.

## Usage

You can access the bot [here](https://web.telegram.org/k/#@TTTaskTTTracker_bot) and enjoy it yourself!
