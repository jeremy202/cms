const { prisma } = require('../config/prisma')
const { normalizeApiId, parseSchema } = require('../utils/schema')

async function listContentTypes() {
  return prisma.contentType.findMany({
    include: { schemaFields: true },
    orderBy: { createdAt: 'desc' },
  })
}

async function createContentType(userId, payload) {
  const parsed = parseSchema(payload.schema)
  const apiId = payload.apiId ? normalizeApiId(payload.apiId) : normalizeApiId(payload.name)

  return prisma.$transaction(async (tx) => {
    const created = await tx.contentType.create({
      data: {
        name: payload.name,
        apiId,
        description: payload.description,
        schema: parsed.raw,
        createdById: userId,
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
      include: { schemaFields: true },
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
      include: { schemaFields: true },
    })
  })
}

module.exports = {
  listContentTypes,
  createContentType,
  updateContentType,
}
