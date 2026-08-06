document.documentElement.classList.add('js');

document.addEventListener('DOMContentLoaded', function () {
    const header = document.querySelector('.site-header');
    const progressBar = document.querySelector('.scroll-progress');

    function updateScrollState() {
        const pageHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrollAmount = window.scrollY;

        if (header) {
            header.classList.toggle('is-scrolled', scrollAmount > 10);
        }

        if (progressBar && pageHeight > 0) {
            const scrollPercent = (scrollAmount / pageHeight) * 100;
            progressBar.style.width = scrollPercent + '%';
        }
    }

    updateScrollState();
    window.addEventListener('scroll', updateScrollState, {passive: true});
    window.addEventListener('resize', updateScrollState);

    const currentPath = window.location.pathname;
    const navigationLinks = document.querySelectorAll('.site-nav a');

    navigationLinks.forEach(function (link) {
        const linkPath = new URL(link.href).pathname;

        if (linkPath === currentPath) {
            link.classList.add('is-current');
        }
    });

    const revealItems = document.querySelectorAll('.reveal');
    const reducedMotion = window.matchMedia(
        '(prefers-reduced-motion: reduce)'
    ).matches;

    if (reducedMotion || !('IntersectionObserver' in window)) {
        revealItems.forEach(function (item) {
            item.classList.add('is-visible');
        });
    } else {
        const revealObserver = new IntersectionObserver(function (entries, observer) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    observer.unobserve(entry.target);
                }
            });
        }, {threshold: 0.12});

        revealItems.forEach(function (item, index) {
            if (item.classList.contains('post-card')) {
                item.style.transitionDelay = (index % 2) * 90 + 'ms';
            }

            revealObserver.observe(item);
        });
    }

    document.querySelectorAll('textarea').forEach(function (textarea) {
        function resizeTextarea() {
            textarea.style.height = 'auto';
            textarea.style.height = textarea.scrollHeight + 'px';
        }

        textarea.addEventListener('input', resizeTextarea);
        resizeTextarea();
    });

    document.querySelectorAll('.button').forEach(function (button) {
        button.addEventListener('click', function (event) {
            const ripple = document.createElement('span');
            const buttonBox = button.getBoundingClientRect();

            ripple.className = 'button-ripple';
            ripple.style.left = event.clientX - buttonBox.left + 'px';
            ripple.style.top = event.clientY - buttonBox.top + 'px';
            button.appendChild(ripple);

            window.setTimeout(function () {
                ripple.remove();
            }, 550);
        });
    });
});
