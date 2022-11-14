import { Router } from 'express'
import neo4j_driver from '../../../../config/neo4j_driver'
import { Building } from '../../../../types/building'
import { Room } from '../../../../types/room'

/**
 * @swagger
 * /api/v1/building/{uri}/rooms:
 *   get:
 *     description: Get Building rooms
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
  '/v1/building/:uri/rooms',
  async (req, res) => {
    const buildingUri = req.params.uri

    const session = neo4j_driver.session()

    try {
      const result = await session.run(
        `MATCH (b:Building {uri: $uri})-[:hasPart]-(r:Room) return r`,
        {
          uri: buildingUri,
        },
      )

      var rooms: Room[] = []
      for (var room of result.records) {
        const node = room.get(0)
        const roomProperties: Room = node.properties
        rooms.push(roomProperties)
      }

      res.json({
        status: 'SUCCESS',
        data: rooms,
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
