const bcrypt = require('bcryptjs')
const { prisma } = require('../config/prisma')

async function registerUser({ email, password, role = 'EDITOR' }) {
  const existing = await prisma.user.findUnique({ where: { email } })
  if (existing) {
    throw new Error('Email already in use')
  }

  const passwordHash = await bcrypt.hash(password, 12)
  const user = await prisma.user.create({
    data: {
      email,
      passwordHash,
      role,
    },
  })

  return user
}

async function loginUser({ email, password }) {
  const user = await prisma.user.findUnique({ where: { email } })
  if (!user) throw new Error('Invalid credentials')

  const valid = await bcrypt.compare(password, user.passwordHash)
  if (!valid) throw new Error('Invalid credentials')

  return user
}

module.exports = { registerUser, loginUser }
