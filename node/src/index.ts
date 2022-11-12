import server from './server'
import dotenv from 'dotenv'
import { start } from 'repl'

dotenv.config()
const port = process.env.PORT || 3000

const startServer = () => {
  server.listen(port, () => {
    console.log(`Server running on port: ${port}`)
  })
}

startServer()
