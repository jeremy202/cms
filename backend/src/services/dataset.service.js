const { prisma } = require('../config/prisma')
const { generateApiToken, hashToken } = require('../utils/token')

async function ensureDefaultDataset() {
  const existing = await prisma.dataset.findFirst({ where: { name: 'production' } })
  if (existing) return existing
  return prisma.dataset.create({ data: { name: 'production', visibility: 'PUBLIC' } })
}

async function listDatasets() {
  return prisma.dataset.findMany({ orderBy: { createdAt: 'asc' } })
}

async function createDataset(payload) {
  return prisma.dataset.create({
    data: {
      name: payload.name,
      visibility: payload.visibility || 'PRIVATE',
    },
  })
}

async function createDeliveryToken(userId, payload) {
  const rawToken = generateApiToken()
  const tokenHash = hashToken(rawToken)

  const record = await prisma.apiToken.create({
    data: {
      name: payload.name,
      tokenHash,
      scopes: payload.scopes || { read: true },
      datasetId: payload.datasetId || null,
      createdById: userId,
    },
  })

  return {
    ...record,
    rawToken,
  }
}

async function listDeliveryTokens() {
  return prisma.apiToken.findMany({
    where: { revokedAt: null },
    include: { dataset: true },
    orderBy: { createdAt: 'desc' },
  })
}

async function revokeDeliveryToken(id) {
  return prisma.apiToken.update({
    where: { id },
    data: { revokedAt: new Date() },
  })
}

module.exports = {
  ensureDefaultDataset,
  listDatasets,
  createDataset,
  createDeliveryToken,
  listDeliveryTokens,
  revokeDeliveryToken,
}
