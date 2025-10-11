const uploadInput = document.getElementById('image-upload');
const uploadBtn = document.getElementById('upload-btn');
const preview = document.getElementById('preview');
const result = document.getElementById('result');

let selectedFile = null;

uploadInput.addEventListener('change', (e) => {
  const file = e.target.files && e.target.files[0];
  selectedFile = file || null;
  preview.innerHTML = '';
  result.textContent = '';

  if (!selectedFile) {
    uploadBtn.disabled = true;
    return;
  }

  uploadBtn.disabled = false;

  const img = document.createElement('img');
  img.src = URL.createObjectURL(selectedFile);
  img.onload = () => URL.revokeObjectURL(img.src);
  preview.appendChild(img);
});

uploadBtn.addEventListener('click', async () => {
  if (!selectedFile) return;

  uploadBtn.disabled = true;
  uploadBtn.textContent = 'Uploading...';
  result.textContent = '';

  const form = new FormData();
  form.append('image', selectedFile);

  try {
    const res = await fetch('/upload', { method: 'POST', body: form });
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || 'Upload failed');

    result.innerHTML = `<strong>Uploaded:</strong> ${data.filename}<br><em>${data.message}</em>`;
  } catch (err) {
    result.textContent = `Error: ${err.message}`;
  } finally {
    uploadBtn.disabled = false;
    uploadBtn.textContent = 'Upload & Analyze';
  }
});
