#!/usr/bin/env python3
import asyncio
import logging
import osdp

import utils


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


class OSDPd:
    PD_0 = 0

    @classmethod
    async def create(cls, pd_info):
        self = OSDPd()

        cp = osdp.ControlPanel(pd_info)
        cp.set_loglevel(osdp.LOG_DEBUG)
        cp.set_event_callback(self.handle_event)
        self.cp = cp

        self.loop = asyncio.get_running_loop()

        self.connected = False
        self.secured = False
        self.ready = False

        await self.refresh()

    def handle_event(self, address, event):
        coro = self.dispatch_event(address, event)
        asyncio.run_coroutine_threadsafe(coro, self.loop)

    async def dispatch_event(self, address, event):
        logging.debug(f"Address: {address} Event: {event}")

        if event["event"] == osdp.EVENT_CARDREAD:
            await self.process_card_read_event(address, event)
        elif event["event"] == osdp.EVENT_STATUS:
            await self.process_status_event(address, event)

    async def process_card_read_event(self, address, event):
        await asyncio.to_thread(utils.send_pending_access_feedback, self.cp, address)
        await asyncio.sleep(10)  # Simulate slow network call

        if event["data"] == b"\x12345":
            await asyncio.to_thread(utils.send_allow_access_feedback, self.cp, address)
        else:
            await asyncio.to_thread(utils.send_deny_access_feedback, self.cp, address)

    async def process_status_event(self, address, event):
        if event["tamper"] == 1:
            await asyncio.to_thread(utils.send_tamper_alert_feedback, self.cp, address)
        elif event["tamper"] == 0:
            await asyncio.to_thread(utils.send_idle_feedback, self.cp, address)

    async def refresh(self):
        while True:
            self.cp.refresh()

            if self.connected != self.cp.status():
                self.connected = self.cp.status()
            if self.secured != self.cp.sc_status():
                self.secured = self.cp.sc_status()
            if self.ready != (self.connected and self.secured):
                self.ready = self.connected and self.secured
                await self.handle_pd_state_change()

            await asyncio.sleep(0.020)

    async def handle_pd_state_change(self):
        logging.info(f"PD state changed to: {self.ready}")
        if self.ready:
            await asyncio.to_thread(utils.send_idle_feedback, self.cp, OSDPd.PD_0)


async def main():
    logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.DEBUG)
    await OSDPd.create(pd_info)


if __name__ == "__main__":
    asyncio.run(main())
