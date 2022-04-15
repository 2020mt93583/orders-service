#orders-service

##build docker image
>docker build . -t orders-service:latest

##run docker image in a container
>docker run -itd --network redis_default -p 8001:8000 --name orders-service-container -e orders-db-name=orders-db -e orders-db-pass=ordersDbPass -e eventq-host-name=eventq -e eventq-pass=eventqPass -e inventory-service-url=inventory-service-container -e users-service-url=users-service-container orders-service:latest