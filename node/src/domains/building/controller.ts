import neo4j_driver from '../../config/neo4j_driver'
import { Building } from './types'

const getBuilding = async (uri: string) => {
  const session = neo4j_driver.session()

  try {
    const result = await session.run(
      `MATCH (b:Building {uri: $uri}) return b`,
      {
        uri: uri,
      },
    )

    const singleRecord = result.records[0]
    const node = singleRecord.get(0)

    const building: Building = node.properties

    console.log(building)

    return building
  } finally {
    await session.close()
  }

  // // on application exit:
  // await neo4j_driver.close()
}

export { getBuilding }
