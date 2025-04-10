/**
 * Job Application Agent - Background Script
 * 
 * This script runs in the background and manages:
 * - Communication between content scripts and popup
 * - Data storage and processing
 * - API communication with the backend server
 */

// State
let currentSession = null;
let learningData = {
  sessions: [],
  fieldsLearned: 0,
  lastAnalyzed: null
};

// Constants
const API_BASE_URL = 'http://127.0.0.1:5000/api';  // Change to your backend URL
const SESSION_STORAGE_KEY = 'currentSession';
const LEARNING_DATA_KEY = 'learningData';

// Initialize by loading stored data
chrome.runtime.onInstalled.addListener(() => {
  console.log('Job Application Agent installed/updated');
  loadStoredData();
});

// Listen for messages from content scripts and popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Background received message:', message.action);
  
  switch (message.action) {
    case 'startLearningSession':
      startLearningSession(message.url, message.pageTitle)
        .then(response => sendResponse(response))
        .catch(error => sendResponse({ status: 'error', message: error.message }));
      break;
      
    case 'endLearningSession':
      endLearningSession()
        .then(response => sendResponse(response))
        .catch(error => sendResponse({ status: 'error', message: error.message }));
      break;
      
    case 'recordEvent':
      recordEvent(message.eventType, message.data, message.url, message.pageTitle)
        .then(response => sendResponse(response))
        .catch(error => sendResponse({ status: 'error', message: error.message }));
      break;
      
    case 'recordingStopped':
      // Notify popup that recording has stopped
      chrome.runtime.sendMessage({ 
        action: "learningStatusChanged", 
        isLearning: false 
      });
      
      // End the current learning session
      endLearningSession()
        .then(response => {
          console.log('Learning session ended from page indicator:', response);
        })
        .catch(error => {
          console.error('Error stopping learning from page indicator:', error);
        });
      break;
      
    case 'getLearningStatus':
      getLearningStatus()
        .then(status => sendResponse(status))
        .catch(error => sendResponse({ status: 'error', message: error.message }));
      break;
      
    case 'analyzeLearning':
      analyzeLearning()
        .then(result => sendResponse(result))
        .catch(error => sendResponse({ status: 'error', message: error.message }));
      break;
      
    case 'exportData':
      exportLearningData()
        .then(() => sendResponse({ status: 'success', message: 'Data exported successfully' }))
        .catch(error => sendResponse({ status: 'error', message: error.message }));
      break;
      
    // Add handlers for popup actions
    case 'getStats':
      const stats = {
        fieldCount: currentSession ? currentSession.fields.size : 0,
        formCount: currentSession ? currentSession.formSubmissions.length : 0,
        isActive: learningData.sessions.length > 0,
        success: true
      };
      console.log('Sending stats to popup:', stats);
      sendResponse(stats);
      break;
      
    case 'startLearning':
      // Get active tab info
      chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        if (tabs && tabs.length > 0) {
          // Start a learning session with the current page
          startLearningSession(tabs[0].url, tabs[0].title)
            .then((response) => {
              console.log('Learning session started:', response);
              
              // Notify content script to start recording
              chrome.tabs.sendMessage(tabs[0].id, {action: 'startRecording'});
              
              // Notify popup (and any other listeners) about the status change
              chrome.runtime.sendMessage({ 
                action: "learningStatusChanged", 
                isLearning: true 
              });
              
              sendResponse({
                success: true,
                message: 'Learning started',
                sessionId: response.sessionId
              });
            })
            .catch((error) => {
              console.error('Error starting learning:', error);
              sendResponse({
                success: false,
                message: error.message
              });
            });
        } else {
          sendResponse({
            success: false,
            message: 'No active tab found'
          });
        }
      });
      break;
      
    case 'stopLearning':
      // Get active tab info
      chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        if (tabs && tabs.length > 0) {
          // Tell the content script to stop recording
          chrome.tabs.sendMessage(tabs[0].id, {action: 'stopRecording'});
          
          // Notify popup (and any other listeners) about the status change
          chrome.runtime.sendMessage({ 
            action: "learningStatusChanged", 
            isLearning: false 
          });
          
          // End the current learning session
          endLearningSession()
            .then((response) => {
              console.log('Learning session ended:', response);
              sendResponse({
                success: true,
                message: 'Learning stopped',
                sessionId: response.sessionId
              });
            })
            .catch((error) => {
              console.error('Error stopping learning:', error);
              sendResponse({
                success: false,
                message: error.message
              });
            });
        } else {
          sendResponse({
            success: false,
            message: 'No active tab found'
          });
        }
      });
      break;
      
    case 'isRecording':
      if (currentSession) {
        sendResponse({ isRecording: true });
      } else {
        // If we're not sure, ask the content script
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
          if (tabs && tabs.length > 0) {
            chrome.tabs.sendMessage(tabs[0].id, {action: 'checkRecordingStatus'}, function(response) {
              if (response && response.isRecording) {
                sendResponse({ isRecording: true });
              } else {
                sendResponse({ isRecording: false });
              }
            });
          } else {
            sendResponse({ isRecording: false });
          }
        });
      }
      break;
  }
  
  // Keep the message channel open for async response
  return true;
});

