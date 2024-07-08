FROM mongo:latest

RUN apt update
RUN apt install wget -y
RUN wget https://fastdl.mongodb.org/tools/db/mongodb-database-tools-ubuntu2004-x86_64-100.9.5.deb
RUN apt install -y --allow-downgrades ./mongodb-database-tools-ubuntu2004-x86_64-100.9.5.deb

COPY . .

CMD sleep 1 && mongosh --username root --password password --host mongo_db --port 27017 --eval "use findrecipe" --eval  "db.dropDatabase()" && mongoimport --host mongo_db --port 27017 --username root --password password --authenticationDatabase admin --db findrecipe --collection recipes --type csv --headerline --file recipes.csv && mongoimport --host mongo_db --port 27017 --username root --password password --authenticationDatabase admin --db findrecipe --collection ingredients --type csv --headerline --file ingredients.csv && mongoimport --host mongo_db --port 27017 --username root --password password --authenticationDatabase admin --db findrecipe --collection weights --type csv --headerline --file weights.csv
