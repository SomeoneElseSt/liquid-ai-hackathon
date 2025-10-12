document.addEventListener('DOMContentLoaded', () => {
  const imageUpload = document.getElementById('image-upload');
  const uploadBtn = document.getElementById('upload-btn'); // Vercel 
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

    const timerPromise = new Promise(resolve => setTimeout(resolve, 60000));

    timerPromise.then(() => {
        const currentLanguage = window.languageManager.currentLanguage || 'en';
        const messages = {
            en: 'File received. AI classification not implemented yet. This is a placeholder response.',
            ja: 'ファイルを受信しました。AI分類はまだ実装されていません。これはプレースホルダー応答です。'
        };

        const result = {
            filename: selectedFile.name,
            message: messages[currentLanguage] || messages.en,
            prediction: null,
            language: currentLanguage
        };
        
        loader.style.display = 'none';
        uploadBtn.disabled = false;
        preview.classList.remove('loading');
        
        resultDiv.innerHTML = `
            <p><strong>File:</strong> ${result.filename}</p>
            <p><strong>Message:</strong> ${result.message}</p>
        `;
        resultDiv.classList.remove('error');
        resultDiv.style.display = 'block';
    });
  });
});
