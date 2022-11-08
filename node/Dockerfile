FROM node:16
WORKDIR /usr/src/app

# Install app dependencies
# A wildcard is used to ensure both package.json and package-lock.json are copied
COPY package*.json ./

RUN npm install

# Bundle app source
COPY . .
EXPOSE 3000
CMD ["npm", "start"]