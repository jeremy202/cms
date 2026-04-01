const path = require('path')
const { prisma } = require('../config/prisma')

async function saveMedia(file) {
  const url = `/uploads/${file.filename}`
  return prisma.mediaFile.create({
    data: {
      originalName: file.originalname,
      filename: file.filename,
      mimeType: file.mimetype,
      size: file.size,
      url,
    },
  })
}

function fileStorageName(file) {
  const ext = path.extname(file.originalname)
  return `${Date.now()}-${Math.round(Math.random() * 1e9)}${ext}`
}

module.exports = { saveMedia, fileStorageName }
