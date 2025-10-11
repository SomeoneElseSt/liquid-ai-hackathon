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
  uploadBtn.innerHTML = `<span class="btn-icon">⏳</span> ${langManager.translate('app.analyzing')}`;
  result.textContent = '';

  const form = new FormData();
  form.append('image', selectedFile);

  try {
    const uploadUrl = `/upload?lang=${langManager.currentLanguage}`;
    const res = await fetch(uploadUrl, { method: 'POST', body: form });
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || langManager.translate('app.upload_failed'));

    // Use server message if available, otherwise use translated message
    const message = data.message || langManager.translate('app.analysis_complete');
    result.innerHTML = `<strong>${langManager.translate('app.analysis_complete')}</strong> ${data.filename}<br><em>${message}</em>`;
    result.parentElement.classList.add('show');
  } catch (err) {
    result.innerHTML = `<strong>${langManager.translate('app.error')}</strong> ${err.message}`;
    result.parentElement.classList.add('show');
  } finally {
    uploadBtn.disabled = false;
    uploadBtn.innerHTML = `<span class="btn-icon">🔍</span> ${langManager.translate('app.analyze_button')}`;
  }
});
