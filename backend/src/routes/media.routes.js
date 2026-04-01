const express = require('express')
const multer = require('multer')
const path = require('path')
const { upload } = require('../controllers/media.controller')
const { authenticate, authorize } = require('../middleware/auth.middleware')
const { fileStorageName } = require('../services/media.service')

const storage = multer.diskStorage({
  destination: (_req, _file, cb) => cb(null, path.resolve(process.cwd(), 'uploads')),
  filename: (_req, file, cb) => cb(null, fileStorageName(file)),
})

const uploader = multer({
  storage,
  limits: { fileSize: 10 * 1024 * 1024 },
})

const router = express.Router()

router.post('/', authenticate, authorize('ADMIN', 'EDITOR'), uploader.single('file'), upload)

module.exports = router
