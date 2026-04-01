const {
  listEntries,
  createEntry,
  getEntry,
  updateEntry,
  deleteEntry,
} = require('../services/entry.service')

function parseFilterQuery(query) {
  const filters = {}
  for (const [key, value] of Object.entries(query)) {
    const match = key.match(/^filters\[(.+)\]$/)
    if (match) {
      filters[match[1]] = value
    }
  }
  return filters
}

async function list(req, res, next) {
  try {
    const filters = parseFilterQuery(req.query)
    const result = await listEntries(req.params.contentType, {
      page: req.query.page,
      pageSize: req.query.pageSize,
      sort: req.query.sort,
      filters,
    })
    return res.json(result)
  } catch (err) {
    if (err.message === 'Content type not found') {
      return res.status(404).json({ error: err.message })
    }
    return next(err)
  }
}

async function create(req, res, next) {
  try {
    const result = await createEntry(req.params.contentType, req.body)
    return res.status(201).json(result)
  } catch (err) {
    if (err.message === 'Content type not found') {
      return res.status(404).json({ error: err.message })
    }
    if (err.message.startsWith('Field')) {
      return res.status(400).json({ error: err.message })
    }
    return next(err)
  }
}

async function getOne(req, res, next) {
  try {
    const result = await getEntry(req.params.contentType, req.params.id)
    return res.json(result)
  } catch (err) {
    if (['Content type not found', 'Entry not found'].includes(err.message)) {
      return res.status(404).json({ error: err.message })
    }
    return next(err)
  }
}

async function update(req, res, next) {
  try {
    const result = await updateEntry(req.params.contentType, req.params.id, req.body)
    return res.json(result)
  } catch (err) {
    if (['Content type not found', 'Entry not found'].includes(err.message)) {
      return res.status(404).json({ error: err.message })
    }
    if (err.message.startsWith('Field')) {
      return res.status(400).json({ error: err.message })
    }
    return next(err)
  }
}

async function remove(req, res, next) {
  try {
    await deleteEntry(req.params.contentType, req.params.id)
    return res.status(204).send()
  } catch (err) {
    if (['Content type not found', 'Entry not found'].includes(err.message)) {
      return res.status(404).json({ error: err.message })
    }
    return next(err)
  }
}

module.exports = {
  list,
  create,
  getOne,
  update,
  remove,
}
