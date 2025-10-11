document.addEventListener('DOMContentLoaded', () => {
    const hero = document.querySelector('.hero-image');
    const heroContent = document.querySelector('.hero-inner');
    const title = hero.querySelector('h1');
    const tagline = hero.querySelector('.tag');
    
    // Get all content sections that should animate
    const contentSections = document.querySelectorAll('.presentation-content h2, .presentation-content h3, .presentation-content p');

    let lastScrollPosition = window.pageYOffset;
    let scrollingDown = true;

    // Calculate when an element is in view
    function isElementInViewport(el) {
        const rect = el.getBoundingClientRect();
        const threshold = 100; // Increased threshold for earlier trigger
        return rect.top < window.innerHeight - threshold && rect.bottom > threshold;
    }

    // Handle element visibility and animations with scroll direction
    function handleContentAnimation(el) {
        if (isElementInViewport(el)) {
            el.classList.add('animate-in');
            el.classList.toggle('scrolling-down', scrollingDown);
            el.classList.toggle('scrolling-up', !scrollingDown);
        } else {
            el.classList.remove('animate-in', 'scrolling-down', 'scrolling-up');
        }
    }

    function handleScroll() {
        // Determine scroll direction
        const currentScroll = window.pageYOffset;
        scrollingDown = currentScroll > lastScrollPosition;
        lastScrollPosition = currentScroll;

        // Hero parallax effect
        if (isElementInViewport(hero)) {
            const scrolled = currentScroll;
            const heroHeight = hero.offsetHeight;
            const scrollProgress = Math.min(scrolled / heroHeight, 1);

            // Parallax effect for hero content
            if (scrollProgress <= 1) {
                heroContent.style.transform = `translateY(${scrolled * 0.4}px)`;
                heroContent.style.opacity = Math.max(0, 1 - (scrollProgress * 1.5));
                
                const scale = 1 - (scrollProgress * 0.15);
                title.style.transform = `scale(${scale})`;
                
                tagline.style.transform = `translateY(${scrolled * 0.5}px)`;
                tagline.style.opacity = Math.max(0, 1 - (scrollProgress * 2));
            }
        }

        // Check and animate content sections
        contentSections.forEach(handleContentAnimation);
    }

    // Add initial classes to content sections
    contentSections.forEach(el => {
        el.classList.add('animate-on-scroll');
    });

    // Throttle scroll events for better performance
    let ticking = false;
    window.addEventListener('scroll', () => {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                handleScroll();
                ticking = false;
            });
            ticking = true;
        }
    });

    // Initialize positions
    handleScroll();
});