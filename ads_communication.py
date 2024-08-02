import pyads
from ctypes import Structure, sizeof, c_ubyte
from dataclasses import dataclass, field
from typing import List, Callable
import platform

@dataclass
class EventNotificator:
    connection: pyads.Connection
    model: tuple
    subscriber: Callable
    symbol: str

    def __post_init__(self):
        size_of_struct = pyads.size_of_structure(self.model)
        attr = pyads.NotificationAttrib(size_of_struct)
        attr.trans_mode = pyads.ADSTRANS_SERVERONCHA
        attr.max_delay = 2500
        attr.cycle_time = 2500
        @self.connection.notification(c_ubyte * size_of_struct)
        def callback(handle, name, timestamp, value):
            self.subscriber(value)

        try:
            print(attr)
            self.connection.add_device_notification(self.symbol,
                                        attr,
                                        callback)
        except pyads.pyads_ex.ADSError:
            print(f"Symbol not found: {self.symbol}")

class RouterConfiguration:
    target_host: str = '192.168.1.10'
    target_pc_name: str = ''
    local_ams_id: str = '127.0.0.1.1.1'
    route_name: str = 'training-ngy8'
    login_user: str = 'Administrator'
    login_password: str = '1'


@dataclass
class AdsCommunication:
    ams_net_id: str = field(default='127.0.0.1.1.1')
    ams_port: int = field(default=851, init=True)
    event_notificators: List[EventNotificator] = field(default_factory=list, init=False)
    connection: pyads.Connection = field(default=None, init=False)
    symbols :List[pyads.symbol.AdsSymbol] = field(default_factory=list, init=False)

    def __post_init__(self):
        self.add_route()
        self.connection = pyads.Connection(self.ams_net_id, self.ams_port)
        self.connection.open()
        #self.symbols = self.connection.get_all_symbols()
        for symbol in self.symbols:
            print(symbol.name)

    def add_route(self):
        if platform.system() != 'Linux':
            return
        pyads.open_port()
        pyads.set_local_address(RouterConfiguration.local_ams_id)
        pyads.add_route_to_plc(RouterConfiguration.local_ams_id,
                               RouterConfiguration.target_pc_name,
                               RouterConfiguration.target_host,
                               RouterConfiguration.login_user,
                               RouterConfiguration.login_password,
                               route_name=RouterConfiguration.route_name)
        pyads.close_port()


    def reg_notification(self,symbol: str, model: tuple, subscriber: Callable):
        self.event_notificators.append(
            EventNotificator(
                connection=self.connection,
                model=model,
                subscriber=subscriber,
                symbol=symbol
            )
        )

    def write(self,symbol: str, value, type):
        self.connection.write_by_name(symbol, value, type)

