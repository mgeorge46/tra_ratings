// main.js - Basic functionality for your PWA
document.addEventListener('DOMContentLoaded', function() {
    console.log("Main JS loaded for PWA");
    // Add additional JavaScript functionality as needed
});

// main.js - Custom handling for the PWA install prompt

let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
  // Prevent the default mini-info bar from showing on mobile
  e.preventDefault();
  // Save the event for later use
  deferredPrompt = e;
  // Display your custom install button (assumes an element with id 'install-btn')
  const installBtn = document.getElementById('install-btn');
  if (installBtn) {
    installBtn.style.display = 'block';
  }
});

// When the install button is clicked, show the install prompt
document.getElementById('install-btn')?.addEventListener('click', () => {
  if (deferredPrompt) {
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then((choiceResult) => {
      if (choiceResult.outcome === 'accepted') {
        console.log('User accepted the install prompt');
      } else {
        console.log('User dismissed the install prompt');
      }
      deferredPrompt = null;
      // Optionally hide the button again
      document.getElementById('install-btn').style.display = 'none';
    });
  }
});