/**
 * Start a new learning session
 */
async function startLearningSession(url, pageTitle) {
  // If there's already an active session, return error
  if (currentSession) {
    return { 
      status: 'error', 
      message: 'A learning session is already active' 
    };
  }
  
  // Create new session
  currentSession = {
    sessionId: generateId(),
    startTime: new Date().toISOString(),
    url: url,
    pageTitle: pageTitle,
    events: [],
    fields: new Map(),
    formSubmissions: []
  };
  
  // Store session in local storage
  await chrome.storage.local.set({ [SESSION_STORAGE_KEY]: currentSession });
  
  console.log('Started learning session:', currentSession.sessionId);
  
  // Try to communicate with backend
  try {
    const response = await fetch(`${API_BASE_URL}/start-learning`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: currentSession.sessionId,
        url: url,
        page_title: pageTitle
      })
    });
    
    const data = await response.json();
    
    if (data.status === 'success') {
      console.log('Backend confirmed session start');
    } else {
      console.warn('Backend returned error on session start:', data.message);
    }
  } catch (error) {
    console.error('Failed to communicate with backend:', error);
    // Continue anyway - we'll store data locally
  }
  
  return { 
    status: 'success', 
    message: 'Learning session started', 
    sessionId: currentSession.sessionId 
  };
}

/**
 * End the current learning session
 */
async function endLearningSession() {
  if (!currentSession) {
    return { 
      status: 'error', 
      message: 'No active learning session' 
    };
  }
  
  // Finish session
  currentSession.endTime = new Date().toISOString();
  
  // Convert fields map to array for storage
  const fieldsArray = Array.from(currentSession.fields.entries())
    .map(([id, data]) => ({ id, ...data }));
  
  // Create the final session data
  const sessionData = {
    ...currentSession,
    fields: fieldsArray,
    fieldsCount: fieldsArray.length
  };
  
  // Add to learning data
  learningData.sessions.push(sessionData);
  learningData.fieldsLearned += fieldsArray.length;
  
  // Update storage
  await chrome.storage.local.set({ [LEARNING_DATA_KEY]: learningData });
  await chrome.storage.local.remove(SESSION_STORAGE_KEY);
  
  // Send data to backend
  try {
    const response = await fetch(`${API_BASE_URL}/finish-learning`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionData.sessionId,
        session_data: sessionData
      })
    });
    
    const data = await response.json();
    
    if (data.status === 'success') {
      console.log('Backend confirmed session end');
    } else {
      console.warn('Backend returned error on session end:', data.message);
    }
  } catch (error) {
    console.error('Failed to send session data to backend:', error);
    // Continue anyway - we have data stored locally
  }
  
  // Clear current session
  const completedSessionId = currentSession.sessionId;
  currentSession = null;
  
  return { 
    status: 'success', 
    message: 'Learning session completed', 
    sessionId: completedSessionId 
  };
}

/**
 * Record an event from the content script
 */
