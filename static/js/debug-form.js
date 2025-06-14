// Form debug script
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('registration-form');
    if (form) {
        console.log('Formulaire trouvé et prêt pour le debug');
        
        form.addEventListener('submit', function(event) {
            console.log('Formulaire soumis!');
            console.log('Validité du formulaire:', form.checkValidity());
            
            // Log form data
            const formData = new FormData(form);
            for (let pair of formData.entries()) {
                console.log(pair[0] + ': ' + pair[1]);
            }
            
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                console.log('Formulaire invalide, soumission empêchée');
                
                // Log invalid fields
                const invalidFields = form.querySelectorAll(':invalid');
                console.log('Champs invalides:', invalidFields);
                invalidFields.forEach(field => {
                    console.log('Champ invalide:', field.name, field.id);
                });
            }
        });
    } else {
        console.log('Formulaire non trouvé!');
    }
});