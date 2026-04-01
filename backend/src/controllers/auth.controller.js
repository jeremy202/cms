const { registerSchema, loginSchema } = require('../validators/auth.validator')
const { registerUser, loginUser } = require('../services/auth.service')
const { signToken } = require('../utils/jwt')

async function register(req, res, next) {
  try {
    const input = registerSchema.parse(req.body)
    const user = await registerUser(input)
    const token = signToken(user)

    return res.status(201).json({
      token,
      user: {
        id: user.id,
        email: user.email,
        role: user.role,
      },
    })
  } catch (err) {
    if (err.message === 'Email already in use') {
      return res.status(409).json({ error: err.message })
    }
    return next(err)
  }
}

async function login(req, res, next) {
  try {
    const input = loginSchema.parse(req.body)
    const user = await loginUser(input)
    const token = signToken(user)

    return res.json({
      token,
      user: {
        id: user.id,
        email: user.email,
        role: user.role,
      },
    })
  } catch (err) {
    if (err.message === 'Invalid credentials') {
      return res.status(401).json({ error: err.message })
    }
    return next(err)
  }
}

function me(req, res) {
  return res.json({ user: req.user })
}

module.exports = { register, login, me }
