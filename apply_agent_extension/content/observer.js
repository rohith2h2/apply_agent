/**
 * Job Application Agent - Form Observer
 * 
 * This content script monitors form interactions to learn how the user fills out
 * job applications. It detects form fields, tracks user input, and sends the data
 * to the background script for analysis.
 */

// State
let isRecordingActive = false;
let formFields = new Map(); // Store field references by ID/name
let fieldValues = new Map(); // Store current values of fields
let formMutationObserver = null;
let fieldObservers = []; // Store disconnect functions for cleanup
let formsDetected = false; // Track if forms were detected
let pageIndicator = null; // Visual indicator element

// Listen for messages from popup/background
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Content script received message:', message);
  
  if (message.action === 'startRecording') {
    isRecordingActive = true;
    startObserving();
    showRecordingIndicator();
    sendResponse({status: 'success', message: 'Recording started'});
  } 
  else if (message.action === 'stopRecording') {
    isRecordingActive = false;
    stopObserving();
    hideRecordingIndicator();
    sendResponse({status: 'success', message: 'Recording stopped'});
  }
  else if (message.action === 'startAutofill') {
    // To be implemented - will handle autofilling forms
    sendResponse({status: 'error', message: 'Autofill not yet implemented'});
  }
  else if (message.action === 'checkForForm') {
    // Check if there are any forms on the page
    const forms = document.querySelectorAll('form');
    const formLikeContainers = document.querySelectorAll('.form, .application-form, [data-form]');
    const hasForm = forms.length > 0 || formLikeContainers.length > 0;
    
    console.log('Form detection check:', { 
      forms: forms.length, 
      formLikeContainers: formLikeContainers.length,
      hasForm: hasForm
    });
    
    sendResponse({
      formDetected: hasForm,
      status: 'success'
    });
  }
  else if (message.action === 'checkRecordingStatus') {
    sendResponse({
      isRecording: isRecordingActive,
      status: 'success'
    });
  }
  
  return true; // Keep the message channel open for async response
});

/**
 * Start observing the page for forms and inputs
 */
function startObserving() {
  console.log('Starting observation of form fields');
  
  // First, find all existing forms
  scanForForms();
  
  // Then set up an observer to detect dynamically added forms
  setupFormObserver();
  
  // Send page metadata
  sendPageMetadata();
}

/**
 * Scan the page for all forms and form fields
 */
function scanForForms() {
  // Find all forms on the page
  const forms = document.querySelectorAll('form');
  forms.forEach(attachFormListeners);
  
  // Also look for form-like containers (some sites don't use <form> tags)
  const possibleFormContainers = document.querySelectorAll('.form, .application-form, [data-form]');
  possibleFormContainers.forEach(container => {
    if (container.tagName !== 'FORM') {
      attachFormFieldListeners(container);
    }
  });
  
  // Some applications might not use forms at all, so scan for input fields directly
  if (forms.length === 0 && possibleFormContainers.length === 0) {
    attachFormFieldListeners(document.body);
  }
}

/**
 * Set up MutationObserver to detect new forms added to the page
 */
function setupFormObserver() {
  formMutationObserver = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.addedNodes.length) {
        mutation.addedNodes.forEach((node) => {
          // Check if the added node is a form
          if (node.nodeName === 'FORM') {
            attachFormListeners(node);
          } 
          // Check if it contains forms
          else if (node.querySelectorAll) {
            const forms = node.querySelectorAll('form');
            forms.forEach(attachFormListeners);
            
            // Also check for form-like containers
            const possibleFormContainers = node.querySelectorAll('.form, .application-form, [data-form]');
            possibleFormContainers.forEach(container => {
              if (container.tagName !== 'FORM') {
                attachFormFieldListeners(container);
              }
            });
          }
        });
      }
    });
  });
  
  // Observe the entire document
  formMutationObserver.observe(document.body, { 
    childList: true, 
    subtree: true 
  });
}

/**
 * Attach event listeners to all elements in a form
 */
function attachFormListeners(form) {
  console.log('Attaching listeners to form:', form);
  
  // Store form metadata
  const formData = {
    id: form.id || generateId('form'),
    action: form.action || window.location.href,
    method: form.method || 'unknown',
    className: form.className,
    fields: []
  };
  
  // Send form metadata
  sendToBackground('formDetected', formData);
  
  // Attach listeners to form fields
  attachFormFieldListeners(form);
  
  // Listen for form submission
  form.addEventListener('submit', (e) => {
    if (isRecordingActive) {
      // Collect all field values at submission time
      const submissionData = {
        formId: formData.id,
        timestamp: new Date().toISOString(),
        fields: Array.from(fieldValues.entries()).map(([id, value]) => ({
          id,
          value
        }))
      };
      
      sendToBackground('formSubmission', submissionData);
    }
  });
}

