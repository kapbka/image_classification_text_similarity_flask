# set base image (host OS)
FROM base:latest

# set the working directory in the container
WORKDIR /code/restful_flask_2/web_text_similarity

# copy and install
COPY en_core_web_sm-2.3.0.tar.gz .
RUN pip install ./en_core_web_sm-2.3.0.tar.gz

# copy the content of the local src directory to the working directory
COPY . .

# command to run on container start
CMD [ "python", "app.py"]
