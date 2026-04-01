const { createContentTypeSchema } = require('../validators/contentType.validator')
const {
  listContentTypes,
  createContentType,
  updateContentType,
} = require('../services/contentType.service')

async function list(req, res, next) {
  try {
    const types = await listContentTypes(req.query.dataset)
    return res.json(types)
  } catch (err) {
    return next(err)
  }
}

async function create(req, res, next) {
  try {
    const payload = createContentTypeSchema.parse(req.body)
    const created = await createContentType(req.user.sub, payload)
    return res.status(201).json(created)
  } catch (err) {
    if (err.code === 'P2002') {
      return res.status(409).json({ error: 'apiId already exists' })
    }
    return next(err)
  }
}

async function update(req, res, next) {
  try {
    const payload = createContentTypeSchema.parse(req.body)
    const updated = await updateContentType(req.params.id, payload)
    return res.json(updated)
  } catch (err) {
    if (err.message === 'Content type not found') {
      return res.status(404).json({ error: err.message })
    }
    return next(err)
  }
}

module.exports = { list, create, update }
