const { z } = require('zod')

const createDatasetSchema = z.object({
  name: z.string().min(2),
  visibility: z.enum(['PUBLIC', 'PRIVATE']).optional(),
})

const createTokenSchema = z.object({
  name: z.string().min(2),
  datasetId: z.string().optional(),
  scopes: z.record(z.any()).optional(),
})

module.exports = { createDatasetSchema, createTokenSchema }
