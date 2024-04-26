# Newyork restaurants - WIP...

[Fastapi](https://fastapi.tiangolo.com/) (python) app linked to [Atlas-Mongodb database](https://www.mongodb.com/).

The purpose of this app is to provide quick and simple api to support any front-end project related to.

## Fastapi

Over the fast, intuitive and easy to code framework it provides, fastapi is totally standard-based giving access to wonderfull [OpenAPI (Swagger)](https://github.com/OAI/OpenAPI-Specification) and [JSON Schema](https://json-schema.org/).

### Setup project

Use any package manager (pip, conda, ...) [to install fastapi, uvicorn](https://fastapi.tiangolo.com/tutorial/#install-fastapi) and required librairies:

```bash
pip install "fastapi[all]"
pip install -r requirements.txt
```

### Run project

Navigate to the directory where your main.py file is located and run:

```bash
uvicorn main:app --reload
```

**--reload** option is a watch mode that reloads app at each change in the source code.

Once served:

* the app shall be available at: <http://localhost:8000/>
* OpenApi documentation is served at: <http://localhost:8000/docs>
* Redoc documentation is served at: <http://localhost:8000/redoc>

**OpenApi illustration**
![swagger](./assets/swagger.png)

## Security

Don't expose your private credentials online, use [dotenv](https://pypi.org/project/python-dotenv/) to use environment variables for your secrets.

.env file (at root level) is added to .gitignore, so you will have to define your own .env file with the credentials required for mongodb connexion.

```env
MONGO_URI=mongodb+srv://<user>:<password>@<mongo_cluster>
```

## Mongodb

You can connect your Atlas cluster with [Pymongo](https://www.mongodb.com/docs/drivers/pymongo/) library.

This way you shall access your cluster, databases and collections.

The database used in this project called **sample_restaurants** is available in the **Sample Dataset** you can load on any free Atlas mongodb account.

## Project structure

### Demo

A demo module is provided, linked to a simple fake database simulated by a dictionary.
The demo_routes are imported to main router with "include_router()" method from fastapi.

### Main router

The real router is placed in /routes folder and imported in main.py the same way.

Mongodb connexion is managed in main.py with @app.on_event() decorators.

## Models

In order to define easy typing, I suggest to use python 3.9 or later.

Models are mainly defined by [Pydantic](https://docs.pydantic.dev/) librairy.
It allows to define database schematics with classes which inherit BaseModel from Pydantic.

You will find a nice startup for API setup [here](https://www.mongodb.com/languages/python/pymongo-tutorial).

## Debugg in vsCode

**launch.json** has been set up in ./.vscode/ for debugging purpose (modify values accordingly to your project). Just place the file at the right place and click on **Start debugging** button from **Run and debugg** menu.

```json
{
    // Use IntelliSense to learn about possible attributes.
    // Hover to view descriptions of existing attributes.
    // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python Debugger: FastAPI",
            "type": "debugpy",
            "request": "launch",
            "module": "uvicorn",
            // "justMyCode": false, // to debugg also in libraries!
            "args": [
                "src.app.main:app",
                "--reload"
            ],
            "jinja": true
        }
    ]
}
```

## Deploy

My choice is to deploy this api on a self-hosted place. You can of course deploy it on any server/service you want.

### Docker nginx

A docker-compose.yml file let you build a docker image containing nginx and current api app.
Running nginx inside Docker offers several advantages:

* Isolation: Docker containers provide isolation for applications, including the Nginx web server. Each container runs in its own environment, separate from other containers and the host system, which helps prevent conflicts and dependency issues.
* Portability: Docker containers are portable and can be easily deployed to different environments, such as development, testing, and production, without needing to worry about differences in the underlying system configuration.
* Scalability: Docker makes it easy to scale applications horizontally by spinning up multiple instances of containers. This allows you to handle increased traffic and workload by distributing the load across multiple instances of Nginx containers.
* Consistency: Docker enables you to define the environment and dependencies for your Nginx server using a Dockerfile, ensuring consistency across different deployments and environments.

Two dockerfiles set up the configurations required for each part (nginx and fastapi app).

### Testing Docker deployement

From root level of the project, several commands may build and serve the app:

```bash
# build docker image
docker-compose build
# run docker containers
docker-compose up
# check for containers deployement
docker ps -a

# stop containers
docker-compose down
# run back containers with an updated configuration
docker-compose up -d
```

First tries will be on localhost network so ports should be set up with HTTP (:80)

```yml
# docker-compose.yml
version: '3'
services:

  fastapi:
    build:
      context: .
      dockerfile: fastapi_dockerfile
    ports:
      - "8000:8000" # host_port:container_port (:8000 for fastapi)
    env_file:
      - .env # give access to credentials

  nginx:
    build:
      context: .
      dockerfile: nginx_dockerfile
    ports:
      - "8080:80" # host_port (:80 in use on host, so using 8080):container_port(Http)
    depends_on:
      - fastapi # ref to fastapi service above
```

```conf
# nginx.conf
events {}

http {
    upstream fastapi {
        server 127.0.0.1:8000;
    }

    server {
        listen 127.0.0.1:80 default_server;

        location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

    }
}

```

Once containers run, you can test in your browser at uris shown in [run project part](#run-project).

### Production deployement

#### Port HTTPS (:446)

HTTP (:80) is not secure, so HTTPS (:446) must be used for giving access to api from internet. HTTPS allows traffic encryption between client and server, protecting against eavesdropping and interception.

Indeed the following points should also be taken in consideration:

* Monitor network traffic and server logs for suspicious activity, and implement intrusion detection and prevention systems if necessary.
* Consider using a web application firewall (WAF) to filter and block malicious traffic before it reaches your server.
* Regularly audit and review your server's security configuration to identify and address potential vulnerabilities.

#### Domain name

Domain name is mostly required to expose host's IP address (hence it is possible to expose IP address with ssl-certificate but the cost is higher).

Many registrars give access to domain name registration and DNS management in order to point to your self-hosted server.
Then you can get a ssl-certificate from a service like [Letsencrypt.org](https://letsencrypt.org/).

docker-compose.yml must reference correct port.

```yml
# docker-compose.yml
version: '3'
services:

  fastapi:
    build:
      context: .
      dockerfile: fastapi_dockerfile
    ports:
      - "8000:8000" # host_port:container_port (:8000 for fastapi)
    env_file:
      - .env # give access to credentials

  nginx:
    build:
      context: .
      dockerfile: nginx_dockerfile
    ports:
      - "443:443" # host_port (:80 in use on host, so using 8080):container_port(Http)
    depends_on:
      - fastapi # ref to fastapi service above
```

nginx.conf must specify port change, domain_name and ssl certificate.

```conf
# nginx.conf
events {}

http {
    upstream fastapi {
        server 127.0.0.1:8000;
    }

    server {
    listen 443 ssl;
    server_name your_domain.com;

    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/privatekey.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
}
```

still W.I.P ....
Production deployement part needs to be tested.