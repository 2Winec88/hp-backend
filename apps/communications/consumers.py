from channels.generic.websocket import AsyncJsonWebsocketConsumer


class HealthCheckConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send_json({'type': 'connection.ready'})

    async def receive_json(self, content, **kwargs):
        if content.get('type') == 'ping':
            await self.send_json({'type': 'pong'})
