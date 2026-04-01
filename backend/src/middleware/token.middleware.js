const { prisma } = require('../config/prisma')
const { hashToken } = require('../utils/token')

async function authenticateApiToken(req, _res, next) {
  const auth = req.headers.authorization || ''
  if (!auth.startsWith('Bearer ')) {
    req.delivery = null
    return next()
  }

  const rawToken = auth.slice(7)
  const tokenHash = hashToken(rawToken)
  const token = await prisma.apiToken.findFirst({
    where: {
      tokenHash,
      revokedAt: null,
    },
    include: { dataset: true },
  })

  req.delivery = token || null
  return next()
}

module.exports = { authenticateApiToken }
