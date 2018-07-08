"""???

.. todo:: Add description and some comments
"""
from datetime import datetime, timedelta
import json
import random
from threading import Thread
import time

from huebridgeemulator.logger import scheduler_logger
from huebridgeemulator.http.client import sendRequest
from huebridgeemulator.tasks.daylight_sensor import daylight_sensor


def scheduler_processor(registry, sensors_state, run_service):
    """???

    .. todo:: Add description and some comments
    """
    scheduler_logger.info("Thread schedulerProcessor starting")
    while run_service:
        for schedule in registry.schedules.keys():
            delay = 0
            if registry.schedules[schedule].status == "enabled":
                if registry.schedules[schedule].localtime[-9:-8] == "A":
                    delay = random.randrange(
                        0,
                        int(registry.schedules[schedule].localtime[-8:-6]) * 3600 +
                        int(registry.schedules[schedule].localtime[-5:-3]) * 60 +
                        int(registry.schedules[schedule].localtime[-2:])
                    )
                    schedule_time = registry.schedules[schedule].localtime[:-9]
                else:
                    schedule_time = registry.schedules[schedule].localtime
                if schedule_time.startswith("W"):
                    pices = schedule_time.split('/T')
                    if int(pices[0][1:]) & (1 << 6 - datetime.today().weekday()):
                        if pices[1] == datetime.now().strftime("%H:%M:%S"):
                            scheduler_logger.info("execute schedule: %s withe delay %s",
                                                  schedule, str(delay))
                            sendRequest(
                                registry.schedules[schedule].command["address"],
                                registry.schedules[schedule].command["method"],
                                json.dumps(registry.schedules[schedule].command["body"]),
                                1,
                                delay)
                elif schedule_time.startswith("PT"):
                    timmer = schedule_time[2:]
                    (hours, minutes, seconds) = timmer.split(':')
                    tdl = timedelta(hours=int(hours), minutes=int(minutes), seconds=int(seconds))
                    custom_date = (datetime.utcnow() - tdl).strftime("%Y-%m-%dT%H:%M:%S")
                    # FIXME: Are we sure that we want to compare ( == ) to a date with seconds ???!
                    if registry.schedules[schedule].starttime == custom_date:
                        scheduler_logger.info("execute timmer: %s withe delay %s",
                                              schedule, str(delay))
                        sendRequest(
                            registry.schedules[schedule].command["address"],
                            registry.schedules[schedule].command["method"],
                            json.dumps(registry.schedules[schedule].command["body"]),
                            1,
                            delay)
                        registry.schedules[schedule].status = "disabled"
                else:
                    if schedule_time == datetime.now().strftime("%Y-%m-%dT%H:%M:%S"):
                        print("execute schedule: " + schedule + " withe delay " + str(delay))
                        sendRequest(
                            registry.schedules[schedule].command["address"],
                            registry.schedules[schedule].command["method"],
                            json.dumps(registry.schedules[schedule].command["body"]),
                            1,
                            delay)
                        if registry.schedules[schedule].autodelete:
                            del registry.schedules[schedule]
        now = datetime.now()
        if now.strftime("%M:%S") == "00:10":
            # auto save configuration every hour
            registry.save()
            Thread(target=daylight_sensor, args=[registry, sensors_state]).start()
            if now.hour == "23" and now.weekday == 6:
                # backup config every Sunday at 23:00:10
                registry.backup()
        time.sleep(1)
