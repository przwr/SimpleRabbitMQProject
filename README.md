SimpleRabbitMQProject
=====================


Requirements
--------------


> - virtualenv
> - rabbitmq-server


Instalation
-----------


> ./install.sh


Usage
-----


# In case rabbitmq is not running:
sudo service rabbitmq-server start

# To run API (A server):
> ./api.py

# To run DB (C server):
> ./db.py


# GET value for a :
first request value for key:
> curl -i http://localhost:5000/api/v1.0/values/a
then to get value go to:
> curl -i http://localhost:5000/api/v1.0/value/a

# POST value for a key:
> curl --data "key=a&value=10" -i http://localhost:5000/api/v1.0/value
