# BreastScan Upload - Deployment Guide

This guide provides multiple deployment options for the BreastScan upload application.

## Prerequisites

- Node.js 18+ installed
- Git repository access
- Account on chosen deployment platform

## Deployment Options

### 1. Docker Deployment (Recommended)

#### Local Docker
```bash
# Build and run with Docker
docker build -t breastscan-app .
docker run -p 3000:3000 breastscan-app
```

#### Docker Compose
```bash
# Run with docker-compose
docker-compose up -d
```

### 2. Vercel (Serverless)

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. Deploy:
```bash
vercel --prod
```

**Note:** File uploads may have limitations on serverless platforms. Consider using cloud storage for production.

### 3. Render (Cloud Platform)

1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Use the provided `render.yaml` configuration
4. Deploy automatically on git push

### 4. Railway

1. Install Railway CLI:
```bash
npm install -g @railway/cli
```

2. Login and deploy:
```bash
railway login
railway init
railway up
```

### 5. Heroku

1. Install Heroku CLI
2. Create and deploy:
```bash
heroku create breastscan-upload
git push heroku main
```

### 6. DigitalOcean App Platform

1. Connect your GitHub repository
2. Configure build settings:
   - Build Command: `npm install`
   - Run Command: `npm start`
3. Deploy

### 7. Traditional VPS/Server

```bash
# Clone repository
git clone <your-repo-url>
cd app

# Install dependencies
npm install --production

# Start with PM2 (recommended)
npm install -g pm2
pm2 start server.js --name "breastscan-app"
pm2 startup
pm2 save

# Or start directly
npm start
```

## Environment Variables

Set these environment variables in your deployment platform:

- `NODE_ENV=production`
- `PORT=3000` (or platform-specific port)

## File Upload Considerations

### For Production Deployments:

1. **Cloud Storage Integration**: Consider integrating with AWS S3, Google Cloud Storage, or similar for file uploads
2. **File Size Limits**: Configure appropriate limits based on your platform
3. **Security**: Implement proper file validation and virus scanning
4. **Backup**: Ensure uploaded files are backed up regularly

### Recommended Cloud Storage Setup:

```javascript
// Example AWS S3 integration (replace multer disk storage)
const AWS = require('aws-sdk');
const multerS3 = require('multer-s3');

const s3 = new AWS.S3({
  accessKeyId: process.env.AWS_ACCESS_KEY_ID,
  secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
  region: process.env.AWS_REGION
});

const upload = multer({
  storage: multerS3({
    s3: s3,
    bucket: process.env.S3_BUCKET_NAME,
    key: function (req, file, cb) {
      cb(null, `uploads/${Date.now()}_${file.originalname}`);
    }
  })
});
```

## SSL/HTTPS

Most deployment platforms provide SSL certificates automatically. For custom domains:

1. **Cloudflare**: Free SSL with CDN
2. **Let's Encrypt**: Free SSL certificates
3. **Platform SSL**: Use platform-provided SSL

## Monitoring and Logging

### Recommended Tools:
- **Sentry**: Error tracking
- **LogRocket**: Session replay
- **New Relic**: Performance monitoring
- **Uptime Robot**: Uptime monitoring

## Performance Optimization

1. **Enable gzip compression**
2. **Use CDN for static assets**
3. **Implement caching headers**
4. **Optimize images**
5. **Use HTTP/2**

## Security Checklist

- [ ] HTTPS enabled
- [ ] File upload validation
- [ ] Rate limiting implemented
- [ ] CORS configured properly
- [ ] Security headers added
- [ ] Input sanitization
- [ ] Regular security updates

## Scaling Considerations

1. **Load Balancing**: Use multiple instances
2. **Database**: Add persistent storage
3. **Caching**: Implement Redis/Memcached
4. **CDN**: Use for static assets
5. **Microservices**: Split into smaller services

## Support

For deployment issues:
1. Check platform-specific documentation
2. Review application logs
3. Verify environment variables
4. Test locally first

## Quick Start Commands

```bash
# Development
npm run dev

# Production
npm start

# Docker
docker-compose up -d

# Vercel
vercel --prod
```