import express, { Express } from 'express'
import dotenv from 'dotenv'
dotenv.config()
import type { ErrorRequestHandler } from 'express'
import router from './routes/createRouter'
import swaggerJsDoc from 'swagger-jsdoc'
import swaggerUi from 'swagger-ui-express'
import glob from 'glob'

const app: Express = express()

const options = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'Hello World',
      version: '1.0.0',
    },
  },
  apis: glob
    .sync('**/*.js', { cwd: `${__dirname}/routes/api/` })
    .map((filename) => 'dist/app/routes/api/' + filename), // files containing annotations as above
}

const swaggerDocs = swaggerJsDoc(options)

app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerDocs))

const errorHandler: ErrorRequestHandler = (err, req, res, next) => {}

app.use(errorHandler)

app.use(express.json())
app.use(express.urlencoded({ extended: true }))

app.use('/api', router())

export default app
