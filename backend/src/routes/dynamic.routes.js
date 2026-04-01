const express = require('express')
const entriesController = require('../controllers/entries.controller')
const { authenticate, authorize } = require('../middleware/auth.middleware')

const router = express.Router()

router.get('/:contentType', entriesController.list)
router.get('/:contentType/:id', entriesController.getOne)

router.post('/:contentType', authenticate, authorize('ADMIN', 'EDITOR'), entriesController.create)
router.put('/:contentType/:id', authenticate, authorize('ADMIN', 'EDITOR'), entriesController.update)
router.delete('/:contentType/:id', authenticate, authorize('ADMIN'), entriesController.remove)

module.exports = router
