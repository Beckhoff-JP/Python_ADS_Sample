from model import EventReporter
import asyncio


async def event_listener(reporter: EventReporter):
    last_time = 0
    while True:
        data = await reporter.queue.get()
        print(data)
        time_diff = data['event_datetime'] - last_time
        print(f"Diff : {time_diff} (x100ns)")
        last_time = data['event_datetime']
        await asyncio.sleep(0.001)

if __name__ == '__main__':
    reporter = EventReporter(ams_net_id='127.0.0.1.1.1')
    asyncio.run(event_listener(reporter))