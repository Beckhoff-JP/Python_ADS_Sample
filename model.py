from ctypes import *
import pyads
import asyncio
from dataclasses import dataclass, field
from ads_communication import AdsCommunication
from pprint import pprint
from collections import OrderedDict


structure_def = (
        ("title", pyads.PLCTYPE_STRING, 1),
        ("name", pyads.PLCTYPE_STRING, 1),
        ("age", pyads.PLCTYPE_UINT, 1),
        ("sex", pyads.PLCTYPE_UINT, 1),
        ("mail_address", pyads.PLCTYPE_STRING, 1),
        ("event_datetime", pyads.PLCTYPE_ULINT, 1),
        ("description", pyads.PLCTYPE_STRING, 1)
)

@dataclass
class EventReporter:
    ams_net_id : str = field(default='127.0.0.1.1.1', init=True)
    ads_port : int = field(default=851, init=True)
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    last_data : OrderedDict = field(default=None)

    def __post_init__(self):
        self.plc: AdsCommunication = AdsCommunication(
            ams_net_id=self.ams_net_id,
            ams_port=self.ads_port
        )
        # 監視したい変数とデータ構造を定義したtupleを登録
        self.plc.reg_notification('MAIN.ads_watch_variable', structure_def,  self.job_event_handler)

    def job_event_handler(self, value):
        data = pyads.dict_from_bytes(value, structure_def)
        self.queue.put_nowait(data)

