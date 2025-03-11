// Global robot controller that works across all pages
(function() {
    console.log('Robot script loaded');
    
    // Track initialization state globally
    let isInitialized = false;
    let animationFrameId = null;
    let pollingInterval = null;
    
    // Initialize immediately and also when DOM is fully loaded
    initRobot();
    document.addEventListener('DOMContentLoaded', initRobot);
    
    // Initialize when route changes in SPA
    function setupNavigationListeners() {
        // Monitor history API changes
        const originalPushState = window.history.pushState;
        window.history.pushState = function() {
            originalPushState.apply(window.history, arguments);
            console.log('Route changed via pushState - checking robot');
            cleanupRobot(); // Clean up before re-initializing
            setTimeout(initRobot, 50); // Slight delay to ensure DOM updates
        };
        
        const originalReplaceState = window.history.replaceState;
        window.history.replaceState = function() {
            originalReplaceState.apply(window.history, arguments);
            console.log('Route changed via replaceState - checking robot');
            cleanupRobot(); // Clean up before re-initializing
            setTimeout(initRobot, 50); // Slight delay to ensure DOM updates
        };
        
        // Handle back/forward navigation
        window.addEventListener('popstate', function() {
            console.log('Route changed via popstate - checking robot');
            cleanupRobot(); // Clean up before re-initializing
            setTimeout(initRobot, 50); // Slight delay to ensure DOM updates
        });
    }
    
    // Cleanup function to reset state before re-initializing
    function cleanupRobot() {
        console.log('Cleaning up robot functionality');
        isInitialized = false;
        
        // Cancel any animation frame
        if (animationFrameId) {
            window.cancelAnimationFrame(animationFrameId);
            animationFrameId = null;
        }
        
        // Clear any polling interval
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
        
        // Reset any mouth styling that might be lingering
        const mouth = document.querySelector('.mouth');
        if (mouth) {
            mouth.style.width = '40%';
            mouth.style.height = '2px';
            mouth.style.borderRadius = '0';
            mouth.style.bottom = '30%';
        }
    }
    
    // Set up navigation monitoring
    setupNavigationListeners();
    
    // Main robot initialization function - will be called multiple times
    function initRobot() {
        console.log('Initializing robot functionality');
        
        // Create a function to repeatedly check for robot elements
        function setupRobotFunctionality() {
            // If already initialized, don't do it again
            if (isInitialized) {
                console.log('Robot already initialized, skipping');
                return true;
            }
            
            // Find all robot elements
            const robot = document.getElementById('robot');
            const mouth = document.querySelector('.mouth');
            
            // If any elements are missing, retry later
            if (!robot || !mouth) {
                console.log('Robot elements not found, will retry');
                return false;
            }
            
            console.log('Robot elements found, setting up functionality');
            
            // Show/hide robot based on page
            if (window.location.pathname.includes('sandbox')) {
                robot.style.display = 'block';
            } else {
                robot.style.display = 'none';
                return true; // We're done if not on sandbox page
            }
            
            // Explicitly set initial mouth styling
            mouth.style.width = '40%';
            mouth.style.height = '2px';
            mouth.style.borderRadius = '0';
            mouth.style.bottom = '30%';
            mouth.style.transition = 'all 0.3s ease'; // Smoother transition
            
            // Create clean smile function with more pronounced smile
            function makeSmile() {
                // Get a fresh reference to the mouth element
                const currentMouth = document.querySelector('.mouth');
                if (!currentMouth) return;
                
                // Apply smile styles
                currentMouth.style.width = '60%';
                currentMouth.style.height = '3px'; // Slightly thicker
                currentMouth.style.borderRadius = '0 0 100px 100px'; // More curved smile
                currentMouth.style.bottom = '25%';
            }
            
            // Create clean neutral mouth function
            function makeNeutral() {
                // Get a fresh reference to the mouth element
                const currentMouth = document.querySelector('.mouth');
                if (!currentMouth) return;
                
                // Reset to neutral state
                currentMouth.style.width = '40%';
                currentMouth.style.height = '2px';
                currentMouth.style.borderRadius = '0';
                currentMouth.style.bottom = '30%';
            }
            
            // Remove any existing event listeners to prevent duplicates
            robot.removeEventListener('mouseenter', makeSmile);
            robot.removeEventListener('mouseleave', makeNeutral);
            
            // Add event listeners to handle hover state
            robot.addEventListener('mouseenter', makeSmile);
            robot.addEventListener('mouseleave', makeNeutral);
            
            // Mark as initialized
            isInitialized = true;
            return true;
        }
        
        // Try immediately
        if (!setupRobotFunctionality()) {
            // If it fails, retry with polling
            let attempts = 0;
            const maxAttempts = 50; // Try for 5 seconds
            
            pollingInterval = setInterval(function() {
                attempts++;
                if (setupRobotFunctionality() || attempts >= maxAttempts) {
                    clearInterval(pollingInterval);
                    pollingInterval = null;
                    console.log(attempts < maxAttempts ? 
                        'Robot functionality initialized after retries' : 
                        'Failed to initialize robot after max attempts');
                }
            }, 100);
        }
    }
})();
