// Client-side form validation

document.addEventListener('DOMContentLoaded', function() {
    // Get all forms that need validation
    const forms = document.querySelectorAll('.needs-validation');

    // Add guardian button
    const addGuardianBtn = document.getElementById('add-guardian');
    if (addGuardianBtn) {
        addGuardianBtn.addEventListener('click', addGuardian);
    }

    // Loop over forms and prevent submission if invalid
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
    
    // Initialize guardian counter if registration form exists
    if (document.getElementById('registration-form')) {
        initGuardianCounter();
    }
    
    // Initialize signature pads if they exist
    initSignaturePads();
});

// Guardian management
let guardianCounter = 1;

function initGuardianCounter() {
    // Count existing guardian sections
    const guardianContainers = document.querySelectorAll('.guardian-container');
    guardianCounter = guardianContainers.length;
    
    // Set hidden input with guardian count
    document.getElementById('num_guardians').value = guardianCounter;
    
    // Add remove button functionality to existing guardians
    guardianContainers.forEach(container => {
        if (guardianCounter > 1) {
            const removeBtn = container.querySelector('.remove-guardian');
            if (removeBtn) {
                removeBtn.addEventListener('click', function() {
                    removeGuardian(this);
                });
            }
        }
    });
}

function addGuardian() {
    guardianCounter++;
    
    // Create new guardian container
    const guardianTemplate = document.getElementById('guardian-template');
    const newGuardian = guardianTemplate.cloneNode(true);
    newGuardian.id = `guardian-${guardianCounter}`;
    newGuardian.classList.remove('d-none');
    newGuardian.classList.add('guardian-container');
    
    // Update field names and IDs with new counter
    const fields = newGuardian.querySelectorAll('input, select');
    fields.forEach(field => {
        const oldName = field.getAttribute('name');
        const oldId = field.getAttribute('id');
        
        if (oldName) {
            field.setAttribute('name', oldName.replace('guardian_template_', `guardian_${guardianCounter}_`));
            field.removeAttribute('disabled');
            field.setAttribute('required', 'required');
        }
        
        if (oldId) {
            field.setAttribute('id', oldId.replace('guardian_template_', `guardian_${guardianCounter}_`));
        }
    });
    
    // Update labels
    const labels = newGuardian.querySelectorAll('label');
    labels.forEach(label => {
        const forAttr = label.getAttribute('for');
        if (forAttr) {
            label.setAttribute('for', forAttr.replace('guardian_template_', `guardian_${guardianCounter}_`));
        }
    });
    
    // Update title
    const title = newGuardian.querySelector('h4');
    if (title) {
        title.textContent = `Tuteur Légal ${guardianCounter}`;
    }
    
    // Add remove button functionality
    const removeBtn = newGuardian.querySelector('.remove-guardian');
    if (removeBtn) {
        removeBtn.addEventListener('click', function() {
            removeGuardian(this);
        });
        removeBtn.classList.remove('d-none');
    }
    
    // Add to the guardian section
    const guardiansSection = document.getElementById('guardians-section');
    guardiansSection.appendChild(newGuardian);
    
    // Update guardian count in hidden field
    document.getElementById('num_guardians').value = guardianCounter;
}

function removeGuardian(button) {
    const guardianContainer = button.closest('.guardian-container');
    guardianContainer.remove();
    
    guardianCounter--;
    
    // Update guardian count in hidden field
    document.getElementById('num_guardians').value = guardianCounter;
    
    // Re-number the remaining guardians
    const guardianContainers = document.querySelectorAll('.guardian-container');
    guardianContainers.forEach((container, index) => {
        if (index > 0) { // Skip the first guardian (template)
            const title = container.querySelector('h4');
            if (title) {
                title.textContent = `Tuteur Légal ${index + 1}`;
            }
        }
    });
}

// Signature Pad functionality
function initSignaturePads() {
    const signaturePads = document.querySelectorAll('.signature-pad');
    
    signaturePads.forEach(canvas => {
        const signaturePad = new SignaturePad(canvas, {
            backgroundColor: 'rgb(255, 255, 255)'
        });
        
        // Clear button functionality
        const clearBtn = document.querySelector(`[data-clear-signature="${canvas.id}"]`);
        if (clearBtn) {
            clearBtn.addEventListener('click', function() {
                signaturePad.clear();
                
                // Clear the hidden input value
                const hiddenInput = document.querySelector(`[data-signature-input="${canvas.id}"]`);
                if (hiddenInput) {
                    hiddenInput.value = '';
                }
            });
        }
        
        // Save signature to hidden input when form is submitted
        const form = canvas.closest('form');
        if (form) {
            form.addEventListener('submit', function() {
                if (!signaturePad.isEmpty()) {
                    const signatureData = signaturePad.toDataURL();
                    const hiddenInput = document.querySelector(`[data-signature-input="${canvas.id}"]`);
                    if (hiddenInput) {
                        hiddenInput.value = signatureData;
                    }
                }
            });
        }
    });
}

// File upload preview
function previewFile(input) {
    const preview = document.getElementById('file-preview');
    const file = input.files[0];
    const reader = new FileReader();
    
    reader.onload = function(e) {
        if (file.type.includes('image')) {
            preview.innerHTML = `<img src="${e.target.result}" class="img-fluid" alt="File preview">`;
        } else if (file.type === 'application/pdf') {
            preview.innerHTML = `<div class="alert alert-info">PDF file selected: ${file.name}</div>`;
        } else {
            preview.innerHTML = `<div class="alert alert-info">File selected: ${file.name}</div>`;
        }
    };
    
    if (file) {
        reader.readAsDataURL(file);
    }
}