/**
 * Attach listeners to form fields within a container
 */
function attachFormFieldListeners(container) {
  // Get all input fields
  const inputs = container.querySelectorAll('input, textarea, select');
  
  inputs.forEach((input) => {
    // Generate a unique ID for this field if it doesn't have one
    const fieldId = input.id || input.name || generateId('field');
    
    // Store field reference
    formFields.set(fieldId, input);
    
    // Extract field metadata
    const fieldData = extractFieldMetadata(input, fieldId);
    
    // Send field detection event
    sendToBackground('fieldDetected', fieldData);
    
    // Attach appropriate event listener based on field type
    attachFieldListener(input, fieldId, fieldData.type);
  });
}

/**
 * Extract metadata about a form field
 */
function extractFieldMetadata(field, fieldId) {
  // Find the field label
  let labelText = findFieldLabel(field);
  
  // Determine field type and specific attributes
  let fieldType = field.type || field.tagName.toLowerCase();
  let fieldAttributes = {};
  
  // Copy relevant attributes
  for (let attr of field.attributes) {
    if (['type', 'placeholder', 'maxlength', 'required', 'pattern', 'min', 'max'].includes(attr.name)) {
      fieldAttributes[attr.name] = attr.value;
    }
  }
  
  // For select elements, get the options
  const options = [];
  if (field.tagName === 'SELECT') {
    Array.from(field.options).forEach(option => {
      options.push({
        value: option.value,
        text: option.text
      });
    });
  }
  
  return {
    id: fieldId,
    name: field.name || '',
    type: fieldType,
    label: labelText,
    placeholder: field.placeholder || '',
    required: field.required || false,
    attributes: fieldAttributes,
    options: options,
    timestamp: new Date().toISOString()
  };
}

/**
 * Find the label text for a form field
 */
function findFieldLabel(field) {
  // Try to find an explicit label
  if (field.id) {
    const label = document.querySelector(`label[for="${field.id}"]`);
    if (label) {
      return label.textContent.trim();
    }
  }
  
  // Check for a parent label element
  let parent = field.parentElement;
  while (parent && parent.tagName !== 'FORM' && parent.tagName !== 'BODY') {
    if (parent.tagName === 'LABEL') {
      return parent.textContent.replace(field.value || '', '').trim();
    }
    
    // Check for common patterns like <div><label>Name</label><input></div>
    const siblingLabel = parent.querySelector('label');
    if (siblingLabel && !siblingLabel.getAttribute('for')) {
      return siblingLabel.textContent.trim();
    }
    
    parent = parent.parentElement;
  }
  
  // Use placeholder as fallback
  if (field.placeholder) {
    return field.placeholder;
  }
  
  // Look at preceding elements for possible labels
  const previousSibling = field.previousElementSibling;
  if (previousSibling && (previousSibling.tagName === 'LABEL' || 
                          previousSibling.tagName === 'SPAN' || 
                          previousSibling.tagName === 'DIV')) {
    return previousSibling.textContent.trim();
  }
  
  // Return field name as last resort
  return field.name || 'Unknown field';
}

/**
 * Attach the appropriate event listener based on field type
 */
function attachFieldListener(field, fieldId, fieldType) {
  // Remove existing listeners if any
  field.removeEventListener('input', handleInputChange);
  field.removeEventListener('change', handleInputChange);
  field.removeEventListener('blur', handleInputChange);
  
  // Function to handle input changes
  function handleInputChange(e) {
    if (!isRecordingActive) return;
    
    const value = field.type === 'checkbox' || field.type === 'radio' 
      ? field.checked 
      : field.value;
    
    // Update stored value
    fieldValues.set(fieldId, value);
    
    // Send update to background
    sendToBackground('fieldValueChanged', {
      fieldId: fieldId,
      value: value,
      timestamp: new Date().toISOString()
    });
  }
  
  // Attach listeners based on field type
  if (fieldType === 'checkbox' || fieldType === 'radio') {
    field.addEventListener('change', handleInputChange);
  } else if (fieldType === 'select-one' || fieldType === 'select-multiple') {
    field.addEventListener('change', handleInputChange);
  } else {
    // For text inputs, textareas, etc.
    field.addEventListener('input', handleInputChange);
    field.addEventListener('blur', handleInputChange); // Catch when focus leaves the field
  }
  
  // Store disconnect function
  fieldObservers.push(() => {
    field.removeEventListener('input', handleInputChange);
    field.removeEventListener('change', handleInputChange);
    field.removeEventListener('blur', handleInputChange);
  });
}

/**
 * Send data to the background script
 */
function sendToBackground(eventType, data) {
  chrome.runtime.sendMessage({
    action: 'recordEvent',
    eventType: eventType,
    data: data,
    url: window.location.href,
    pageTitle: document.title,
    timestamp: new Date().toISOString()
  });
}

