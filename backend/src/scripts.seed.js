require('dotenv').config()

const bcrypt = require('bcryptjs')
const { prisma } = require('./config/prisma')

async function main() {
  const email = process.env.ADMIN_EMAIL || 'admin@example.com'
  const password = process.env.ADMIN_PASSWORD || 'admin12345'

  const existing = await prisma.user.findUnique({ where: { email } })
  if (!existing) {
    const passwordHash = await bcrypt.hash(password, 12)
    await prisma.user.create({
      data: {
        email,
        passwordHash,
        role: 'ADMIN',
      },
    })
    console.log('Created admin user:', email)
  } else {
    console.log('Admin already exists:', email)
  }

  const dataset = await prisma.dataset.findUnique({ where: { name: 'production' } })
  if (!dataset) {
    await prisma.dataset.create({
      data: {
        name: 'production',
        visibility: 'PUBLIC',
      },
    })
    console.log('Created default dataset: production')
  } else {
    console.log('Dataset already exists: production')
  }
}

main()
  .catch((err) => {
    console.error(err)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
