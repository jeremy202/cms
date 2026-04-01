const jwt = require('jsonwebtoken')
const { jwtSecret } = require('../config/env')

function signToken(user) {
  return jwt.sign({ sub: user.id, role: user.role, email: user.email }, jwtSecret, { expiresIn: '12h' })
}

function verifyToken(token) {
  return jwt.verify(token, jwtSecret)
}

module.exports = { signToken, verifyToken }
