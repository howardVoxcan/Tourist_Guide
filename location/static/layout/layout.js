// Simple JavaScript for tab switching functionality
document.addEventListener('DOMContentLoaded', function() {
    const tabButtons = document.querySelectorAll('.tab-button');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            tabButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // In a real implementation, you would also need to show the correct tab content
        });
    });
    
    // Implement sticky header on scroll
    window.addEventListener('scroll', function() {
        const header = document.querySelector('header');
        header.classList.toggle('sticky', window.scrollY > 0);
    });
    
    // Make search button interactive
    const searchButton = document.querySelector('.search-button');
    searchButton.addEventListener('click', function() {
        alert('Search functionality would be implemented in a real application.');
    });
    
    // Add hover effects to nav items
    const navLinks = document.querySelectorAll('.nav-tabs a');
    navLinks.forEach(link => {
        link.addEventListener('mouseenter', function() {
            this.style.transition = 'all 0.3s ease';
        });
    });
    
    // Add responsiveness to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('click', function() {
            // In a real app, this would navigate to the detail page
            console.log('Card clicked!');
        });
    });
});