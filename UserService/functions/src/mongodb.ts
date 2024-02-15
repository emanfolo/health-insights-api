import * as mongoDB from "mongodb";

export const connectMongoDB = async () => {
  const user = process.env.USERNAME;
  const password = process.env.PASSWORD;
  const uri = `mongodb+srv://${user}:${password}@wellnessmate.fqctlmb.mongodb.net/?retryWrites=true&w=majority`;

  const mongoClient = new mongoDB.MongoClient(uri);

  await mongoClient.connect();

  return mongoClient;
};
