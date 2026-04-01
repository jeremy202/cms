require('dotenv').config()

const { app } = require('./app')
const { port } = require('./config/env')

app.listen(port, () => {
  console.log(`CMS backend listening on http://localhost:${port}`)
})
