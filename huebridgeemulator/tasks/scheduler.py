"""???

.. todo:: Add description and some comments
"""
from datetime import datetime, timedelta
import time
import random
import json

from huebridgeemulator.logger import scheduler_logger
from huebridgeemulator.http.client import sendRequest


def scheduler_processor(conf_obj, run_service):
    """???

    .. todo:: Add description and some comments
    """
    bridge_config = conf_obj.bridge
    scheduler_logger.info("Thread schedulerProcessor starting")
    while run_service:
        for schedule in bridge_config["schedules"].keys():
            delay = 0
            if bridge_config["schedules"][schedule]["status"] == "enabled":
                if bridge_config["schedules"][schedule]["localtime"][-9:-8] == "A":
                    delay = random.randrange(
                        0,
                        int(bridge_config["schedules"][schedule]["localtime"][-8:-6]) * 3600 +
                        int(bridge_config["schedules"][schedule]["localtime"][-5:-3]) * 60 +
                        int(bridge_config["schedules"][schedule]["localtime"][-2:])
                    )
                    schedule_time = bridge_config["schedules"][schedule]["localtime"][:-9]
                else:
                    schedule_time = bridge_config["schedules"][schedule]["localtime"]
                if schedule_time.startswith("W"):
                    pices = schedule_time.split('/T')
                    if int(pices[0][1:]) & (1 << 6 - datetime.today().weekday()):
                        if pices[1] == datetime.now().strftime("%H:%M:%S"):
                            scheduler_logger.info("execute schedule: %s withe delay %s",
                                                  schedule, str(delay))
                            sendRequest(
                                bridge_config["schedules"][schedule]["command"]["address"],
                                bridge_config["schedules"][schedule]["command"]["method"],
                                json.dumps(bridge_config["schedules"][schedule]["command"]["body"]),
                                1,
                                delay)
                elif schedule_time.startswith("PT"):
                    timmer = schedule_time[2:]
                    (hours, minutes, seconds) = timmer.split(':')
                    tdl = timedelta(hours=int(hours), minutes=int(minutes), seconds=int(seconds))
                    custom_date = (datetime.utcnow() - tdl).strftime("%Y-%m-%dT%H:%M:%S")
                    # FIXME: Are we sure that we want to compare ( == ) to a date with seconds ???!
                    if bridge_config["schedules"][schedule]["starttime"] == custom_date:
                        scheduler_logger.info("execute timmer: %s withe delay %s",
                                              schedule, str(delay))
                        sendRequest(
                            bridge_config["schedules"][schedule]["command"]["address"],
                            bridge_config["schedules"][schedule]["command"]["method"],
                            json.dumps(bridge_config["schedules"][schedule]["command"]["body"]),
                            1,
                            delay)
                        bridge_config["schedules"][schedule]["status"] = "disabled"
                else:
                    if schedule_time == datetime.now().strftime("%Y-%m-%dT%H:%M:%S"):
                        print("execute schedule: " + schedule + " withe delay " + str(delay))
                        sendRequest(
                            bridge_config["schedules"][schedule]["command"]["address"],
                            bridge_config["schedules"][schedule]["command"]["method"],
                            json.dumps(bridge_config["schedules"][schedule]["command"]["body"]),
                            1,
                            delay)
                        if bridge_config["schedules"][schedule]["autodelete"]:
                            del bridge_config["schedules"][schedule]
        now = datetime.now()
        if now.strftime("%M:%S") == "00:10":
            # auto save configuration every hour
            conf_obj.save()
            if now.hour == "23" and now.weekday == 6:
                # backup config every Sunday at 23:00:10
                conf_obj.backup()
        time.sleep(1)
