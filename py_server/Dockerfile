# 
FROM aecgeeks/ifcopenshell

RUN sudo apt-get update
RUN sudo apt-get install python3-pip -y

# 
WORKDIR /usr/src/app

# 
COPY ./requirements.txt /usr/src/app/requirements.txt
COPY ./files /usr/src/app/files
RUN sudo chmod -R 754 /usr/src/app/files

# 
RUN python3 -m pip install --upgrade pip

# 
RUN pip install --no-cache-dir -r /usr/src/app/requirements.txt

# 
COPY ./app /usr/src/app/app

# 
CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
