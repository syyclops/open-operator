import { Router } from 'express'
import { getBuilding } from './controller'

const router = Router()

// Get Buildings
router.get('/:uri', async (req, res) => {
  const buildingUri = req.params.uri

  try {
    const building = await getBuilding(buildingUri)

    res.json({
      status: 'SUCCESS',
      data: building,
    })
  } catch (err) {
    res.json({
      status: 'FAILED',
      message: (err as any).message,
    })
  }
})

export default router
