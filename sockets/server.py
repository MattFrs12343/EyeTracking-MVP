import asyncio
import json
import websockets

class EventServer:
    def __init__(self, host="127.0.0.1", port=8765, message_callback=None):
        self.host = host
        self.port = port
        self.clients = set()
        self.loop = None
        self.message_callback = message_callback

    async def register(self, websocket):
        self.clients.add(websocket)
        print(f"[EventServer] Nuevo cliente conectado. Total clientes: {len(self.clients)}")
        try:
            async for message in websocket:
                if self.message_callback:
                    self.message_callback(message)
        finally:
            self.clients.remove(websocket)
            print(f"[EventServer] Cliente desconectado. Total clientes: {len(self.clients)}")

    async def broadcast_event(self, event_name, confidence=1.0):
        if not self.clients:
            return

        message = json.dumps({
            "type": "TESTING",
            "event": event_name,
            "confidence": confidence
        })
        
        tasks = [asyncio.create_task(client.send(message)) for client in self.clients]
        await asyncio.gather(*tasks)

    async def broadcast_message(self, data_dict):
        if not self.clients:
            return
            
        message = json.dumps(data_dict)
        tasks = [asyncio.create_task(client.send(message)) for client in self.clients]
        await asyncio.gather(*tasks)

    async def start_server(self):
        print(f"[EventServer] Iniciando servidor WebSocket en ws://{self.host}:{self.port}")
        async with websockets.serve(self.register, self.host, self.port):
            await asyncio.Future()  # run forever

    def run_in_background(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.start_server())
