import express, { Express } from 'express'
import dotenv from 'dotenv'
dotenv.config()
import type { ErrorRequestHandler } from 'express'
import router from './routes/createRouter'

const app: Express = express()

const errorHandler: ErrorRequestHandler = (err, req, res, next) => {}

app.use(errorHandler)

app.use(express.json())
app.use(express.urlencoded({ extended: true }))

app.use('/api', router())

export default app
