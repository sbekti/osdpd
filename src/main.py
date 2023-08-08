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

pd_list = [
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
    @classmethod
    async def create(cls, pd_list):
        self = OSDPd()
        self.pd_list = pd_list

        cp = osdp.ControlPanel(pd_list)
        cp.set_loglevel(osdp.LOG_DEBUG)
        cp.set_event_callback(self.handle_event)
        self.cp = cp

        self.loop = asyncio.get_running_loop()
        self.pd_status = 0

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
        await asyncio.sleep(9.2)  # Simulate slow network call

        data = event["data"]
        length = event["length"]
        hex_str = f"{(int.from_bytes(data) >> len(data) * 8 - length):x}"
        logging.info(f"hex_str: {hex_str}, length: {length}")

        if hex_str == "12345":
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

            pd_status = self.cp.status() & self.cp.sc_status()
            pd_status_diff = pd_status ^ self.pd_status

            for pd_index in range(len(self.pd_list)):
                toggled = pd_status_diff & (1 << pd_index)
                ready = pd_status & (1 << pd_index)
                if toggled:
                    await self.handle_pd_state_change(pd_index, ready)

            self.pd_status = pd_status

            await asyncio.sleep(0.020)

    async def handle_pd_state_change(self, pd_index, ready):
        logging.info(f"PD {pd_index} state changed to: {ready}")
        if ready:
            await asyncio.to_thread(utils.send_idle_feedback, self.cp, pd_index)


async def main():
    logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.DEBUG)
    await OSDPd.create(pd_list)


if __name__ == "__main__":
    asyncio.run(main())
