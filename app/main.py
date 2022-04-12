import requests
import time
from fastapi import FastAPI
from fastapi.background import BackgroundTasks
from redis_om import get_redis_connection, HashModel
from starlette.requests import Request

app = FastAPI()

redis = get_redis_connection(
    host="localhost",
    port=6379,
    password="eYVX7EwVmmxKPCDmwMtyKVge8oLd2t81",
    decode_responses=True
)


class Order(HashModel):
    product_id: str
    user_id: str
    billing_address: str
    price: float
    fee: float
    total: float
    quantity: int
    status: str  # pending, completed, refunded

    class Meta:
        database = redis


@app.get('/orders/{pk}')
def get(pk: str):
    return Order.get(pk)


@app.post('/orders')
async def create(request: Request, background_tasks: BackgroundTasks):  # id, quantity
    body = await request.json()

    req = requests.get('http://localhost:8000/products/%s' % body['id'])
    product = req.json()

    user_req = requests.get('http://localhost:8002/users/%s' % body['userId'])
    user = user_req.json()

    order = Order(
        product_id=body['id'],
        user_id=body['userId'],
        billing_address=user['address'],
        price=product['price'],
        fee=0.2 * product['price'],
        total=1.2 * product['price'],
        quantity=body['quantity'],
        status='pending'
    )
    order.save()

    background_tasks.add_task(complete_order, order)

    return order


def complete_order(order: Order):
    time.sleep(5)
    order.status = 'completed'
    order.save()
    redis.xadd('order_completed', order.dict(), '*')
