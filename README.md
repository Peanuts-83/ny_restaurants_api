# Newyork restaurants - WIP...

[Fastapi](https://fastapi.tiangolo.com/) (python) app linked to [Atlas-Mongodb database](https://www.mongodb.com/).

The purpose of this app is to provide quick and simple api to support any front-end project related to.

## Fastapi

Over the fast, intuitive and easy to code framework it provides, fastapi is totally standard-based giving access to wonderfull [OpenAPI (Swagger)](https://github.com/OAI/OpenAPI-Specification) and [JSON Schema](https://json-schema.org/)

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