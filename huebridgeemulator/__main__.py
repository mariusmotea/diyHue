"""HueBridgeEmulator entrypoint."""
from threading import Thread
from time import sleep
import argparse

from huebridgeemulator.tools.deconz import scanDeconz
from huebridgeemulator.registry import registry
from huebridgeemulator.tasks.ssdp import ssdp_search, ssdp_broadcast
from huebridgeemulator.tasks.scheduler import scheduler_processor
from huebridgeemulator.tasks.light import sync_with_lights
from huebridgeemulator.web.server import start
from huebridgeemulator.tools.light import update_all_lights
from huebridgeemulator.logger import main_logger, LOG_LEVELS


def main():
    """Main and entrypoitn function."""
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config-file',
                        required=True, help='Config file')
    parser.add_argument('-l', '--log-level', choices=LOG_LEVELS,
                        default="WARNING", help='Log Level')
    args = parser.parse_args()
    # Set log level
    main_logger.setLevel(args.log_level)

    # Setings some variables ??!!
    sensors_state = {}
    # if set to true all lights will be updated with last know state on startup.
    update_lights_on_startup = False

    # Load config
    registry.set_filepath(args.config_file)

    if registry.deconz["enabled"]:
        scanDeconz(registry)
    registry.save()
    try:
        run_service = True
        # scheduler_processor(registry, sensors_state, run_service)
        if update_lights_on_startup:
            update_all_lights(registry)
        Thread(target=ssdp_search).start()
        Thread(target=ssdp_broadcast).start()
        Thread(target=scheduler_processor, args=[registry, sensors_state, run_service]).start()
        Thread(target=sync_with_lights, args=[registry]).start()
        # Thread(target=run, args=[False, registry, sensors_state]).start()
        # Thread(target=run, args=[True, registry, sensors_state]).start()
        Thread(target=start, args=[registry, sensors_state]).start()
        main_logger.info("Main loop starting")
        while True:
            main_logger.debug("Main loop run")
            sleep(10)
    # Improve this try/accept
    # and add thread stop handler
    except Exception as exp:  # pylint: disable=W0703
        print("server stopped " + str(exp))
    finally:
        run_service = False
        registry.save()
        print('config saved')


if __name__ == "__main__":
    main()
