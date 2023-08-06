from enum import Enum
import osdp


class LEDPattern(Enum):
    IDLE = 1
    PENDING_ACCESS = 2
    ALLOW_ACCESS = 3
    DENY_ACCESS = 4
    TAMPER_ALERT = 5


class BuzzerPattern(Enum):
    IDLE = 1
    ALLOW_ACCESS = 2
    DENY_ACCESS = 3
    TAMPER_ALERT = 4


def send_pending_access_feedback(cp, address):
    cp.send_command(address, _gen_led_command(LEDPattern.PENDING_ACCESS))


def send_allow_access_feedback(cp, address):
    cp.send_command(address, _gen_led_command(LEDPattern.ALLOW_ACCESS))
    cp.send_command(address, _gen_buzzer_command(BuzzerPattern.ALLOW_ACCESS))


def send_deny_access_feedback(cp, address):
    cp.send_command(address, _gen_led_command(LEDPattern.DENY_ACCESS))
    cp.send_command(address, _gen_buzzer_command(BuzzerPattern.DENY_ACCESS))


def send_tamper_alert_feedback(cp, address):
    cp.send_command(address, _gen_led_command(LEDPattern.TAMPER_ALERT))
    cp.send_command(address, _gen_buzzer_command(BuzzerPattern.TAMPER_ALERT))


def send_idle_feedback(cp, address):
    cp.send_command(address, _gen_led_command(LEDPattern.IDLE))
    cp.send_command(address, _gen_buzzer_command(BuzzerPattern.IDLE))


def _gen_led_command(pattern: LEDPattern, reader_number: int = 0, led_number: int = 0):
    command = {
        "command": osdp.CMD_LED,
        "reader": reader_number,
        "led_number": led_number,
    }

    if pattern == LEDPattern.IDLE:
        command.update(
            {
                "control_code": 1,  # permanent
                "on_count": 2,
                "off_count": 0,
                "on_color": osdp.LED_COLOR_BLUE,
                "off_color": osdp.LED_COLOR_NONE,
                "timer_count": 1,
                "permanent": True,
            }
        )
    elif pattern == LEDPattern.PENDING_ACCESS:
        command.update(
            {
                "control_code": 2,  # temporary
                "on_count": 6,
                "off_count": 6,
                "on_color": 5,  # Purple
                "off_color": osdp.LED_COLOR_NONE,
                "timer_count": 1000,
                "temporary": True,
            }
        )
    elif pattern == LEDPattern.ALLOW_ACCESS:
        command.update(
            {
                "control_code": 2,  # temporary
                "on_count": 3,
                "off_count": 3,
                "on_color": osdp.LED_COLOR_GREEN,
                "off_color": osdp.LED_COLOR_GREEN,
                "timer_count": 6,
                "temporary": True,
            }
        )
    elif pattern == LEDPattern.DENY_ACCESS:
        command.update(
            {
                "control_code": 2,  # temporary
                "on_count": 1,
                "off_count": 1,
                "on_color": osdp.LED_COLOR_RED,
                "off_color": osdp.LED_COLOR_NONE,
                "timer_count": 9,
                "temporary": True,
            }
        )
    elif pattern == LEDPattern.TAMPER_ALERT:
        command.update(
            {
                "control_code": 1,  # permanent
                "on_count": 2,
                "off_count": 0,
                "on_color": osdp.LED_COLOR_RED,
                "off_color": osdp.LED_COLOR_NONE,
                "timer_count": 1,
                "permanent": True,
            }
        )

    return command


def _gen_buzzer_command(
    pattern: BuzzerPattern,
    reader_number: int = 0,
):
    command = {
        "command": osdp.CMD_BUZZER,
        "reader": reader_number,
    }

    if pattern == BuzzerPattern.IDLE:
        command.update(
            {
                "on_count": 0,
                "off_count": 0,
                "rep_count": 0,  # forever
                "control_code": 1,  # off
            }
        )
    elif pattern == BuzzerPattern.ALLOW_ACCESS:
        command.update(
            {
                "on_count": 3,
                "off_count": 1,
                "rep_count": 1,
                "control_code": 2,  # default tone
            }
        )
    elif pattern == BuzzerPattern.DENY_ACCESS:
        command.update(
            {
                "on_count": 1,
                "off_count": 1,
                "rep_count": 3,
                "control_code": 2,  # default tone
            }
        )
    elif pattern == BuzzerPattern.TAMPER_ALERT:
        command.update(
            {
                "on_count": 1,
                "off_count": 1,
                "rep_count": 0,  # forever
                "control_code": 2,  # default tone
            }
        )

    return command
