const { z } = require('zod')

const fieldSchema = z.object({
  name: z.string().min(1),
  displayName: z.string().optional(),
  type: z.enum(['TEXT', 'NUMBER', 'BOOLEAN', 'MEDIA', 'RELATION', 'RICH_TEXT']),
  required: z.boolean().optional(),
  unique: z.boolean().optional(),
  options: z.record(z.any()).optional(),
  order: z.number().optional(),
})

const createContentTypeSchema = z.object({
  name: z.string().min(2),
  apiId: z.string().optional(),
  description: z.string().optional(),
  schema: z.object({ fields: z.array(fieldSchema).min(1) }),
})

module.exports = { createContentTypeSchema }
