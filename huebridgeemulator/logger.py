"""Module defining HueBridgeEmulator loggers."""

import logging


LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

FORMAT = '%(asctime)-15s - %(levelname)-8s - %(name)s - %(message)s'

logging.basicConfig(format=FORMAT)

# pylint: disable=C0103
main_logger = logging.getLogger('HueBridgeEmulator')
http_logger = main_logger.getChild('http')
registry_logger = main_logger.getChild('registry')
light_logger = main_logger.getChild('light')
light_scan_logger = light_logger.getChild('scan')
sspd_search_logger = main_logger.getChild('sspdSearch')
sspd_broadcast_logger = main_logger.getChild('sspdBroadcast')
scheduler_logger = main_logger.getChild('scheduler')
sync_with_lights_logger = main_logger.getChild('sync_with_lights')
daylight_logger = main_logger.getChild('daylight')
scan_logger = main_logger.getChild('scan_lights')
rule_logger = main_logger.getChild('ruler')
