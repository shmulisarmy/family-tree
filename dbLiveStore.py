import asyncio
from dataclasses import dataclass, field
import json
import time
from datetime import datetime
from typing import Callable, Optional

from fastapi import WebSocket


from db import get_cursor_and_connection
from query import Query


def row_factory(cursor, row):
    return dict(zip([column[0] for column in cursor.description], row))



@dataclass
class DbLiveStore:
    # def __init__(self, store_name: str, initial_data_query: Query, update_query: Query):
    initial_data_query: Query
    update_query: Query
    data: dict[int, dict] = field(default_factory=dict)
    clients: list[WebSocket] = field(default_factory=list)
    updateInterval: int = 1
    last_update_check: float = 0
    store_name: str = ""
    setField_event: Optional[Callable] = None
    toast_on_change: bool = False
    popular_field: Optional[str] = "id"


    def leave_client(self, client):
        self.clients.remove(client)

    def assert_task(self, task):
        cur, conn = get_cursor_and_connection()
        #Todo make an assert for making sure update query has a way of checking last updated and each db row has a last_updated column
        print("the db schema and update query must have a last_updated column")
        cur.execute(self.update_query.string, (self.last_update_check,))

    async def post_init(self):
        print("__post_init__")
        cursor, conn = get_cursor_and_connection()
        cursor.execute(self.initial_data_query.string, self.initial_data_query.args)
        tasks = cursor.fetchall()
        self.last_update_check = time.time()

        for row in tasks:
            task = row_factory(cursor, row)
            print(f'{task = }')
            del task["last_updated"]

            asyncio.create_task(self.set(task["id"], task))

    async def receive_update(self):
        #Todo schedule this to run on updateInterval
        cursor, conn = get_cursor_and_connection()
        print(f'{self.last_update_check = }')
        cursor.execute(self.update_query.string, (self.last_update_check,))
        tasks = cursor.fetchall()
        self.last_update_check = int(time.time())
        for row in tasks:
            task = row_factory(cursor, row)
            print(f'{task = }')
            del task["last_updated"]

            await self.set(task["id"], task)


    async def join_client(self, client):
        self.clients.append(client)
        await client.send_text(json.dumps({"type": "store-join", "store": self.store_name, "data": self.data}))

    async def setField(self, key, field, value):
        # in case it gets changed while we are processing
        popular_field_value = self.data[key][self.popular_field]
        task = self.data[key]
        task[field] = value
        if self.toast_on_change:
            for client in self.clients:
                await client.send_text(json.dumps({"type": "toast", "message": f"{popular_field_value}'s {field} got updated to {value}"}))
        await self.set(key, task)

    async def set(self, key, task):
        self.data[key] = task
        for client in self.clients:
            await client.send_text(json.dumps({"type": "store-setValue", "store": self.store_name, "key": key, "data": task}))

    def get(self, key):
        return self.data.get(key)