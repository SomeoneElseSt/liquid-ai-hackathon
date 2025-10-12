const uploadInput = document.getElementById('image-upload');
const uploadBtn = document.getElementById('upload-btn');
const preview = document.getElementById('preview');
const result = document.getElementById('result');

let selectedFile = null;

// Enable button by default
uploadBtn.disabled = false;

uploadInput.addEventListener('change', (e) => {
  const file = e.target.files && e.target.files[0];
  selectedFile = file || null;
  preview.innerHTML = '';
  result.innerHTML = '';

  uploadBtn.disabled = false;

  if (selectedFile) {
    // Show preview
    const img = document.createElement('img');
    img.src = URL.createObjectURL(selectedFile);
    img.onload = () => URL.revokeObjectURL(img.src);
    preview.appendChild(img);
  }
});

uploadBtn.addEventListener('click', async () => {
  if (!selectedFile) {
    result.innerHTML = '<strong>Please select an image first</strong>';
    return;
  }

  uploadBtn.disabled = true;
  uploadBtn.textContent = 'Analyzing...';
  result.innerHTML = '';

  const form = new FormData();
  form.append('image', selectedFile);

  try {
    const res = await fetch('/upload', { method: 'POST', body: form });
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || 'Upload failed');

    result.innerHTML = `<strong>Analysis Complete:</strong> ${data.filename}<br><em>${data.message || 'Image analyzed successfully'}</em>`;
  } catch (err) {
    result.innerHTML = `<strong>Error:</strong> ${err.message}`;
  } finally {
    uploadBtn.disabled = false;
    uploadBtn.textContent = 'Analyze Image';
  }
});
