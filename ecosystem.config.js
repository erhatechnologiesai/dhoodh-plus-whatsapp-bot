module.exports = {
  apps: [
    {
      name: 'dhoodh-backend',
      cwd: './backend',
      script: 'python3',
      args: '-m uvicorn app.main:app --host 0.0.0.0 --port 8000',
      autorestart: true,
      max_restarts: 10,
      restart_delay: 3000,
      env: {
        PYTHONUNBUFFERED: '1'
      }
    },
    {
      name: 'dhoodh-gateway',
      cwd: './whatsapp-gateway',
      script: 'gateway.js',
      autorestart: true,
      max_restarts: 10,
      restart_delay: 4000,
      env: {
        PORT: 3001
      }
    },
    {
      name: 'dhoodh-frontend',
      cwd: './frontend',
      script: 'npm',
      args: 'start',
      autorestart: true,
      env: {
        PORT: 3000,
        NODE_ENV: 'production'
      }
    }
  ]
};
