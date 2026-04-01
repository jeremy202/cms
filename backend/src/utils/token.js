const crypto = require('crypto')

function generateApiToken() {
  return `cms_${crypto.randomBytes(32).toString('hex')}`
}

function hashToken(raw) {
  return crypto.createHash('sha256').update(raw).digest('hex')
}

module.exports = { generateApiToken, hashToken }
