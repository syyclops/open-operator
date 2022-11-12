import neo4j from 'neo4j-driver'
import dotenv from 'dotenv'
dotenv.config()

const driver = neo4j.driver(
  process.env.NEO4J_URL!,
  neo4j.auth.basic(process.env.NEO4J_USER!, process.env.NEO4J_PASS!),
)

export default driver
