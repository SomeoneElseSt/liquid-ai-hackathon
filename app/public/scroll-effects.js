document.addEventListener('DOMContentLoaded', () => {
    const hero = document.querySelector('.hero-image');
    const heroContent = document.querySelector('.hero-inner');
    const title = hero.querySelector('h1');
    const tagline = hero.querySelector('.tag');

    // Calculate when the hero section is in view
    function isElementInViewport(el) {
        const rect = el.getBoundingClientRect();
        return rect.bottom > 0 && rect.top < window.innerHeight;
    }

    function handleScroll() {
        if (!isElementInViewport(hero)) return;

        const scrolled = window.pageYOffset;
        const heroHeight = hero.offsetHeight;
        const scrollProgress = Math.min(scrolled / heroHeight, 1);

        // Parallax effect for hero content
        if (scrollProgress <= 1) {
            // Move content up slower than scroll speed
            heroContent.style.transform = `translateY(${scrolled * 0.4}px)`;
            
            // Fade out content as we scroll
            const opacity = Math.max(0, 1 - (scrollProgress * 1.5));
            heroContent.style.opacity = opacity;
            
            // Scale down title slightly
            const scale = 1 - (scrollProgress * 0.15);
            title.style.transform = `scale(${scale})`;
            
            // Move tagline slightly faster for depth
            tagline.style.transform = `translateY(${scrolled * 0.5}px)`;
            tagline.style.opacity = Math.max(0, 1 - (scrollProgress * 2));
        }
    }

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