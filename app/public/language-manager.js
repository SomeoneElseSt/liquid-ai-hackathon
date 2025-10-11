class LanguageManager {
  constructor() {
    this.currentLanguage = this.getStoredLanguage() || 'en';
    this.translations = {};
    this.init();
  }

  async init() {
    await this.loadTranslations();
    this.updateUI();
    this.setupLanguageSwitcher();
  }

  getStoredLanguage() {
    return localStorage.getItem('breastscan-language') || 'en';
  }

  setStoredLanguage(lang) {
    localStorage.setItem('breastscan-language', lang);
  }

  async loadTranslations() {
    try {
      const [enTranslations, jaTranslations] = await Promise.all([
        fetch('/translations/en.json').then(res => res.json()),
        fetch('/translations/ja.json').then(res => res.json())
      ]);
      
      this.translations = {
        en: enTranslations,
        ja: jaTranslations
      };
    } catch (error) {
      console.error('Failed to load translations:', error);
    }
  }

  translate(key) {
    const keys = key.split('.');
    let value = this.translations[this.currentLanguage];
    
    for (const k of keys) {
      value = value?.[k];
    }
    
    return value || key;
  }

  switchLanguage(lang) {
    if (this.translations[lang]) {
      this.currentLanguage = lang;
      this.setStoredLanguage(lang);
      this.updateUI();
      this.updateDocumentLanguage();
      this.updateServerLanguagePreference();
    }
  }

  updateServerLanguagePreference() {
    // Update any existing fetch requests to include language preference
    const originalFetch = window.fetch;
    window.fetch = (url, options = {}) => {
      if (typeof url === 'string' && url.startsWith('/')) {
        const urlObj = new URL(url, window.location.origin);
        urlObj.searchParams.set('lang', this.currentLanguage);
        url = urlObj.toString();
      }
      return originalFetch(url, options);
    };
  }

  updateDocumentLanguage() {
    document.documentElement.lang = this.currentLanguage === 'ja' ? 'ja' : 'en';
  }

  updateUI() {
    // Update all elements with data-translate attribute
    const elements = document.querySelectorAll('[data-translate]');
    elements.forEach(element => {
      const key = element.getAttribute('data-translate');
      const translation = this.translate(key);
      
      if (element.tagName === 'INPUT' && element.type === 'submit') {
        element.value = translation;
      } else if (element.hasAttribute('placeholder')) {
        element.placeholder = translation;
      } else {
        element.textContent = translation;
      }
    });

    // Update title elements
    const titleElements = document.querySelectorAll('[data-translate-title]');
    titleElements.forEach(element => {
      const key = element.getAttribute('data-translate-title');
      element.title = this.translate(key);
    });

    // Update language switcher
    this.updateLanguageSwitcher();
  }

  setupLanguageSwitcher() {
    // Create language switcher if it doesn't exist
    let switcher = document.getElementById('language-switcher');
    if (!switcher) {
      switcher = this.createLanguageSwitcher();
      const nav = document.querySelector('.nav .links');
      if (nav) {
        nav.appendChild(switcher);
      }
    }
  }

  createLanguageSwitcher() {
    const switcher = document.createElement('div');
    switcher.id = 'language-switcher';
    switcher.className = 'language-switcher';
    
    const button = document.createElement('button');
    button.className = 'language-btn';
    button.innerHTML = `
      <span class="language-icon">🌐</span>
    `;
    button.title = 'Language / 言語'; // Tooltip for accessibility
    
    const dropdown = document.createElement('div');
    dropdown.className = 'language-dropdown';
    dropdown.innerHTML = `
      <a href="#" data-lang="en" class="language-option">
        <span class="flag">🇺🇸</span>
        <span data-translate="language.english">English</span>
      </a>
      <a href="#" data-lang="ja" class="language-option">
        <span class="flag">🇯🇵</span>
        <span data-translate="language.japanese">日本語</span>
      </a>
    `;
    
    switcher.appendChild(button);
    switcher.appendChild(dropdown);
    
    // Add event listeners
    button.addEventListener('click', (e) => {
      e.preventDefault();
      dropdown.classList.toggle('show');
    });
    
    dropdown.addEventListener('click', (e) => {
      e.preventDefault();
      const lang = e.target.closest('[data-lang]')?.getAttribute('data-lang');
      if (lang) {
        this.switchLanguage(lang);
        dropdown.classList.remove('show');
      }
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
      if (!switcher.contains(e.target)) {
        dropdown.classList.remove('show');
      }
    });
    
    return switcher;
  }

  updateLanguageSwitcher() {
    const switcher = document.getElementById('language-switcher');
    if (switcher) {
      const currentOption = switcher.querySelector(`[data-lang="${this.currentLanguage}"]`);
      const otherOption = switcher.querySelector(`[data-lang="${this.currentLanguage === 'en' ? 'ja' : 'en'}"]`);
      
      if (currentOption && otherOption) {
        currentOption.classList.add('active');
        otherOption.classList.remove('active');
      }
    }
  }
}

// Initialize language manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.languageManager = new LanguageManager();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = LanguageManager;
}
