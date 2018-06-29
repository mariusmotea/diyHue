import logging

LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

FORMAT = '%(asctime)-15s - %(levelname)-8s - %(name)s - %(message)s'
logging.basicConfig(format=FORMAT)

main_logger = logging.getLogger('HueBridgeEmulator')
http_logger = main_logger.getChild('http')
light_logger = main_logger.getChild('light')
sspd_search_logger = main_logger.getChild('sspdSearch')
sspd_broadcast_logger = main_logger.getChild('sspdBroadcast')

