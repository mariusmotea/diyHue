from huebridgeemulator.common import BaseObject

class AlarmConfig(BaseObject):

    _RESOURCE_TYPE = "alarm_config"
    _MANDATORY_ATTRS = ('mail_from', 'mail_password', 'mail_recipients',
                        'mail_subject', 'mail_username', 'smtp_port', 'smtp_server')
