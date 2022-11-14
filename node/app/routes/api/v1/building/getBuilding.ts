import { Router } from 'express'
import neo4j_driver from '../../../../config/neo4j_driver'
import { Building } from '../../../../types/building'

/**
 * @swagger
 * /api/v1/building/{uri}:
 *   get:
 *     description: Get Building by uri
 *     parameters:
 *     - in: path
 *       name: uri
 *       description: building uri
 *       type: string
 *       required: true
 *       minimum: 1
 *     responses:
 *       200:
 *         description: OK
 *     tags:
 *       - building
 */
module.exports = Router({ mergeParams: true }).get(
  '/v1/building/:uri',
  async (req, res) => {
    const buildingUri = req.params.uri

    const session = neo4j_driver.session()

    try {
      const result = await session.run(
        `MATCH (b:Building {uri: $uri}) return b`,
        {
          uri: buildingUri,
        },
      )

      const singleRecord = result.records[0]

      var building: Building | null = null

      if (singleRecord !== undefined) {
        const node = singleRecord.get(0)

        building = node.properties
      }

      res.json({
        status: 'SUCCESS',
        data: building,
      })
    } catch (err) {
      res.json({
        status: 'FAILED',
        message: (err as any).message,
      })
    } finally {
      await session.close()
    }
  },
)