/**
 * Send metadata about the current page
 */
function sendPageMetadata() {
  const metadata = {
    url: window.location.href,
    title: document.title,
    domain: window.location.hostname,
    timestamp: new Date().toISOString()
  };
  
  // Try to detect if this is a job application page
  const isJobApplication = detectIfJobApplication();
  metadata.isJobApplication = isJobApplication;
  
  sendToBackground('pageMetadata', metadata);
}

/**
 * Try to detect if the current page is a job application
 */
function detectIfJobApplication() {
  // Check URL patterns
  const url = window.location.href.toLowerCase();
  if (url.includes('apply') || url.includes('career') || 
      url.includes('job') || url.includes('application')) {
    return true;
  }
  
  // Check for common form fields in job applications
  const fields = document.querySelectorAll('input, textarea, select');
  let relevantFieldCount = 0;
  
  fields.forEach(field => {
    const fieldText = (field.id || '') + ' ' + (field.name || '') + ' ' + 
                     (field.placeholder || '') + ' ' + (findFieldLabel(field) || '');
    
    const lcFieldText = fieldText.toLowerCase();
    
    if (lcFieldText.includes('name') || lcFieldText.includes('email') || 
        lcFieldText.includes('resume') || lcFieldText.includes('cv') ||
        lcFieldText.includes('cover letter') || lcFieldText.includes('experience') ||
        lcFieldText.includes('education') || lcFieldText.includes('skill')) {
      relevantFieldCount++;
    }
  });
  
  return relevantFieldCount >= 3;
}

/**
 * Generate a unique ID
 */
function generateId(prefix = 'field') {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Stop all observation and clean up
 */
function stopObserving() {
  console.log('Stopping observation of form fields');
  
  // Disconnect form observer
  if (formMutationObserver) {
    formMutationObserver.disconnect();
    formMutationObserver = null;
  }
  
  // Remove all field listeners
  fieldObservers.forEach(disconnect => disconnect());
  fieldObservers = [];
  
  // Clear stored data
  formFields.clear();
  fieldValues.clear();
}

/**
 * Create and show a recording indicator on the page
 */
function showRecordingIndicator() {
  // Remove any existing indicator first
  hideRecordingIndicator();
  
  // Create the floating indicator element
  pageIndicator = document.createElement('div');
  pageIndicator.id = 'job-app-agent-indicator';
  pageIndicator.innerHTML = `
    <div class="indicator-content">
      <div class="recording-dot"></div>
      <span>Job Application Agent Recording</span>
      <button id="stop-recording-btn">Stop</button>
    </div>
  `;
  
  // Add styles
  const style = document.createElement('style');
  style.textContent = `
    #job-app-agent-indicator {
      position: fixed;
      top: 10px;
      right: 10px;
      z-index: 9999;
      background-color: rgba(255, 255, 255, 0.95);
      border: 1px solid #dc3545;
      border-radius: 8px;
      padding: 8px 12px;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
      font-family: Arial, sans-serif;
      font-size: 14px;
      transition: opacity 0.3s ease;
    }
    #job-app-agent-indicator .indicator-content {
      display: flex;
      align-items: center;
    }
    #job-app-agent-indicator .recording-dot {
      width: 12px;
      height: 12px;
      background-color: #dc3545;
      border-radius: 50%;
      margin-right: 8px;
      animation: pulse 1.5s infinite;
    }
    #job-app-agent-indicator #stop-recording-btn {
      background-color: #dc3545;
      color: white;
      border: none;
      border-radius: 4px;
      padding: 4px 8px;
      margin-left: 10px;
      cursor: pointer;
      font-size: 12px;
    }
    #job-app-agent-indicator #stop-recording-btn:hover {
      background-color: #bd2130;
    }
    @keyframes pulse {
      0% { opacity: 1; }
      50% { opacity: 0.6; }
      100% { opacity: 1; }
    }
  `;
  
  // Add to the document
  document.head.appendChild(style);
  document.body.appendChild(pageIndicator);
  
  // Add event listener to stop button
  document.getElementById('stop-recording-btn').addEventListener('click', function() {
    isRecordingActive = false;
    stopObserving();
    hideRecordingIndicator();
    
    // Notify the background script that recording has stopped
    chrome.runtime.sendMessage({
      action: 'recordingStopped',
      url: window.location.href,
      pageTitle: document.title
    });
  });
}

/**
 * Remove the recording indicator from the page
 */
function hideRecordingIndicator() {
  if (pageIndicator) {
    pageIndicator.remove();
    pageIndicator = null;
  }
}

// Initialize if the extension was already recording
chrome.storage.local.get(['currentSession'], function(result) {
  if (result.currentSession) {
    isRecordingActive = true;
    startObserving();
  }
}); 