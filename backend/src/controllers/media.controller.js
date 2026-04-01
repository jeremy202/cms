const { saveMedia } = require('../services/media.service')

async function upload(req, res, next) {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'file is required' })
    }
    const media = await saveMedia(req.file)
    return res.status(201).json(media)
  } catch (err) {
    return next(err)
  }
}

module.exports = { upload }
