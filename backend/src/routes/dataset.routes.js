const express = require('express')
const {
  listAll,
  createOne,
  listTokens,
  createToken,
  revokeToken,
} = require('../controllers/dataset.controller')
const { authenticate, authorize } = require('../middleware/auth.middleware')

const router = express.Router()

router.get('/', authenticate, listAll)
router.post('/', authenticate, authorize('ADMIN'), createOne)

router.get('/tokens', authenticate, authorize('ADMIN'), listTokens)
router.post('/tokens', authenticate, authorize('ADMIN'), createToken)
router.delete('/tokens/:id', authenticate, authorize('ADMIN'), revokeToken)

module.exports = router
