#!/usr/bin/env python3
import asyncio
import logging
import osdp

from utils import (
    LEDPattern,
    BuzzerPattern,
    gen_led_command,
    gen_buzzer_command,
)


# fmt: off
key_custom = bytes([
    0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
    0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F,
])
# fmt: on

pd_info = [
    # PD_0 info
    {
        "address": 0,
        "flags": osdp.FLAG_ENFORCE_SECURE,
        "scbk": key_custom,
        "channel_type": "uart",
        "channel_speed": 9600,
        "channel_device": "/dev/ttyUSB0",
    }
]

PD_0 = 0


async def handle_pd_state_change(cp, ready):
    logging.info(f"PD state changed to: {ready}")
    if ready:
        cp.send_command(PD_0, gen_led_command(LEDPattern.IDLE))
        cp.send_command(PD_0, gen_buzzer_command(BuzzerPattern.IDLE))


async def cp_refresh(cp):
    connected = False
    secured = False
    ready = False

    while True:
        cp.refresh()

        if connected != cp.status():
            connected = cp.status()
        if secured != cp.sc_status():
            secured = cp.sc_status()
        if ready != (connected and secured):
            ready = connected and secured
            await handle_pd_state_change(cp, ready)

        await asyncio.sleep(0.020)


async def process_card_read_event(cp, address, event):
    cp.send_command(address, gen_led_command(LEDPattern.PENDING_ACCESS))
    await asyncio.sleep(10)  # Simulate slow network call

    if event["data"] == b"\x12345":
        cp.send_command(address, gen_led_command(LEDPattern.ALLOW_ACCESS))
        cp.send_command(address, gen_buzzer_command(BuzzerPattern.ALLOW_ACCESS))
    else:
        cp.send_command(address, gen_led_command(LEDPattern.DENY_ACCESS))
        cp.send_command(address, gen_buzzer_command(BuzzerPattern.DENY_ACCESS))


async def process_status_event(cp, address, event):
    if event["tamper"] == 1:
        cp.send_command(address, gen_led_command(LEDPattern.TAMPER_ALERT))
        cp.send_command(address, gen_buzzer_command(BuzzerPattern.TAMPER_ALERT))
    elif event["tamper"] == 0:
        cp.send_command(address, gen_led_command(LEDPattern.IDLE))
        cp.send_command(address, gen_buzzer_command(BuzzerPattern.IDLE))


async def dispatch_event(cp, address, event):
    logging.debug(f"Address: {address} Event: {event}")

    if event["event"] == osdp.EVENT_CARDREAD:
        await process_card_read_event(cp, address, event)
    elif event["event"] == osdp.EVENT_STATUS:
        await process_status_event(cp, address, event)


async def main():
    logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.DEBUG)

    cp = osdp.ControlPanel(pd_info)

    logging.info(f"pyosdp Version: {cp.get_version()} Info: {cp.get_source_info()}")
    cp.set_loglevel(osdp.LOG_DEBUG)

    def handle_event(address, event):
        loop = asyncio.get_running_loop()
        loop.create_task(dispatch_event(cp, address, event))

    cp.set_event_callback(handle_event)

    tasks = [
        asyncio.create_task(cp_refresh(cp)),
    ]
    await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())
