#!/bin/bash

rm -rf ~/server/ny_restAPI
mkdir ~/server/ny_restAPI
cp ./fastapi_dockerfile ~/server/ny_restAPI/fastapi_dockerfile
cp ./.env ~/server/ny_restAPI/.env
cp -r ./src ~/server/ny_restAPI/src
cp ./requirements.txt ~/server/ny_restAPI/requirements.txt
