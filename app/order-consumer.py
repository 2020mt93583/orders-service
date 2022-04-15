import os
import time

from main import Order
from redis_om import get_redis_connection

key = 'refund_order'
group = 'payment-group'

eventq = get_redis_connection(
    host=os.environ['eventq-host-name'],
    port=6379,
    password=os.environ['eventq-pass'],
    decode_responses=True
)

try:
    eventq.xgroup_create(key, group)
except:
    print('Group already exists!')

while True:
    try:
        results = eventq.xreadgroup(group, key, {key: '>'}, None)

        if results:
            print(results)
            for result in results:
                obj = result[1][0][1]
                order = Order.get(obj['pk'])
                order.status = 'refunded'
                order.save()

    except Exception as e:
        print(str(e))
    time.sleep(1)
