/*-----------------------------------------------------------------------------------
/*
/* Main JS
/*
-----------------------------------------------------------------------------------*/  
// Form validation and reset functionality
(function($) {

    // Colocar esto al inicio de tu $(document).ready
$(document).ready(function() {
    // Verificar si el formulario fue enviado exitosamente
    const formSubmitted = sessionStorage.getItem('formSubmitted');
    const hasSuccessMessage = $('.alert-success').length > 0;
    
    if (formSubmitted === 'true' || hasSuccessMessage) {
        // Limpiar el formulario solo si fue enviado exitosamente
        clearForm();
        // Limpiar la bandera
        sessionStorage.removeItem('formSubmitted');
    } else {
        // Si hay error pero el formulario fue enviado, mantener valores
        if ($('.alert-error').length > 0 || $('.error-message:visible').length > 0) {
            // No hacer nada, mantener los valores existentes
        } else {
            // Si es carga inicial de página (no hay mensaje de éxito ni error)
            clearForm();
        }
    }
    
    // Función para limpiar el formulario
    function clearForm() {
        const form = $('form');
        form[0].reset();
        // Limpiar campos específicos que podrían no resetearse completamente
        $('#date-of-birth').val('');
        $('#region').val('');
        // Limpiar mensajes de error
        $('.error-message').text('');
        // Quitar clases de error/éxito
        $('.input-error').removeClass('input-error');
        $('.input-success').removeClass('input-success');
    }
    
});

    $(document).ready(function() {
        const form = $('#registrationForm');
        
        // Name validation
        $('#name').on('input', function() {
            const nameError = $('#nameError');
            if ($(this).val().trim() === '') {
                nameError.text('El nombre es requerido');
            } else {
                nameError.text('');
            }
        });

        // Email validation
        $('#email').on('input', function() {
            const emailError = $('#emailError');
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            
            if ($(this).val().trim() === '') {
                emailError.text('El correo electrónico es requerido');
            } else if (!emailRegex.test($(this).val())) {
                emailError.text('Por favor ingrese un correo electrónico válido');
            } else {
                emailError.text('');
            }
        });

        // Date of birth validation
        $('#date-of-birth').on('change', function() {
            const dobError = $('#dobError');
            if (!$(this).val()) {
                dobError.text('La fecha de nacimiento es requerida');
            } else {
                const today = new Date();
                const selectedDate = new Date($(this).val());
                
                if (selectedDate > today) {
                    dobError.text('La fecha no puede ser en el futuro');
                } else {
                    dobError.text('');
                }
            }
        });

        //region validation
        $('#region').on('change', function() {
            const regionError = $('#regionError');
            
            if ($(this).val() === '' || $(this).val() === null) {
                $(this).addClass('input-error');
                regionError.text('Por favor seleccione una región');
            } else {
                $(this).removeClass('input-error').addClass('input-success');
                regionError.text('');
            }
        });

        // Phone validation
        $('#phone').on('input', function() {
            const phoneError = $('#phoneError');
            let value = $(this).val().replace(/\D/g, '');
            
            if (value.length > 10) {
                value = value.slice(0, 10);
            }
            
            if (value.length >= 3) {
                value = value.slice(0,3) + '-' + value.slice(3);
            }
            if (value.length >= 7) {
                value = value.slice(0,7) + '-' + value.slice(7);
            }
            
            $(this).val(value);
            
            if (!value) {
                phoneError.text('El número de teléfono es requerido');
            } else if (value.length < 12) {
                phoneError.text('Formato requerido: 123-456-7890');
            } else {
                phoneError.text('');
            }
        });

        // Server-side email validation error display
        $('.messages .alert').each(function() {
            const message = $(this).text().trim();
            if (message.includes('Correo electrónico ya en uso')) {
                $('#emailError').text('El correo electrónico ya esta registrado');
            }
        });
    });
})(jQuery);


