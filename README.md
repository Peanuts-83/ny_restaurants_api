[![Python](https://img.shields.io/badge/Language-Python-info?logo=python&logoColor=white&color=3776AB)](https://www.python.org/)
[![Fastapi](https://img.shields.io/badge/Code-Fastapi-info?logo=fastapi&logoColor=white&color=009688)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/Database-MongoDB-info?logo=mongodb&logoColor=white&color=47A248)](https://www.mongodb.com/)
[![Docker](https://img.shields.io/badge/Deploy-Docker-info?logo=docker&logoColor=white&color=2496ED)](https://www.docker.com/)
[![OpenApi](https://img.shields.io/badge/Doc-OpenApi-info?logo=openapiinitiative&logoColor=white&color=6BA539)](https://www.openapis.org/)

# Newyork restaurants API

[Fastapi](https://fastapi.tiangolo.com/) (python) app linked to [Atlas-Mongodb database](https://www.mongodb.com/).

The purpose of this app is to provide quick and simple api to support any front-end project related to.

You can query to collections: restaurants and neighborhoods. Routes have been defined to query for one item, a list of items, distinct values on a field, create, update and delete items or fields.

*A little demo api is also defined, not linked to any database, but connected to local variable for quick testing purpose.*

## Fastapi

Over the fast, intuitive and easy way to build your API, fastapi is totally standard-based giving access to wonderfull [OpenAPI (Swagger)](https://github.com/OAI/OpenAPI-Specification) and [JSON Schema](https://json-schema.org/).

By the way, a friend of mine told me Python was one of the worst code language for heat climate change, because it's not a compiled but interpreted language, low to run and large on space disk use |:( (his name's Grumpy!)

Up your choice to use it or not.

### Setup project

Use any package manager (pip, conda, ...) [to install fastapi, uvicorn](https://fastapi.tiangolo.com/tutorial/#install-fastapi) and required librairies:

```bash
# install with conda and a virtual env in my case
conda create -n NYCrest_env python=3.12.7 anaconda
conda activate NYCrest_env
pip install -r requirements.txt
```

Select right python interpreter: CTL+SHIFT+P "Python select interpreter" (I select NYCrest_env)

### First launch - set centroid field

Atlas mongoDB provides a **Sample Dataset**, which **sample_restaurants** used in this project comes from.

You will find in **main.py** file a commented line with *console_setup()* method . Uncomment and activate **centroid** option in order to update your *neighborhoods collection*. This way each of your neighborhood item will gain **geometry.centroid** field, the center coordinates of borough's polygon.

You can then comment *console_setup()* line back.

### Run project

Navigate to the directory where your main.py file is located and run:

```bash
uvicorn main:app --reload
```

**--reload** option is a watch mode that reloads app at each change in the source code.

Once served:

* the app shall be available at: <http://localhost:8000/>
* **OpenApi documentation** is served at: <http://localhost:8000/docs>
* Redoc documentation is served at: <http://localhost:8000/redoc>

### Debug project

Json conf file is available at .vscode/launch.json, providing abillity to debug api app from "Run and debug" menu in vsCode.
Just click **Play** button in front of **Python debugger: FastAPi**.

This way you can place breakpoints in your code and access available data at any moment.

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

## Real open data - NYC Open Data (Socrata)

### DocRef

* https://dev.socrata.com/foundry/bronx.lehman.cuny.edu/nc96-khaq
* https://support.socrata.com/hc/en-us/articles/115005364207-Access-Data-Insights-Data-using-OData

### API

* https://data.cityofnewyork.us/api/odata/v4/pitm-atqc

### Analyse

Real recent data could be used in a second time, on condition to be reformated the right way to apply current model.
We can download data in *.csv format, which allows us to rework them and insert them into a DB, and integrate them into a framework which allows a more elegant query system...

The SoQL (SQL like) query used for the public API is encoded in the url, which gives a disgusting blob! No way I would use this way of exposing my requests. Come on baby, don't you know body payload?!!  XD

Query for top 100 results from restaurant table with all columns:

* URl

```bash
https://data.cityofnewyork.us/resource/pitm-atqc.json?$query=SELECT%0A%20%20%60objectid%60%2C%0A%20%20%60globalid%60%2C%0A%20%20%60seating_interest_sidewalk%60%2C%0A%20%20%60restaurant_name%60%2C%0A%20%20%60legal_business_name%60%2C%0A%20%20%60doing_business_as_dba%60%2C%0A%20%20%60bulding_number%60%2C%0A%20%20%60street%60%2C%0A%20%20%60borough%60%2C%0A%20%20%60zip%60%2C%0A%20%20%60business_address%60%2C%0A%20%20%60food_service_establishment%60%2C%0A%20%20%60sidewalk_dimensions_length%60%2C%0A%20%20%60sidewalk_dimensions_width%60%2C%0A%20%20%60sidewalk_dimensions_area%60%2C%0A%20%20%60roadway_dimensions_length%60%2C%0A%20%20%60roadway_dimensions_width%60%2C%0A%20%20%60roadway_dimensions_area%60%2C%0A%20%20%60approved_for_sidewalk_seating%60%2C%0A%20%20%60approved_for_roadway_seating%60%2C%0A%20%20%60qualify_alcohol%60%2C%0A%20%20%60sla_serial_number%60%2C%0A%20%20%60sla_license_type%60%2C%0A%20%20%60landmark_district_or_building%60%2C%0A%20%20%60landmarkdistrict_terms%60%2C%0A%20%20%60healthcompliance_terms%60%2C%0A%20%20%60time_of_submission%60%2C%0A%20%20%60latitude%60%2C%0A%20%20%60longitude%60%2C%0A%20%20%60community_board%60%2C%0A%20%20%60council_district%60%2C%0A%20%20%60census_tract%60%2C%0A%20%20%60bin%60%2C%0A%20%20%60bbl%60%2C%0A%20%20%60nta%60%0AORDER%20BY%20%60objectid%60%20ASC%20NULL%20LAST%0ALIMIT%20100%0AOFFSET%200&
```

* Decoded request

```SQL
$query: SELECT
  `objectid`,
  `globalid`,
  `seating_interest_sidewalk`,
  `restaurant_name`,
  `legal_business_name`,
  `doing_business_as_dba`,
  `bulding_number`,
  `street`,
  `borough`,
  `zip`,
  `business_address`,
  `food_service_establishment`,
  `sidewalk_dimensions_length`,
  `sidewalk_dimensions_width`,
  `sidewalk_dimensions_area`,
  `roadway_dimensions_length`,
  `roadway_dimensions_width`,
  `roadway_dimensions_area`,
  `approved_for_sidewalk_seating`,
  `approved_for_roadway_seating`,
  `qualify_alcohol`,
  `sla_serial_number`,
  `sla_license_type`,
  `landmark_district_or_building`,
  `landmarkdistrict_terms`,
  `healthcompliance_terms`,
  `time_of_submission`,
  `latitude`,
  `longitude`,
  `community_board`,
  `council_district`,
  `census_tract`,
  `bin`,
  `bbl`,
  `nta`
ORDER BY `objectid` ASC NULL LAST
LIMIT 100
OFFSET 0
```

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
CTL+C # in logs window or
docker-compose stop
# run back containers with logs --follow
docker-compose start -f
# stop and remove containers
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
