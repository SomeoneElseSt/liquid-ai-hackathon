document.addEventListener('DOMContentLoaded', () => {
  const imageUpload = document.getElementById('image-upload');
  const uploadBtn = document.getElementById('upload-btn');
  const preview = document.getElementById('preview');
  const resultDiv = document.getElementById('result');
  const loader = document.getElementById('loader');
  const progressBar = document.querySelector('.progress-bar');

  let selectedFile = null;

  imageUpload.addEventListener('change', () => {
    selectedFile = imageUpload.files[0];
    if (selectedFile) {
      uploadBtn.disabled = false;
      const reader = new FileReader();
      reader.onload = e => {
        preview.innerHTML = `<img src="${e.target.result}" alt="Image preview" />`;
      };
      reader.readAsDataURL(selectedFile);
      resultDiv.style.display = 'none';
      loader.style.display = 'none';
    } else {
      uploadBtn.disabled = true;
      preview.innerHTML = '';
    }
  });

  uploadBtn.addEventListener('click', () => {
    if (!selectedFile) return;

    // UI setup for loading
    uploadBtn.disabled = true;
    preview.classList.add('loading');
    resultDiv.style.display = 'none';
    loader.style.display = 'block';
    
    progressBar.style.transition = 'none';
    progressBar.style.width = '0%';

    // Force reflow to start animation correctly
    void progressBar.offsetWidth;

    // Start 60s fake loading animation
    progressBar.style.transition = 'width 60s linear';
    progressBar.style.width = '100%';

    const formData = new FormData();
    formData.append('image', selectedFile);

    const uploadPromise = fetch('/upload', {
        method: 'POST',
        body: formData,
    }).then(response => response.json());

    const timerPromise = new Promise(resolve => setTimeout(resolve, 60000));

    Promise.all([uploadPromise, timerPromise]).then(([result]) => {
        loader.style.display = 'none';
        uploadBtn.disabled = false;
        preview.classList.remove('loading');
        
        if (result.error) {
            resultDiv.innerHTML = `<p><strong>Error:</strong> ${result.error}</p>`;
            resultDiv.classList.add('error');
        } else {
            resultDiv.innerHTML = `
                <p><strong>File:</strong> ${result.filename}</p>
                <p><strong>Message:</strong> ${result.message}</p>
            `;
            resultDiv.classList.remove('error');
        }
        resultDiv.style.display = 'block';
    }).catch(() => {
        // This will catch fetch errors and is also delayed by the timer
        loader.style.display = 'none';
        uploadBtn.disabled = false;
        preview.classList.remove('loading');

        resultDiv.innerHTML = `<p><strong>Error:</strong> Could not connect to the server.</p>`;
        resultDiv.classList.add('error');
        resultDiv.style.display = 'block';
    });
  });
});
