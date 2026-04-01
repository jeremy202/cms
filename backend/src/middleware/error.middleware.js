function notFound(_req, res) {
  return res.status(404).json({ error: 'Not found' })
}

function errorHandler(err, _req, res, _next) {
  if (err?.name === 'ZodError') {
    return res.status(400).json({ error: 'Validation failed', details: err.issues })
  }
  return res.status(500).json({ error: err.message || 'Internal server error' })
}

module.exports = { notFound, errorHandler }
