import requests
import time
import os

from fastapi import FastAPI
from fastapi.background import BackgroundTasks
from redis_om import get_redis_connection, HashModel
from starlette.requests import Request

app = FastAPI()

redis = get_redis_connection(
    host=os.environ['orders-db-name'],
    port=6379,
    password=os.environ['orders-db-pass'],
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


INVENTORY_SERVICE_URL = 'http://' + os.environ['inventory-service-url']
USERS_SERVICE_URL = 'http://' + os.environ['users-service-url']


@app.post('/orders')
async def create(request: Request, background_tasks: BackgroundTasks):  # id, quantity
    body = await request.json()

    req = requests.get(INVENTORY_SERVICE_URL + '/products/%s' % body['productId'])
    product = req.json()

    user_req = requests.get(USERS_SERVICE_URL + '/users/%s' % body['userId'])
    user = user_req.json()

    order = Order(
        product_id=body['productId'],
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
    time.sleep(10)
    order.status = 'completed'
    order.save()
    redis.xadd('order_completed', order.dict(), '*')
