// Popup script for Job Application Agent

document.addEventListener('DOMContentLoaded', function() {
  console.log("Popup loaded - DOM content loaded");
  
  // DOM Elements
  const statusBadge = document.getElementById('status-badge');
  const learningSection = document.getElementById('learning-section');
  const activelearningSection = document.getElementById('activelearning-section');
  const recordingIndicator = document.getElementById('recording-indicator');
  const detectionAlert = document.getElementById('detection-alert');
  const fieldCount = document.getElementById('field-count');
  const formCount = document.getElementById('form-count');
  
  // Log which elements were found
  console.log("Elements found:", {
    statusBadge: !!statusBadge,
    learningSection: !!learningSection,
    activelearningSection: !!activelearningSection,
    recordingIndicator: !!recordingIndicator,
    detectionAlert: !!detectionAlert,
    fieldCount: !!fieldCount,
    formCount: !!formCount
  });
  
  // Buttons
  const startLearningBtn = document.getElementById('start-learning-btn');
  const stopLearningBtn = document.getElementById('stop-learning-btn');
  const startAutofillBtn = document.getElementById('start-autofill-btn');
  const viewDataBtn = document.getElementById('view-data-btn');
  const settingsBtn = document.getElementById('settings-btn');
  const exportDataBtn = document.getElementById('export-data-btn');
  
  // Log which buttons were found
  console.log("Buttons found:", {
    startLearningBtn: !!startLearningBtn,
    stopLearningBtn: !!stopLearningBtn,
    startAutofillBtn: !!startAutofillBtn,
    viewDataBtn: !!viewDataBtn,
    settingsBtn: !!settingsBtn,
    exportDataBtn: !!exportDataBtn
  });
  
  // Initial state
  let isLearning = false;
  let isActive = false;
  
  // Function to update UI based on current state
  function updateUI() {
    console.log("Updating UI - learning:", isLearning, "active:", isActive);
    
    // Update status badge
    if (isLearning) {
      statusBadge.textContent = 'Learning';
      statusBadge.classList.remove('active');
      statusBadge.classList.add('learning');
    } else if (isActive) {
      statusBadge.textContent = 'Active';
      statusBadge.classList.remove('learning');
      statusBadge.classList.add('active');
    } else {
      statusBadge.textContent = 'Inactive';
      statusBadge.classList.remove('active', 'learning');
    }
    
    // Show/hide sections based on state
    learningSection.style.display = !isLearning ? 'block' : 'none';
    activelearningSection.style.display = isLearning ? 'block' : 'none';
    recordingIndicator.style.display = isLearning ? 'flex' : 'none';
    
    // Update buttons
    startLearningBtn.style.display = !isLearning ? 'block' : 'none';
    stopLearningBtn.style.display = isLearning ? 'block' : 'none';
    startAutofillBtn.disabled = !isActive;
  }
  
  // Check if form detected on current page
  function checkFormDetection() {
    console.log("Checking for form detection...");
    try {
      chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        if (tabs && tabs.length > 0) {
          console.log("Active tab:", tabs[0].url);
          chrome.tabs.sendMessage(tabs[0].id, {action: "checkForForm"}, function(response) {
            console.log("Form detection response:", response);
            if (response && response.formDetected) {
              detectionAlert.style.display = 'block';
            } else {
              detectionAlert.style.display = 'none';
            }
          });
        } else {
          console.error("No active tabs found");
        }
      });
    } catch (err) {
      console.error("Error checking form detection:", err);
    }
  }
  
  // Get stats from background
  function getStats() {
    console.log("Getting stats from background...");
    try {
      chrome.runtime.sendMessage({action: "getStats"}, function(response) {
        console.log("Stats response:", response);
        if (response) {
          fieldCount.textContent = response.fieldCount || 0;
          formCount.textContent = response.formCount || 0;
          isActive = response.isActive || false;
          updateUI();
        }
      });
    } catch (err) {
      console.error("Error getting stats:", err);
    }
  }
  
  // Check if recording is active
  function checkRecordingStatus() {
    console.log("Checking if recording is active...");
    try {
      chrome.runtime.sendMessage({action: "isRecording"}, function(response) {
        console.log("Recording status response:", response);
        if (response && response.isRecording) {
          isLearning = true;
          updateUI();
        }
      });
    } catch (err) {
      console.error("Error checking recording status:", err);
    }
  }
  
  // Start learning mode
  startLearningBtn.addEventListener('click', function() {
    console.log("Start learning button clicked");
    try {
      chrome.runtime.sendMessage({action: "startLearning"}, function(response) {
        console.log("Start learning response:", response);
        if (response && response.success) {
          isLearning = true;
          updateUI();
        }
      });
    } catch (err) {
      console.error("Error starting learning:", err);
    }
  });
  
  // Stop learning mode
  stopLearningBtn.addEventListener('click', function() {
    console.log("Stop learning button clicked");
    try {
      chrome.runtime.sendMessage({action: "stopLearning"}, function(response) {
        console.log("Stop learning response:", response);
        if (response && response.success) {
          isLearning = false;
          isActive = true;
          updateUI();
        }
      });
    } catch (err) {
      console.error("Error stopping learning:", err);
    }
  });
  
  // Start autofill
  startAutofillBtn.addEventListener('click', function() {
    console.log("Start autofill button clicked");
    try {
      chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        chrome.tabs.sendMessage(tabs[0].id, {action: "startAutofill"});
        window.close(); // Close popup after triggering autofill
      });
    } catch (err) {
      console.error("Error starting autofill:", err);
    }
  });
  
  // View data
  viewDataBtn.addEventListener('click', function() {
    console.log("View data button clicked");
    try {
      chrome.runtime.openOptionsPage();
    } catch (err) {
      console.error("Error opening options page:", err);
    }
  });
  
  // Export data
  exportDataBtn.addEventListener('click', function() {
    console.log("Export data button clicked");
    try {
      chrome.runtime.sendMessage({action: "exportData"}, function(response) {
        console.log("Export data response:", response);
        if (response && response.status === 'success') {
          // Show success message
          alert('Data exported successfully! Check your downloads folder.');
        } else {
          alert('Failed to export data: ' + (response ? response.message : 'Unknown error'));
        }
      });
    } catch (err) {
      console.error("Error exporting data:", err);
      alert('Error exporting data: ' + err.message);
    }
  });
  
  // Settings
  settingsBtn.addEventListener('click', function() {
    console.log("Settings button clicked");
    try {
      chrome.tabs.create({url: 'options/options.html#settings'});
    } catch (err) {
      console.error("Error opening settings:", err);
    }
  });
  
  // Initialize
  console.log("Initializing popup...");
  try {
    checkFormDetection();
    getStats();
    checkRecordingStatus(); // Check if recording is already active
  } catch (err) {
    console.error("Error during initialization:", err);
  }
  
  // Listen for messages from background
  chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
    console.log("Message received:", request);
    if (request.action === "learningStatusChanged") {
      isLearning = request.isLearning;
      updateUI();
    } else if (request.action === "statsUpdated") {
      getStats();
    }
  });
  
  console.log("Popup initialization complete");
}); 