(function($) {

	/*---------------------------------------------------- */
  	/* Preloader
   ------------------------------------------------------ */ 
  	$(window).load(function() {

   	// will first fade out the loading animation 
    	$("#status").fadeOut("slow"); 

    	// will fade out the whole DIV that covers the website. 
    	$("#preloader").delay(500).fadeOut("slow").remove();     
      
    	$('.js #hero .hero-image img').addClass("animated fadeInUpBig"); 
      $('.js #hero .buttons a.trial').addClass("animated shake");    

  	}) 


  	/*---------------------------------------------------- */
  	/* Mobile Menu
   ------------------------------------------------------ */  
  	var toggle_button = $("<a>", {                         
                        id: "toggle-btn", 
                        html : "Menu",
                        title: "Menu",
                        href : "#" } 
                        );
  	var nav_wrap = $('nav#nav-wrap')
  	var nav = $("ul#nav");  

  	/* id JS is enabled, remove the two a.mobile-btns 
  	and dynamically prepend a.toggle-btn to #nav-wrap */
  	nav_wrap.find('a.mobile-btn').remove(); 
  	nav_wrap.prepend(toggle_button); 

  	toggle_button.on("click", function(e) {
   	e.preventDefault();
    	nav.slideToggle("fast");     
  	});

  	if (toggle_button.is(':visible')) nav.addClass('mobile');
  	$(window).resize(function(){
   	if (toggle_button.is(':visible')) nav.addClass('mobile');
    	else nav.removeClass('mobile');
  	});

  	$('ul#nav li a').on("click", function(){      
   	if (nav.hasClass('mobile')) nav.fadeOut('fast');      
  	});


  	/*----------------------------------------------------*/
  	/* FitText Settings
  	------------------------------------------------------ */
  	setTimeout(function() {

   	$('h1.responsive-headline').fitText(1.2, { minFontSize: '25px', maxFontSize: '40px' });

  	}, 100);


  	/*----------------------------------------------------*/
  	/* Smooth Scrolling
  	------------------------------------------------------ */
  	$('.smoothscroll').on('click', function (e) {
	 	
	 	e.preventDefault();

   	var target = this.hash,
    	$target = $(target);

    	$('html, body').stop().animate({
       	'scrollTop': $target.offset().top
      }, 800, 'swing', function () {
      	window.location.hash = target;
      });

  	});


  	/*----------------------------------------------------*/
  	/* Highlight the current section in the navigation bar
  	------------------------------------------------------*/
	var sections = $("section"),
	navigation_links = $("#nav-wrap a");

	sections.waypoint( {

      handler: function(event, direction) {

		   var active_section;

			active_section = $(this);
			if (direction === "up") active_section = active_section.prev();

			var active_link = $('#nav-wrap a[href="#' + active_section.attr("id") + '"]');

         navigation_links.parent().removeClass("current");
			active_link.parent().addClass("current");

		},
		offset: '35%'
	});


	/*----------------------------------------------------*/
  	/* FitVids
  	/*----------------------------------------------------*/
   $(".fluid-video-wrapper").fitVids();


   /*----------------------------------------------------*/
  	/* Waypoints Animations
   ------------------------------------------------------ */
  	$('.js .design').waypoint(function() {
   	$('.js .design .feature-media').addClass( 'animated pulse' );    
  	}, { offset: 'bottom-in-view' });

  	$('.js .responsive').waypoint(function() {
   	$('.js .responsive .feature-media').addClass( 'animated pulse' );    
  	}, { offset: 'bottom-in-view' });

  	$('.js .cross-browser').waypoint(function() {
   	$('.js .cross-browser .feature-media').addClass( 'animated pulse' ); 
  	}, { offset: 'bottom-in-view' });

  	$('.js .video').waypoint(function() {
   	$('.js .video .feature-media').addClass( 'animated pulse' );     
  	}, { offset: 'bottom-in-view' });

  	$('.js #contactanos').waypoint(function() {
   	$('.js #contactanos input[type="email"]').addClass( 'animated fadeInLeftBig show' ); 
    	$('.js #contactanos input[type="submit"]').addClass( 'animated fadeInRightBig show' );   
  	}, { offset: 'bottom-in-view' });

  	
  	/*----------------------------------------------------*/
  	/* Flexslider
  	/*----------------------------------------------------*/
  	$('.flexslider').flexslider({
   	namespace: "flex-",
      controlsContainer: ".flex-container",
      animation: 'slide',
      controlNav: true,
      directionNav: false,
      smoothHeight: true,
      slideshowSpeed: 7000,
      animationSpeed: 600,
      randomize: false,
   });


   /*----------------------------------------------------*/
   /* ImageLightbox
   /*----------------------------------------------------*/

   if($("html").hasClass('cssanimations')) {

      var activityIndicatorOn = function()
      {
       	$( '<div id="imagelightbox-loading"><div></div></div>' ).appendTo( 'body' );
      },
      activityIndicatorOff = function()
      {
       	$( '#imagelightbox-loading' ).remove();
      },

      overlayOn = function()
      {
       	$( '<div id="imagelightbox-overlay"></div>' ).appendTo( 'body' );
      },
      overlayOff = function()
      {
       	$( '#imagelightbox-overlay' ).remove();
      },

      closeButtonOn = function( instance )
      {
       	$( '<a href="#" id="imagelightbox-close" title="close"><i class="fa fa fa-times"></i></a>' ).appendTo( 'body' ).on( 'click touchend', function(){ $( this ).remove(); instance.quitImageLightbox(); return false; });
      },
      closeButtonOff = function()
      {
       	$( '#imagelightbox-close' ).remove();
      },

      captionOn = function()
      {
      	var description = $( 'a[href="' + $( '#imagelightbox' ).attr( 'src' ) + '"] img' ).attr( 'alt' );
        	if( description.length > 0 )
         	$( '<div id="imagelightbox-caption">' + description + '</div>' ).appendTo( 'body' );        
      },
      captionOff = function()
      {
       	$( '#imagelightbox-caption' ).remove();
      };     

      var instanceA = $( 'a[data-imagelightbox="a"]' ).imageLightbox(
      {
         onStart:   function() { overlayOn(); closeButtonOn( instanceA ); },
         onEnd:     function() { overlayOff(); captionOff(); closeButtonOff(); activityIndicatorOff(); },
         onLoadStart: function() { captionOff(); activityIndicatorOn(); },
         onLoadEnd:   function() { captionOn(); activityIndicatorOff(); }

      });
        
    }      
    else {
         
      /*----------------------------------------------------*/
   	/* prettyPhoto for old IE
   	/*----------------------------------------------------*/
      $("#screenshots").find(".item-wrap a").attr("rel","prettyPhoto[pp_gal]");

      $("a[rel^='prettyPhoto']").prettyPhoto( {

      	animation_speed: 'fast', /* fast/slow/normal */
      	slideshow: false, /* false OR interval time in ms */
      	autoplay_slideshow: false, /* true/false */
      	opacity: 0.80, /* Value between 0 and 1 */
      	show_title: true, /* true/false */
      	allow_resize: true, /* Resize the photos bigger than viewport. true/false */
      	default_width: 500,
      	default_height: 344,
      	counter_separator_label: '/', /* The separator for the gallery counter 1 "of" 2 */
      	theme: 'pp_default', /* light_rounded / dark_rounded / light_square / dark_square / facebook */
      	hideflash: false, /* Hides all the flash object on a page, set to TRUE if flash appears over prettyPhoto */
      	wmode: 'opaque', /* Set the flash wmode attribute */
      	autoplay: true, /* Automatically start videos: True/False */
      	modal: false, /* If set to true, only the close button will close the window */
      	overlay_gallery: false, /* If set to true, a gallery will overlay the fullscreen image on mouse over */
      	keyboard_shortcuts: true, /* Set to false if you open forms inside prettyPhoto */
      	deeplinking: false,
      	social_tools: false

      }); 

    }
	//to make sure the radio button is unckecked everytime the page is loaded
	$(document).ready(function() {
        $('input[type="radio"]').prop('checked', false); // Uncheck all radio buttons on load
    });
	
	//to show a textbox if they want the registry personalized to write any petitions
	$(document).ready(function() {
        const textboxContainer = $('#textbox-container');
        
        // Initially hide the text box
        textboxContainer.hide();

        // Add event listeners for the radio buttons
        $('input[name="personalizada"]').on('change', function() {
            if ($('#si').is(':checked')) {
                textboxContainer.show(); // Show the text box
            } else {
                textboxContainer.hide(); // Hide the text box
            }
        });
    });

	//so that the users cannot pick a date for the envent with 1 week anticipation
	$(document).ready(function() {
        const datePicker = $('#event-date');
        const today = new Date();
        const oneWeekLater = new Date();

        // Add 7 days to today's date
        oneWeekLater.setDate(today.getDate() + 7);

        // Format dates as YYYY-MM-DD
        const todayFormatted = today.toISOString().split('T')[0];
        const oneWeekLaterFormatted = oneWeekLater.toISOString().split('T')[0];

        // Set the min and max attributes for the date picker
        datePicker.attr('min', oneWeekLaterFormatted);
        datePicker.attr('max', '');

        // Example: Log the range for debugging
        console.log(`Date picker restricted from: ${todayFormatted} to ${oneWeekLaterFormatted}`);
    });

	document.addEventListener('DOMContentLoaded', function () {
		// Clear all text areas and input fields on page load
		const clearInputs = () => {
			const inputs = document.querySelectorAll('textarea, input[type="text"], input[type="email"], input[type="number"], input[type="date"]');
			inputs.forEach(input => input.value = '');
		};
		clearInputs();
	
		// Handle phone number input formatting
		const formatPhoneNumber = (event) => {
			const input = event.target;
			let formattedValue = input.value.replace(/\D/g, ''); // Remove non-numeric characters
	
			// Limit to a maximum of 10 digits
			if (formattedValue.length > 10) {
				formattedValue = formattedValue.slice(0, 10);
			}
	
			// Format the phone number with dashes
			if (formattedValue.length > 3 && formattedValue.length <= 6) {
				formattedValue = formattedValue.slice(0, 3) + '-' + formattedValue.slice(3);
			} else if (formattedValue.length > 6) {
				formattedValue = formattedValue.slice(0, 3) + '-' + formattedValue.slice(3, 6) + '-' + formattedValue.slice(6);
			}
	
			input.value = formattedValue;
		};
	
		// Apply formatting only to specific phone number input
		const phoneInput = document.querySelector('#phone'); // Update ID as per your input field
		if (phoneInput) {
			phoneInput.addEventListener('input', formatPhoneNumber);
		}
	});


	// Form validation
    $(document).ready(function() {
        const form = $('#registrationForm');
        
        // Name validation
        $('#name').on('input', function() {
            const nameError = $('#nameError');
            if ($(this).val().trim() === '') {
                $(this).addClass('input-error');
                nameError.text('El nombre es requerido');
            } else {
                $(this).removeClass('input-error').addClass('input-success');
                nameError.text('');
            }
        });

        // Email validation
        $('#email').on('input', function() {
            const emailError = $('#emailError');
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            
            if (!emailRegex.test($(this).val())) {
                $(this).addClass('input-error');
                emailError.text('Por favor ingrese un correo electrónico válido');
            } else {
                $(this).removeClass('input-error').addClass('input-success');
                emailError.text('');
            }
        });

        // Phone validation
        $('#phone').on('input', function() {
            const phoneError = $('#phoneError');
            const phoneRegex = /^\d{3}-\d{3}-\d{4}$/;
            
            // Format the phone number
            let value = $(this).val().replace(/\D/g, '');
            if (value.length >= 3) {
                value = value.slice(0,3) + '-' + value.slice(3);
            }
            if (value.length >= 7) {
                value = value.slice(0,7) + '-' + value.slice(7);
            }
            if (value.length > 12) {
                value = value.slice(0,12);
            }
            $(this).val(value);

            if (!phoneRegex.test($(this).val())) {
                $(this).addClass('input-error');
                phoneError.text('Formato requerido: 123-456-7890');
            } else {
                $(this).removeClass('input-error').addClass('input-success');
                phoneError.text('');
            }
        });

        // Date of birth validation
        $('#date-of-birth').on('change', function() {
            const dobError = $('#dobError');
            const today = new Date();
            const selectedDate = new Date($(this).val());
            
            if (selectedDate > today) {
                $(this).addClass('input-error');
                dobError.text('La fecha no puede ser en el futuro');
            } else {
                $(this).removeClass('input-error').addClass('input-success');
                dobError.text('');
            }
        });

        // Form submission
        form.on('submit', function(e) {
            let hasErrors = false;
            
            // Trigger validation on all required fields including region
            $('#name').trigger('input');
            $('#email').trigger('input');
            $('#phone').trigger('input');
            $('#date-of-birth').trigger('change');
            $('#region').trigger('change');
            
            $(this).find('input, select').each(function() {
                if ($(this).hasClass('input-error') || $(this).val().trim() === '') {
                    hasErrors = true;
                    // Marcar el campo específico con error
                    if (!$(this).hasClass('input-error')) {
                        $(this).addClass('input-error');
                        // Si no hay mensaje de error, añadirlo
                        const fieldId = $(this).attr('id');
                        const errorEl = $('#' + fieldId + 'Error');
                        if (errorEl.length && !errorEl.text()) {
                            errorEl.text('Este campo es requerido');
                        }
                    }
                }
            });
            
            if (hasErrors) {
                e.preventDefault(); // Prevenir envío del formulario
                // Scroll al primer error
                const firstError = $('.input-error:first');
                if (firstError.length) {
                    $('html, body').animate({
                        scrollTop: firstError.offset().top - 100
                    }, 500);
                }
                alert('Por favor corrija los errores antes de enviar el formulario.');
                return false;
            }
            
            // Si llegamos aquí, el formulario es válido y se enviará
            // Agregamos una bandera al sessionStorage
            sessionStorage.setItem('formSubmitted', 'true');
        });
    });

/*---------------------------------------------------- */
    /* Chart.js Integration
    ------------------------------------------------------ */ 
    function initChart() {
        console.log('Initializing chart...');
        
        const canvasId = '#attendeesChartattendee-chart';
        const dataScriptId = '#chart-data-attendee-chart';
        
        const canvas = document.querySelector(canvasId);
        const dataScript = document.querySelector(dataScriptId);
        
        if (!canvas || !dataScript) return;
        
        try {
            const chartData = JSON.parse(dataScript.textContent);
            const ctx = canvas.getContext('2d');
            
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: chartData.dates,
                    datasets: [
                        {
                            label: 'Pre-registered',
                            data: chartData.preRegistered,
                            borderColor: '#4CAF50',
                            backgroundColor: 'rgba(76, 175, 80, 0.1)',
                            fill: true,
                            tension: 0.4
                        },
                        {
                            label: 'Registered at Event',
                            data: chartData.registeredAtEvent,
                            borderColor: '#2196F3',
                            backgroundColor: 'rgba(33, 150, 243, 0.1)',
                            fill: true,
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        title: {
                            display: true,
                            text: 'Attendee Registration Overview'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error creating chart:', error);
        }
    }

    $(document).ready(function() {
        // Initialize charts when document is ready
        if (typeof Chart !== 'undefined') {
            initChart();
        } else {
            // Wait for Chart.js to load
            const checkInterval = setInterval(function() {
                if (typeof Chart !== 'undefined') {
                    clearInterval(checkInterval);
                    initChart();
                }
            }, 100);
        }
        
        // Form validation code (keep your existing form validation code here)
        const form = $('#registrationForm');
        if (form.length) {
            // Your existing form validation code...
        }
    });

    /*---------------------------------------------------- */
    /* Mobile Menu
    ------------------------------------------------------ */  
    var toggle_button = $("<a>", {                         
        id: "toggle-btn", 
        html : "Menu",
        title: "Menu",
        href : "#" 
    });
    var nav_wrap = $('nav#nav-wrap');
    var nav = $("ul#nav");  

    nav_wrap.find('a.mobile-btn').remove(); 
    nav_wrap.prepend(toggle_button); 

    toggle_button.on("click", function(e) {
        e.preventDefault();
        nav.slideToggle("fast");     
    });

    if (toggle_button.is(':visible')) nav.addClass('mobile');
    $(window).resize(function(){
        if (toggle_button.is(':visible')) nav.addClass('mobile');
        else nav.removeClass('mobile');
    });

    $('ul#nav li a').on("click", function(){      
        if (nav.hasClass('mobile')) nav.fadeOut('fast');      
    });


})(jQuery);

document.addEventListener('DOMContentLoaded', function() {
    // Direct chart initialization
    try {
        var chartCanvas = document.getElementById('attendanceBarChart');
        
        if (chartCanvas) {
            var ctx = chartCanvas.getContext('2d');
            
            // Read data attributes from the canvas element
            var arrivalPercentage = parseFloat(chartCanvas.getAttribute('data-arrival-percentage') || 0);
            var checkedOutAttendees = parseFloat(chartCanvas.getAttribute('data-checked-out-attendees') || 0);
            var checkOutRate = Math.round((checkedOutAttendees / 200) * 100 * 10) / 10;
            
            // Log values for debugging
            console.log('Chart values:', {
                arrivalPercentage: arrivalPercentage,
                checkedOutAttendees: checkedOutAttendees,
                checkOutRate: checkOutRate
            });
            
            // Make sure Chart.js is loaded
            if (typeof Chart === 'undefined') {
                console.error('Chart.js is not loaded!');
                return;
            }
            
            // Set explicit height on the canvas
            chartCanvas.style.height = '250px';
            
            // Destroy any existing chart instance
            if (window.attendanceChart) {
                window.attendanceChart.destroy();
            }
            
            // Create new chart instance
            window.attendanceChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Check-in', 'Check-out'],
                    datasets: [{
                        label: 'Attendance Rate (%)',
                        data: [arrivalPercentage, checkOutRate],
                        backgroundColor: [
                            'rgba(28, 200, 138, 0.8)',  // Green for check-in
                            'rgba(54, 185, 204, 0.8)'   // Blue for check-out
                        ],
                        borderColor: [
                            'rgb(28, 200, 138)',
                            'rgb(54, 185, 204)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    maintainAspectRatio: false,
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            ticks: {
                                callback: function(value) {
                                    return value + '%';
                                }
                            }
                        }
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return context.raw.toFixed(1) + '%';
                                }
                            }
                        }
                    }
                }
            });
            
            console.log('Chart initialized successfully');
        } else {
            console.error('Chart canvas element not found');
        }
    } catch (error) {
        console.error('Error initializing chart:', error);
    }
});