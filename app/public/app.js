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

  // Show preview
  const img = document.createElement('img');
  img.src = URL.createObjectURL(selectedFile);
  img.onload = () => URL.revokeObjectURL(img.src);
  preview.appendChild(img);
  
  // Show preview section
  preview.style.display = 'block';
});

uploadBtn.addEventListener('click', async () => {
  if (!selectedFile) return;

  uploadBtn.disabled = true;
  uploadBtn.innerHTML = '<span class="btn-icon">⏳</span> Analyzing...';
  result.textContent = '';

  const form = new FormData();
  form.append('image', selectedFile);

  try {
    const res = await fetch('/upload', { method: 'POST', body: form });
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || 'Upload failed');

    result.innerHTML = `<strong>Analysis Complete:</strong> ${data.filename}<br><em>${data.message}</em>`;
    result.parentElement.classList.add('show');
  } catch (err) {
    result.innerHTML = `<strong>Error:</strong> ${err.message}`;
    result.parentElement.classList.add('show');
  } finally {
    uploadBtn.disabled = false;
    uploadBtn.innerHTML = '<span class="btn-icon">🔍</span> Upload & Analyze';
  }
});
