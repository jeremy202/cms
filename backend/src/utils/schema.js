const slugify = require('slugify')

const allowedFieldTypes = new Set(['TEXT', 'NUMBER', 'BOOLEAN', 'MEDIA', 'RELATION', 'RICH_TEXT'])

function normalizeApiId(name) {
  return slugify(name, { lower: true, strict: true, trim: true })
}

function parseSchema(schemaInput) {
  const schema = typeof schemaInput === 'string' ? JSON.parse(schemaInput) : schemaInput
  if (!schema || typeof schema !== 'object' || !Array.isArray(schema.fields)) {
    throw new Error('Schema must include fields array')
  }

  const fields = schema.fields.map((f, idx) => {
    if (!f.name || !f.type) {
      throw new Error('Each field must include name and type')
    }
    const normalizedType = String(f.type).toUpperCase()
    if (!allowedFieldTypes.has(normalizedType)) {
      throw new Error(`Unsupported field type: ${f.type}`)
    }

    return {
      name: String(f.name),
      displayName: String(f.displayName || f.name),
      type: normalizedType,
      required: Boolean(f.required),
      unique: Boolean(f.unique),
      options: f.options || null,
      order: Number.isFinite(f.order) ? Number(f.order) : idx,
    }
  })

  return {
    fields,
    raw: {
      ...schema,
      fields,
    },
  }
}

function coerceValueByFieldType(type, value) {
  if (value === undefined) return value
  switch (type) {
    case 'NUMBER':
      if (value === null || value === '') return null
      if (Number.isNaN(Number(value))) throw new Error(`Field expects number, got ${value}`)
      return Number(value)
    case 'BOOLEAN':
      if (typeof value === 'boolean') return value
      if (typeof value === 'string') return ['true', '1', 'yes', 'on'].includes(value.toLowerCase())
      return Boolean(value)
    case 'MEDIA':
      return value
    case 'RELATION':
      return value
    default:
      return value == null ? null : String(value)
  }
}

function validateEntryAgainstSchema(fields, input) {
  const data = {}
  for (const field of fields) {
    const incoming = input[field.name]
    if (field.required && (incoming === undefined || incoming === null || incoming === '')) {
      throw new Error(`Field ${field.name} is required`)
    }
    if (incoming !== undefined) {
      data[field.name] = coerceValueByFieldType(field.type, incoming)
    }
  }

  for (const key of Object.keys(input)) {
    if (!fields.some((f) => f.name === key)) {
      data[key] = input[key]
    }
  }

  return data
}

module.exports = {
  normalizeApiId,
  parseSchema,
  validateEntryAgainstSchema,
}
