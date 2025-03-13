console.log("mathquill_init.js loaded.");

window.onerror = function(message, source, lineno, colno, error) {
    console.error("Global error:", message, "at", source, lineno + ":" + colno);
};

window.initMathQuill = function(retries) {
    retries = retries || 0;
    if (typeof MathQuill === 'undefined') {
        console.log("MathQuill is undefined on attempt:", retries);
        if (retries < 10) {
            setTimeout(function(){ window.initMathQuill(retries+1); }, 500);
            return;
        } else {
            console.error("MathQuill did not load.");
            return;
        }
    }
    var inputElem = document.getElementById('mathquill-input');
    if (!inputElem) {
        if (retries < 10) {
            setTimeout(function(){ window.initMathQuill(retries+1); }, 500);
        }
        return;
    }
    console.log("MathQuill is available and element found:", inputElem);
    var MQ = MathQuill.getInterface(2);
    
    window.mathField = MQ.MathField(inputElem, {
        spaceBehavesLikeTab: true,
        handlers: {
            edit: function() {
                // Get the overlay placeholder element
                var placeholder = inputElem.parentNode.querySelector('.mq-placeholder');
                // Toggle placeholder visibility depending on whether mathField is empty
                if (window.mathField.latex().trim() === "") {
                    placeholder.style.display = "block";
                } else {
                    placeholder.style.display = "none";
                }
            }
        }
    });
    // Clear any initial content.
    window.mathField.latex('');
    
    // After a short delay, set the placeholder attribute for the pseudo-element (if you're using that approach)
    setTimeout(function(){
        var editableField = inputElem.querySelector('.mq-editable-field');
        if(editableField) {
            editableField.setAttribute('data-placeholder', 'Type your equation here!');
        }
    }, 100);
    
    console.log("MathQuill initialized:", window.mathField);
    
    // Initial check: if the field is empty, ensure the overlay placeholder is visible.
    var placeholder = inputElem.parentNode.querySelector('.mq-placeholder');
    if (window.mathField.latex().trim() === "") {
        placeholder.style.display = "block";
    } else {
        placeholder.style.display = "none";
    }
};

window.addEventListener("load", function(){
    console.log("Window fully loaded - calling initMathQuill");
    window.initMathQuill();
});