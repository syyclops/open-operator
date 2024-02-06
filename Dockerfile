FROM python:3.10

WORKDIR /usr/src/app

COPY . .

RUN python3 -m pip install -e .
RUN pip install python-dotenv

EXPOSE 8080

# Run server.py when the container launches
CMD ["python", "./examples/server.py"]
