const express = require('express');
const path = require('path');
const fs = require('fs');
const multer = require('multer');

const app = express();
const port = process.env.PORT || 3000;

// Ensure uploads directory exists
const uploadsDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

// Multer storage configuration
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, uploadsDir),
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname);
    const base = path.basename(file.originalname, ext).replace(/\s+/g, '_');
    cb(null, `${Date.now()}_${base}${ext}`);
  }
});

const upload = multer({
  storage,
  fileFilter: (req, file, cb) => {
    // Accept only image files
    if (!file.mimetype.startsWith('image/')) return cb(new Error('Only image files are allowed'));
    cb(null, true);
  }
});

// Serve static frontend files from /public
app.use(express.static(path.join(__dirname, 'public')));

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Endpoint to receive an uploaded image. Field name: 'image'
app.post('/upload', upload.single('image'), (req, res) => {
  if (!req.file) return res.status(400).json({ error: 'No file uploaded' });

  // Placeholder response: real AI classification will be implemented later
  res.json({
    filename: req.file.filename,
    message: 'File received. AI classification not implemented yet. This is a placeholder response.',
    prediction: null
  });
});

// Basic error handler for upload errors
app.use((err, req, res, next) => {
  if (err) {
    return res.status(400).json({ error: err.message || 'Server error' });
  }
  next();
});

app.listen(port, () => {
  console.log(`Server is running at http://localhost:${port}`);
});