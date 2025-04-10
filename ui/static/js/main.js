/**
 * Main JavaScript for Job Application Agent
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Flash message auto-dismiss
    const flashMessages = document.querySelectorAll('.alert-dismissible');
    flashMessages.forEach(function(alert) {
        setTimeout(function() {
            const closeButton = alert.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        }, 5000);
    });

    // Add smooth scrolling to all links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Confirmation dialogs
    document.querySelectorAll('[data-confirm]').forEach(function(element) {
        element.addEventListener('click', function(e) {
            if (!confirm(this.getAttribute('data-confirm'))) {
                e.preventDefault();
            }
        });
    });

    // AJAX form submission helper
    document.querySelectorAll('form[data-ajax="true"]').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const submitButton = form.querySelector('[type="submit"]');
            const originalText = submitButton.innerHTML;
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
            
            fetch(form.action, {
                method: form.method,
                body: new FormData(form),
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.redirect) {
                    window.location.href = data.redirect;
                } else if (data.message) {
                    showNotification(data.message, data.status || 'success');
                    if (data.status !== 'error') {
                        form.reset();
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('An error occurred. Please try again.', 'error');
            })
            .finally(() => {
                submitButton.disabled = false;
                submitButton.innerHTML = originalText;
            });
        });
    });
});

// Show notification function
function showNotification(message, type = 'info') {
    const notificationArea = document.getElementById('notification-area') || createNotificationArea();
    
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    notification.role = 'alert';
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    notificationArea.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 150);
    }, 5000);
}

// Create notification area if it doesn't exist
function createNotificationArea() {
    const notificationArea = document.createElement('div');
    notificationArea.id = 'notification-area';
    notificationArea.className = 'position-fixed top-0 end-0 p-3';
    notificationArea.style.zIndex = '1050';
    document.body.appendChild(notificationArea);
    return notificationArea;
} 