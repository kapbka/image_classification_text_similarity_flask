# set base image (host OS)
FROM base:latest

# set the working directory in the container
WORKDIR /code/restful_flask_2/web_bank

# copy the content of the local src directory to the working directory
COPY . .

# command to run on container start
CMD [ "python", "app.py"]
