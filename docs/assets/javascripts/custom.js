/* Custom JavaScript for jinpy-utils documentation */

// Initialize when the DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize math rendering with KaTeX
    if (typeof renderMathInElement !== 'undefined') {
        renderMathInElement(document.body, {
            delimiters: [
                {left: '$$', right: '$$', display: true},
                {left: '$', right: '$', display: false},
                {left: '\\(', right: '\\)', display: false},
                {left: '\\[', right: '\\]', display: true}
            ]
        });
    }

    // Enhanced code block functionality
    enhanceCodeBlocks();

    // Add copy feedback for code blocks
    addCopyFeedback();

    // Initialize tooltips for API documentation
    initializeTooltips();

    // Add scroll progress indicator
    addScrollProgress();
});

// Enhance code blocks with additional features
function enhanceCodeBlocks() {
    const codeBlocks = document.querySelectorAll('pre code');

    codeBlocks.forEach(block => {
        // Add language label
        const language = block.className.match(/language-(\w+)/);
        if (language && language[1]) {
            const label = document.createElement('div');
            label.className = 'code-language-label';
            label.textContent = language[1].toUpperCase();
            block.parentElement.insertBefore(label, block);
        }

        // Add line numbers for longer code blocks
        if (block.textContent.split('\n').length > 5) {
            block.classList.add('line-numbers');
        }
    });
}

// Add visual feedback for copy operations
function addCopyFeedback() {
    const copyButtons = document.querySelectorAll('[data-clipboard-target]');

    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Show feedback
            const originalText = button.textContent;
            button.textContent = 'Copied!';
            button.classList.add('copied');

            // Reset after 2 seconds
            setTimeout(() => {
                button.textContent = originalText;
                button.classList.remove('copied');
            }, 2000);
        });
    });
}

// Initialize tooltips for API documentation
function initializeTooltips() {
    // Add hover tooltips for API references
    const apiRefs = document.querySelectorAll('.doc-signature, .doc-heading');

    apiRefs.forEach(ref => {
        ref.addEventListener('mouseenter', function() {
            // Add custom tooltip logic here if needed
        });
    });
}

// Add scroll progress indicator
function addScrollProgress() {
    // Create progress bar element
    const progressBar = document.createElement('div');
    progressBar.className = 'scroll-progress';
    progressBar.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 0%;
        height: 3px;
        background-color: var(--md-primary-fg-color);
        z-index: 9999;
        transition: width 0.2s ease;
    `;

    document.body.appendChild(progressBar);

    // Update progress on scroll
    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset;
        const docHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrollPercent = (scrollTop / docHeight) * 100;

        progressBar.style.width = scrollPercent + '%';
    });
}

// Search enhancement
function enhanceSearch() {
    const searchInput = document.querySelector('[data-md-component="search-query"]');

    if (searchInput) {
        // Add search shortcuts
        document.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                searchInput.focus();
            }
        });

        // Add search history
        let searchHistory = JSON.parse(localStorage.getItem('search-history') || '[]');

        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && this.value.trim()) {
                searchHistory.unshift(this.value.trim());
                searchHistory = [...new Set(searchHistory)].slice(0, 10);
                localStorage.setItem('search-history', JSON.stringify(searchHistory));
            }
        });
    }
}

// Initialize enhanced search when search component is loaded
if (typeof md !== 'undefined' && md.search) {
    md.search.worker.then(() => {
        enhanceSearch();
    });
}

// Theme toggle enhancement
function enhanceThemeToggle() {
    const themeToggle = document.querySelector('[data-md-component="palette"]');

    if (themeToggle) {
        // Add theme transition
        document.documentElement.style.setProperty('--md-transition-duration', '0.3s');
    }
}

// Call theme enhancement
enhanceThemeToggle();

// Analytics and user experience tracking
function trackUserExperience() {
    // Track time spent on page
    let startTime = Date.now();

    window.addEventListener('beforeunload', function() {
        const timeSpent = Math.round((Date.now() - startTime) / 1000);

        // Send analytics if configured
        if (typeof gtag !== 'undefined') {
            gtag('event', 'page_view_duration', {
                'duration': timeSpent,
                'page_location': window.location.href
            });
        }
    });

    // Track scroll depth
    let maxScroll = 0;

    window.addEventListener('scroll', function() {
        const scrollPercent = Math.round(
            (window.pageYOffset / (document.documentElement.scrollHeight - window.innerHeight)) * 100
        );

        if (scrollPercent > maxScroll) {
            maxScroll = scrollPercent;
        }
    });

    // Send scroll depth on page unload
    window.addEventListener('beforeunload', function() {
        if (typeof gtag !== 'undefined') {
            gtag('event', 'scroll_depth', {
                'scroll_depth': maxScroll,
                'page_location': window.location.href
            });
        }
    });
}

// Initialize user experience tracking
trackUserExperience();
