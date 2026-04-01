const { prisma } = require('../config/prisma')
const { normalizeApiId, parseSchema } = require('../utils/schema')
const { ensureDefaultDataset } = require('./dataset.service')

async function listContentTypes(datasetName) {
  let datasetId = null
  if (datasetName) {
    const dataset = await prisma.dataset.findUnique({ where: { name: datasetName } })
    if (!dataset) return []
    datasetId = dataset.id
  }

  return prisma.contentType.findMany({
    where: datasetId ? { datasetId } : undefined,
    include: { schemaFields: true, dataset: true },
    orderBy: { createdAt: 'desc' },
  })
}

async function createContentType(userId, payload) {
  const parsed = parseSchema(payload.schema)
  const apiId = payload.apiId ? normalizeApiId(payload.apiId) : normalizeApiId(payload.name)

  const dataset = payload.datasetId
    ? await prisma.dataset.findUnique({ where: { id: payload.datasetId } })
    : await ensureDefaultDataset()

  if (!dataset) throw new Error('Dataset not found')

  return prisma.$transaction(async (tx) => {
    const created = await tx.contentType.create({
      data: {
        name: payload.name,
        apiId,
        description: payload.description,
        schema: parsed.raw,
        createdById: userId,
        datasetId: dataset.id,
      },
    })

    await tx.contentTypeField.createMany({
      data: parsed.fields.map((field) => ({
        contentTypeId: created.id,
        ...field,
      })),
    })

    return tx.contentType.findUnique({
      where: { id: created.id },
      include: { schemaFields: true, dataset: true },
    })
  })
}

async function updateContentType(contentTypeId, payload) {
  const existing = await prisma.contentType.findUnique({ where: { id: contentTypeId } })
  if (!existing) throw new Error('Content type not found')

  const parsed = parseSchema(payload.schema)

  return prisma.$transaction(async (tx) => {
    const updated = await tx.contentType.update({
      where: { id: contentTypeId },
      data: {
        name: payload.name,
        description: payload.description,
        schema: parsed.raw,
        version: { increment: 1 },
      },
    })

    await tx.contentTypeField.deleteMany({ where: { contentTypeId } })
    await tx.contentTypeField.createMany({
      data: parsed.fields.map((field) => ({
        contentTypeId,
        ...field,
      })),
    })

    return tx.contentType.findUnique({
      where: { id: updated.id },
      include: { schemaFields: true, dataset: true },
    })
  })
}

module.exports = {
  listContentTypes,
  createContentType,
  updateContentType,
}
