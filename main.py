import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
import json
from typing import Any, Callable
from fastapi import FastAPI, HTTPException, WebSocket, Request, Response, WebSocketDisconnect, Query as QueryParam
from fastapi.responses import HTMLResponse
from fastapi.routing import APIRouter
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


from dbLiveStore import DbLiveStore
from query import Query

templates = Jinja2Templates(directory="frontend/dist")   





@dataclass
class Signal:
    name: str
    value: Any
    clients: list[WebSocket] = field(default_factory=list)


    async def join_client(self, client: WebSocket):
        self.clients.append(client)
        await client.send_text(json.dumps({"type": "signal", "name": self.name, "value": self.value}))

    def leave_client(self, client: WebSocket):
        self.clients.remove(client)

    async def set(self, value: Any|Callable[[Any], Any]):
        self.value = value(self.value) if callable(value) else value
        for client in self.clients:
            await client.send_text(json.dumps({"type": "signal", "name": self.name, "value": self.value}))

async def setInterval(callback: Callable, interval: int, func_is_async: bool = False):
    while True:
        await asyncio.sleep(interval)
        if func_is_async:
            await callback()
        else:
            callback()



app = FastAPI()



app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")


from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/docs2")
async def get_schema():
    return app.openapi()


@app.get("/fuck-deprecated")
async def fuck():
    return "i dont give a fuck"
@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

    

peopleStore = DbLiveStore(store_name="people", initial_data_query=Query("select * from people;", []), update_query=Query("select * from people where last_updated >= ?;", []), toast_on_change=True, popular_field="name")
playerCountSignal = Signal("playerCount", 0)


apiRouter = APIRouter(prefix="/people")
class UpdateNamePayload(BaseModel):
    id: int
    name: str

@apiRouter.put("/name")
async def update_name(payload: UpdateNamePayload):
    await peopleStore.setField(payload.id, "name", payload.name)


class Person(BaseModel):
    id: int
    name: str
    parent: int | None = None
    secret: str | None = None
    last_updated: float | None = None
    

# @apiRouter.get("/", response_model=dict[int, Person])
# async def get_people():
#     return peopleStore.data

@apiRouter.get("/", response_model=Person)
async def get_person(id: int = QueryParam(...)):
    person = peopleStore.get(id)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


app.include_router(apiRouter)

@app.on_event("startup")
async def startup():
    await peopleStore.post_init()
    asyncio.create_task(setInterval(peopleStore.receive_update, 1, True))


@app.get("/")
async def root(request: Request):
    authCookies = request.cookies.get("auth")
    return {"message": "Hello World"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text(json.dumps({"type": "toast", "message": "you are connected to the server"}))
    await peopleStore.join_client(websocket)
    await playerCountSignal.join_client(websocket)
    await playerCountSignal.set(lambda v: v + 1)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except Exception:
        peopleStore.leave_client(websocket)
        playerCountSignal.leave_client(websocket)
        await playerCountSignal.set(lambda v: v - 1)

port = 8080
inDev = False
if inDev:
    from generate_ts_types import place_ts_in_file
    place_ts_in_file(app.openapi(), str(port))
if __name__ == "__main__":
    import uvicorn
    uvicorn.run('main:app', host="0.0.0.0", port=port, reload=True)