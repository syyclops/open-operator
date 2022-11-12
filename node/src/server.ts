import express, { Express, Request, Response } from 'express'
import dotenv from 'dotenv'
dotenv.config()
import type { ErrorRequestHandler } from 'express'
import routes from './routes'

const app: Express = express()

const errorHandler: ErrorRequestHandler = (err, req, res, next) => {}

app.use(errorHandler)

app.use(routes)

export default app
