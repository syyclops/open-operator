import  {  Router } from 'express'
import buildingRoutes from '../domains/building'

const router = Router()

router.use("/building", buildingRoutes)

export default router