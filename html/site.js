
document.addEventListener('DOMContentLoaded', () => {
    // Basic lang persistence if needed
    const currentLang = document.documentElement.lang;
    const langLinks = document.querySelectorAll('[data-lang-link]');
    
    langLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            const targetLang = link.getAttribute('data-lang-link');
            console.log('Switching to', targetLang);
        });
    });
});
