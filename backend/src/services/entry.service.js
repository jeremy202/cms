const { prisma } = require('../config/prisma')
const { validateEntryAgainstSchema } = require('../utils/schema')

function buildPagination(query) {
  const page = Math.max(1, Number(query.page || 1))
  const pageSize = Math.max(1, Math.min(100, Number(query.pageSize || 20)))
  return { page, pageSize, skip: (page - 1) * pageSize, take: pageSize }
}

function applyQueryOps(entries, query) {
  let output = [...entries]

  const { filters, sort } = query
  if (filters) {
    for (const [key, value] of Object.entries(filters)) {
      output = output.filter((item) => String(item.data?.[key] ?? '') === String(value))
    }
  }

  if (sort) {
    const [field, direction = 'asc'] = String(sort).split(':')
    output.sort((a, b) => {
      const av = a.data?.[field]
      const bv = b.data?.[field]
      if (av === bv) return 0
      if (av == null) return 1
      if (bv == null) return -1
      const cmp = String(av).localeCompare(String(bv), undefined, { numeric: true })
      return direction === 'desc' ? -cmp : cmp
    })
  }

  return output
}

async function resolveContentType(apiId) {
  return prisma.contentType.findUnique({
    where: { apiId },
    include: { schemaFields: { orderBy: { order: 'asc' } } },
  })
}

async function listEntries(apiId, query = {}) {
  const contentType = await resolveContentType(apiId)
  if (!contentType) throw new Error('Content type not found')

  const all = await prisma.entry.findMany({
    where: { contentTypeId: contentType.id },
    orderBy: { createdAt: 'desc' },
  })

  const filtered = applyQueryOps(all, {
    filters: query.filters,
    sort: query.sort,
  })

  const { page, pageSize, skip, take } = buildPagination(query)
  const paginated = filtered.slice(skip, skip + take)

  return {
    data: paginated,
    meta: {
      page,
      pageSize,
      total: filtered.length,
      pageCount: Math.ceil(filtered.length / pageSize) || 1,
    },
    contentType,
  }
}

async function createEntry(apiId, payload) {
  const contentType = await resolveContentType(apiId)
  if (!contentType) throw new Error('Content type not found')

  const data = validateEntryAgainstSchema(contentType.schemaFields, payload.data || {})

  const entry = await prisma.entry.create({
    data: {
      contentTypeId: contentType.id,
      data,
      published: Boolean(payload.published),
    },
  })

  return { entry, contentType }
}

async function getEntry(apiId, id) {
  const contentType = await resolveContentType(apiId)
  if (!contentType) throw new Error('Content type not found')

  const entry = await prisma.entry.findFirst({ where: { id, contentTypeId: contentType.id } })
  if (!entry) throw new Error('Entry not found')

  return { entry, contentType }
}

async function updateEntry(apiId, id, payload) {
  const { entry, contentType } = await getEntry(apiId, id)
  const mergedInput = { ...(entry.data || {}), ...(payload.data || {}) }
  const data = validateEntryAgainstSchema(contentType.schemaFields, mergedInput)

  const updated = await prisma.entry.update({
    where: { id: entry.id },
    data: {
      data,
      published: payload.published === undefined ? entry.published : Boolean(payload.published),
    },
  })

  return { entry: updated, contentType }
}

async function deleteEntry(apiId, id) {
  const { entry } = await getEntry(apiId, id)
  await prisma.entry.delete({ where: { id: entry.id } })
}

module.exports = {
  listEntries,
  createEntry,
  getEntry,
  updateEntry,
  deleteEntry,
}
