# 
FROM aecgeeks/ifcopenshell

RUN sudo apt-get update
RUN sudo apt-get install python3-pip -y

# 
WORKDIR /usr/src/app

# 
COPY ./requirements.txt /usr/src/app/requirements.txt

# 
RUN python3 -m pip install --upgrade pip

# 
RUN pip install --no-cache-dir -r /usr/src/app/requirements.txt

# 
# COPY ./app /usr/src/app/app

EXPOSE 3000

# 
CMD ["/bin/bash"]
