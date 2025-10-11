document.addEventListener('DOMContentLoaded', () => {
    // Wrap page content in transition container
    const main = document.querySelector('main');
    main.classList.add('page-content');

    // Handle link clicks for page transitions
    document.querySelectorAll('a').forEach(link => {
        // Only handle internal links
        if (link.href && link.href.startsWith(window.location.origin)) {
            link.addEventListener('click', e => {
                e.preventDefault();
                const target = e.currentTarget.href;
                
                // Start page exit animation
                main.classList.add('leaving');
                
                // Wait for animation to complete before navigation
                setTimeout(() => {
                    window.location.href = target;
                }, 400); // Match the pageLeave animation duration
            });
        }
    });
});