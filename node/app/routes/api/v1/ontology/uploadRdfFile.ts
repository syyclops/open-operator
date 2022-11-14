import { Router } from 'express'
import neo4j_driver from '../../../../config/neo4j_driver'

/**
 * @swagger
 * /api/v1/ontology/uploadRdfFile:
 *   post:
 *     description: Upload RDF File
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               url:
 *                 type: string
 *                 description: link to raw turtle file for rdf graph
 *     responses:
 *       200:
 *         description: OK
 *     tags:
 *       - ontology
 */
module.exports = Router({ mergeParams: true }).post(
  '/v1/ontology/uploadRdfFile',
  async (req, res) => {
    const url = req.body.url
    const session = neo4j_driver.session()

    try {
      const result = await session.run(
        `call n10s.rdf.import.fetch($url, 'Turtle')`,
        { url: url },
      )

      res.json({
        status: 'SUCCESS',
        data: 'Uploaded Ontology successfully',
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
