// This script controls the stick figure animations
document.addEventListener('DOMContentLoaded', function() {
    // Wait for DOM to be fully loaded
    setTimeout(() => {
        const robot = document.getElementById("robot");
        const eyes = document.querySelectorAll(".eye");
        const mouth = document.querySelector(".mouth");
        const navLinks = document.querySelectorAll(".nav-link");
        let isHoveringNavLink = false;
        let isHoveringRobot = false;

        // Make eyes follow mouse cursor when not hovering over the robot
        document.addEventListener("mousemove", (event) => {
            if (robot && eyes && !isHoveringRobot) {
                eyes.forEach(eye => {
                    const eyeRect = eye.getBoundingClientRect();
                    const eyeX = eyeRect.left + eyeRect.width / 2;
                    const eyeY = eyeRect.top + eyeRect.height / 2;
                    const angle = Math.atan2(event.clientY - eyeY, event.clientX - eyeX);
                    const offsetX = Math.cos(angle) * 3;
                    const offsetY = Math.sin(angle) * 3;
                    eye.style.transition = "transform 0.1s ease-out";
                    eye.style.transform = `translate(${offsetX}px, ${offsetY}px)`;
                });
            }
        });

        // Make mouth open when hovering over navbar links (complete oval)
        if (navLinks && mouth) {
            navLinks.forEach(link => {
                link.addEventListener('mouseenter', () => {
                    isHoveringNavLink = true;
                    // Complete oval for navbar hover
                    mouth.style.height = '12px';
                    mouth.style.borderRadius = '50%';
                });

                link.addEventListener('mouseleave', () => {
                    isHoveringNavLink = false;
                    // Only close mouth if not hovering over the robot itself
                    if (!isHoveringRobot) {
                        mouth.style.height = '2px';
                        mouth.style.borderRadius = '5px';
                    } else {
                        // Smile shape when hovering on robot
                        mouth.style.height = '10px';
                        mouth.style.borderRadius = '50% / 0 0 100% 100%';
                    }
                });
            });
            
            // Control mouth and eyes when hovering over robot itself
            if (robot) {
                robot.addEventListener('mouseenter', () => {
                    isHoveringRobot = true;
                    
                    // Center the eyes
                    eyes.forEach(eye => {
                        eye.style.transition = "transform 0.2s ease-in-out";
                        eye.style.transform = "translate(0, 0)";
                    });
                    
                    // Smile shape for robot hover
                    mouth.style.height = '10px';
                    mouth.style.borderRadius = '50% / 0 0 100% 100%';
                });
                
                robot.addEventListener('mouseleave', () => {
                    isHoveringRobot = false;
                    
                    // Only change mouth if not hovering over a nav link
                    if (!isHoveringNavLink) {
                        mouth.style.height = '2px';
                        mouth.style.borderRadius = '5px';
                    } else {
                        // Complete oval for navbar hover
                        mouth.style.height = '12px';
                        mouth.style.borderRadius = '50%';
                    }
                });
            }
        }
    }, 500); // Small delay to ensure elements are loaded
});