import { Router } from 'express'
import neo4j_driver from '../../../../config/neo4j_driver'

/**
 * @swagger
 * /api/v1/ontology/graphInit:
 *   post:
 *     description: Init Graph
 *     responses:
 *       200:
 *         description: OK
 *     tags:
 *       - ontology
 */
module.exports = Router({ mergeParams: true }).post(
  '/v1/ontology/graphInit',
  async (req, res) => {
    const session = neo4j_driver.session()

    try {
      const result = await session.run(
        `call n10s.graphconfig.init({handleVocabUris: "IGNORE"})`,
      )

      //   console.log(result.records[0])

      res.json({
        status: 'SUCCESS',
        data: 'Graph inited',
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
