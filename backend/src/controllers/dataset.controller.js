const {
  listDatasets,
  createDataset,
  createDeliveryToken,
  listDeliveryTokens,
  revokeDeliveryToken,
} = require('../services/dataset.service')
const { createDatasetSchema, createTokenSchema } = require('../validators/dataset.validator')

async function listAll(_req, res, next) {
  try {
    const datasets = await listDatasets()
    return res.json(datasets)
  } catch (err) {
    return next(err)
  }
}

async function createOne(req, res, next) {
  try {
    const payload = createDatasetSchema.parse(req.body)
    const dataset = await createDataset(payload)
    return res.status(201).json(dataset)
  } catch (err) {
    return next(err)
  }
}

async function listTokens(_req, res, next) {
  try {
    const tokens = await listDeliveryTokens()
    return res.json(tokens)
  } catch (err) {
    return next(err)
  }
}

async function createToken(req, res, next) {
  try {
    const payload = createTokenSchema.parse(req.body)
    const token = await createDeliveryToken(req.user.sub, payload)
    return res.status(201).json(token)
  } catch (err) {
    return next(err)
  }
}

async function revokeToken(req, res, next) {
  try {
    await revokeDeliveryToken(req.params.id)
    return res.status(204).send()
  } catch (err) {
    return next(err)
  }
}

module.exports = {
  listAll,
  createOne,
  listTokens,
  createToken,
  revokeToken,
}
