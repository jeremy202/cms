const path = require('path')
const express = require('express')
const cors = require('cors')
const helmet = require('helmet')
const morgan = require('morgan')
const rateLimit = require('express-rate-limit')

const { corsOrigin } = require('./config/env')
const authRoutes = require('./routes/auth.routes')
const contentTypeRoutes = require('./routes/contentType.routes')
const mediaRoutes = require('./routes/media.routes')
const dynamicRoutes = require('./routes/dynamic.routes')
const { notFound, errorHandler } = require('./middleware/error.middleware')

const app = express()

app.use(helmet())
app.use(
  cors({
    origin: corsOrigin,
    credentials: false,
  })
)
app.use(express.json({ limit: '2mb' }))
app.use(express.urlencoded({ extended: true }))
app.use(morgan('dev'))
app.use(
  '/api',
  rateLimit({
    windowMs: 60 * 1000,
    max: 300,
    standardHeaders: true,
    legacyHeaders: false,
  })
)

app.use('/uploads', express.static(path.resolve(process.cwd(), 'uploads')))

app.get('/health', (_req, res) => res.json({ ok: true }))
app.use('/api/auth', authRoutes)
app.use('/api/content-types', contentTypeRoutes)
app.use('/api/media', mediaRoutes)
app.use('/api', dynamicRoutes)

app.use(notFound)
app.use(errorHandler)

module.exports = { app }