async function recordEvent(eventType, data, url, pageTitle) {
  if (!currentSession) {
    return { status: 'error', message: 'No active learning session' };
  }
  
  // Add event to session
  const event = {
    eventType,
    data,
    url,
    pageTitle,
    timestamp: new Date().toISOString()
  };
  
  currentSession.events.push(event);
  
  // Special handling for different event types
  switch (eventType) {
    case 'fieldDetected':
      // Store field metadata
      currentSession.fields.set(data.id, {
        metadata: data,
        values: []
      });
      break;
      
    case 'fieldValueChanged':
      // Store field value changes
      if (currentSession.fields.has(data.fieldId)) {
        const field = currentSession.fields.get(data.fieldId);
        field.values.push({
          value: data.value,
          timestamp: data.timestamp
        });
        currentSession.fields.set(data.fieldId, field);
      }
      break;
      
    case 'formSubmission':
      // Store form submission
      currentSession.formSubmissions.push(data);
      break;
  }
  
  // Update storage
  await chrome.storage.local.set({ [SESSION_STORAGE_KEY]: currentSession });
  
  return { status: 'success', message: 'Event recorded' };
}

/**
 * Get learning status
 */
async function getLearningStatus() {
  return {
    status: 'success',
    isRecording: currentSession !== null,
    currentSession: currentSession ? currentSession.sessionId : null,
    sessionsCompleted: learningData.sessions.length,
    fieldsLearned: learningData.fieldsLearned,
    lastAnalyzed: learningData.lastAnalyzed,
    progress: Math.min(Math.round((learningData.sessions.length / 3) * 100), 100)
  };
}

/**
 * Analyze learning data and generate patterns
 */
async function analyzeLearning() {
  if (learningData.sessions.length === 0) {
    return { 
      status: 'error', 
      message: 'No learning sessions available for analysis' 
    };
  }
  
  // Try to send data to backend for analysis
  try {
    const response = await fetch(`${API_BASE_URL}/analyze-learning`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sessions: learningData.sessions
      })
    });
    
    const data = await response.json();
    
    if (data.status === 'success') {
      // Update last analyzed timestamp
      learningData.lastAnalyzed = new Date().toISOString();
      await chrome.storage.local.set({ [LEARNING_DATA_KEY]: learningData });
      
      return { 
        status: 'success', 
        message: 'Learning data analyzed successfully',
        patterns: data.patterns
      };
    } else {
      return { 
        status: 'error', 
        message: data.message || 'Analysis failed' 
      };
    }
  } catch (error) {
    console.error('Failed to analyze learning data:', error);
    return { 
      status: 'error', 
      message: 'Failed to communicate with backend for analysis' 
    };
  }
}

/**
 * Load stored data from local storage
 */
async function loadStoredData() {
  try {
    const result = await chrome.storage.local.get([SESSION_STORAGE_KEY, LEARNING_DATA_KEY]);
    
    if (result[SESSION_STORAGE_KEY]) {
      currentSession = result[SESSION_STORAGE_KEY];
      console.log('Restored active session:', currentSession.sessionId);
    }
    
    if (result[LEARNING_DATA_KEY]) {
      learningData = result[LEARNING_DATA_KEY];
      console.log('Loaded learning data:', learningData.sessions.length, 'sessions');
    }
  } catch (error) {
    console.error('Error loading stored data:', error);
  }
}

/**
 * Generate a unique ID
 */
function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substring(2);
}

/**
 * Export all learning data as a downloadable JSON file
 */
async function exportLearningData() {
  try {
    // Get the current session if any
    let allData = { ...learningData };
    
    // If there's an active session, include it
    if (currentSession) {
      // Convert fields Map to array for serialization
      const fieldsArray = Array.from(currentSession.fields.entries())
        .map(([id, data]) => ({ id, ...data }));
      
      allData.currentSession = {
        ...currentSession,
        fields: fieldsArray
      };
    }
    
    // Create a JSON blob
    const jsonString = JSON.stringify(allData, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    // Create a download link and trigger it
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `job_application_data_${timestamp}.json`;
    
    // Use chrome.downloads API to download the file
    chrome.downloads.download({
      url: url,
      filename: filename,
      saveAs: false
    });
    
    return { status: 'success' };
  } catch (error) {
    console.error('Error exporting data:', error);
    throw error;
  }
} 