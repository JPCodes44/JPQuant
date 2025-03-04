"""
RBI how to automate your trading 

R - research - google scholar, GPT 03 (idea what to look up on google scholar),  

"""

import json  # imports the json module
import time  # imports the time module
from datetime import datetime, timedelta  # imports the datetime and timedelta modules
from termcolor import cprint  # imports the cprint module
import random  # imports the random module


def load_tasks():  # defines the load_tasks function
    with open(
        "/Users/jpmak/Desktop/dev/productivity_app/tasks.json",
        "r",  # opens the json file
    ) as f:  # opens the json file
        tasks = json.load(f)  # loads the json file
    return tasks  # returns the tasks


def get_tasks_schedule(tasks):
    task_start_time = datetime.now()  # gets the current time
    schedule = []  # creates an empty list
    for task, minutes in tasks.items():  # loops through the tasks and minutes
        end_time = task_start_time + timedelta(  # adds the end time to the current time
            minutes=minutes  # adds the minutes to the current time
        )  # adds the minutes to the current time
        schedule.append(
            (task, task_start_time, end_time)
        )  # appends the task, start time, and end time to the schedule
        task_start_time = end_time  # sets the task start time to the end time
    return schedule  # returns the schedule


def main():
    tasks = load_tasks()  # loads the tasks
    schedule = get_tasks_schedule(tasks)  # gets the tasks schedule
    current_index = 0  # sets the current index to 0
    while True:  # loops forever
        now = datetime.now()  # gets the current time
        current_task, start_time, end_time = schedule[
            current_index
        ]  # gets the current task, start time, and end time
        remaining_time = end_time - now  # gets the remaining time
        remaining_minutes = int(
            remaining_time.total_seconds() // 60
        )  # gets the remaining minutes as an integer

        for index, (task, s_time, e_time) in enumerate(
            schedule
        ):  # loops through the schedule and gets the index, task, start time, and end time
            if index < current_index:
                # task is completed
                print(f'{task} done: {e_time.strftime("%H:%M")}')
            elif index == current_index:
                if remaining_minutes < 2:
                    cprint("{task} < 2m left", "white", "on_red", attrs={"blink"})
                elif remaining_minutes < 5:
                    cprint(f"{task} - {remaining_minutes} mins", "white", "on_red")
                else:
                    cprint(f"{task} - {remaining_minutes} mins", "white", "on_blue")
            else:
                print(f'{task} @ {s_time.strftime("%H:%M")}')

        list_of_reminders = [
            "i have a 1000 percent algo",
            "time is irrelevant, keep swimin",
            "every day i get better",
            "rest at the end",
            "jobs not finished",
            "deal was already made",
            "best algo trader in the world",
        ]

        random_reminder = random.choice(list_of_reminders)
        print("✨" + random_reminder)

        if now >= end_time:
            current_index += 1
            if current_index >= len(schedule):
                cprint("all tasks are completed", "white", "on_green")
                break

        time.sleep(15)


main()
