const express = require('express')
const entriesController = require('../controllers/entries.controller')
const { authenticate, authorize } = require('../middleware/auth.middleware')
const { authenticateApiToken } = require('../middleware/token.middleware')

const router = express.Router()

// Admin/authoring API (full draft visibility)
router.get('/:contentType', entriesController.list)
router.get('/:contentType/:id', entriesController.getOne)
router.post('/:contentType', authenticate, authorize('ADMIN', 'EDITOR'), entriesController.create)
router.put('/:contentType/:id', authenticate, authorize('ADMIN', 'EDITOR'), entriesController.update)
router.delete('/:contentType/:id', authenticate, authorize('ADMIN'), entriesController.remove)

// Sanity-like delivery API
const deliveryRouter = express.Router()
deliveryRouter.get('/query', authenticateApiToken, entriesController.query)
deliveryRouter.get('/:dataset/:contentType', authenticateApiToken, entriesController.list)
deliveryRouter.get('/:dataset/:contentType/:id', authenticateApiToken, entriesController.getOne)

module.exports = { router, deliveryRouter }
