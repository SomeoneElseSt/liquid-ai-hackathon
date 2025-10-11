# Frontend (BreastScan demo)

Minimal Express frontend for uploading breast exam images to a placeholder AI classification endpoint.

Quick start

```bash
cd app
npm install
npm start
# open http://localhost:3000
```

Notes

- This is a demo landing page with an upload button. Uploaded images are saved into `uploads/`.
- No AI inference is implemented yet; server returns a placeholder JSON response.
- For production use with medical data, add proper security, authentication, logging, and HIPAA-compliant storage.
