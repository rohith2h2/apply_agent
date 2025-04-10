"""
Browser Controller
================
This module handles browser automation for interacting with job application websites.
"""

import os
import time
import logging
import json
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, ElementHandle

logger = logging.getLogger(__name__)

class BrowserController:
    """
    Controls browser interactions for automating job applications.
    """
    
    def __init__(self, headless: bool = False, slow_mo: int = 100):
        """
        Initialize the browser controller.
        
        Args:
            headless (bool): Whether to run the browser in headless mode
            slow_mo (int): Slow down operations by this many milliseconds
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.recording = False
        self.recorded_actions = []
    
    def start(self) -> bool:
        """
        Start the browser.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless, slow_mo=self.slow_mo)
            self.context = self.browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
            )
            self.page = self.context.new_page()
            
            # Set up page event listeners
            self._setup_event_listeners()
            
            logger.info("Browser started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start browser: {e}", exc_info=True)
            self.close()
            return False
    
    def close(self) -> None:
        """Close the browser and clean up resources."""
        try:
            if self.page:
                self.page.close()
                self.page = None
            
            if self.context:
                self.context.close()
                self.context = None
            
            if self.browser:
                self.browser.close()
                self.browser = None
            
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
            
            logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Error closing browser: {e}", exc_info=True)
    
    def _setup_event_listeners(self) -> None:
        """Set up event listeners for page events."""
        if not self.page:
            return
        
        # Log console messages
        self.page.on("console", lambda msg: logger.debug(f"Console {msg.type}: {msg.text}"))
        
        # Log page errors
        self.page.on("pageerror", lambda err: logger.error(f"Page error: {err}"))
        
        # Log request/response for debugging
        self.page.on("request", lambda request: logger.debug(f"Request: {request.method} {request.url}"))
        self.page.on("response", lambda response: logger.debug(f"Response: {response.status} {response.url}"))
    
    def navigate(self, url: str) -> bool:
        """
        Navigate to a URL.
        
        Args:
            url (str): The URL to navigate to
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.page:
            logger.error("Browser not started")
            return False
        
        try:
            response = self.page.goto(url, wait_until="networkidle", timeout=60000)
            if not response:
                logger.warning(f"Failed to get response from {url}")
                return False
            
            if response.status >= 400:
                logger.warning(f"Got status code {response.status} from {url}")
                return False
            
            logger.info(f"Navigated to {url}")
            
            if self.recording:
                self.recorded_actions.append({
                    "action_type": "navigate",
                    "url": url,
                    "timestamp": time.time()
                })
            
            return True
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}", exc_info=True)
            return False
    
    def fill_form_field(self, selector: str, value: str) -> bool:
        """
        Fill a form field.
        
        Args:
            selector (str): CSS selector for the field
            value (str): Value to fill in
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.page:
            logger.error("Browser not started")
            return False
        
        try:
            # Wait for the element to be visible
            self.page.wait_for_selector(selector, state="visible", timeout=10000)
            
            # Clear the field first
            self.page.fill(selector, "")
            
            # Fill the field
            self.page.fill(selector, value)
            
            logger.info(f"Filled form field {selector} with value: {value}")
            
            if self.recording:
                self.recorded_actions.append({
                    "action_type": "fill",
                    "selector": selector,
                    "value": value,
                    "timestamp": time.time()
                })
            
            return True
        except Exception as e:
            logger.error(f"Failed to fill form field {selector}: {e}", exc_info=True)
            return False
    
    def click(self, selector: str) -> bool:
        """
        Click on an element.
        
        Args:
            selector (str): CSS selector for the element
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.page:
            logger.error("Browser not started")
            return False
        
        try:
            # Wait for the element to be visible
            self.page.wait_for_selector(selector, state="visible", timeout=10000)
            
            # Click the element
            self.page.click(selector)
            
            logger.info(f"Clicked on element {selector}")
            
            if self.recording:
                self.recorded_actions.append({
                    "action_type": "click",
                    "selector": selector,
                    "timestamp": time.time()
                })
            
            return True
        except Exception as e:
            logger.error(f"Failed to click on element {selector}: {e}", exc_info=True)
            return False
    
    def select_option(self, selector: str, option: Union[str, List[str]]) -> bool:
        """
        Select an option from a dropdown.
        
        Args:
            selector (str): CSS selector for the dropdown
            option (Union[str, List[str]]): Option(s) to select
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.page:
            logger.error("Browser not started")
            return False
        
        try:
            # Wait for the element to be visible
            self.page.wait_for_selector(selector, state="visible", timeout=10000)
            
            # Select the option
            self.page.select_option(selector, option)
            
            logger.info(f"Selected option {option} from dropdown {selector}")
            
            if self.recording:
                self.recorded_actions.append({
                    "action_type": "select",
                    "selector": selector,
                    "option": option,
                    "timestamp": time.time()
                })
            
            return True
        except Exception as e:
            logger.error(f"Failed to select option from dropdown {selector}: {e}", exc_info=True)
            return False
    
    def check(self, selector: str, checked: bool = True) -> bool:
        """
        Check or uncheck a checkbox.
        
        Args:
            selector (str): CSS selector for the checkbox
            checked (bool): Whether to check or uncheck
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.page:
            logger.error("Browser not started")
            return False
        
        try:
            # Wait for the element to be visible
            self.page.wait_for_selector(selector, state="visible", timeout=10000)
            
            # Check or uncheck the checkbox
            self.page.set_checked(selector, checked)
            
            logger.info(f"{'Checked' if checked else 'Unchecked'} checkbox {selector}")
            
            if self.recording:
                self.recorded_actions.append({
                    "action_type": "check",
                    "selector": selector,
                    "checked": checked,
                    "timestamp": time.time()
                })
            
            return True
        except Exception as e:
            logger.error(f"Failed to {'check' if checked else 'uncheck'} checkbox {selector}: {e}", exc_info=True)
            return False
    
    def upload_file(self, selector: str, file_path: str) -> bool:
        """
        Upload a file.
        
        Args:
            selector (str): CSS selector for the file input
            file_path (str): Path to the file to upload
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.page:
            logger.error("Browser not started")
            return False
        
        try:
            # Wait for the element to be visible
            self.page.wait_for_selector(selector, timeout=10000)
            
            # Upload the file
            self.page.set_input_files(selector, file_path)
            
            logger.info(f"Uploaded file {file_path} to input {selector}")
            
            if self.recording:
                self.recorded_actions.append({
                    "action_type": "upload",
                    "selector": selector,
                    "file_path": file_path,
                    "timestamp": time.time()
                })
            
            return True
        except Exception as e:
            logger.error(f"Failed to upload file to input {selector}: {e}", exc_info=True)
            return False
    
    def wait_for_navigation(self, timeout: int = 30000) -> bool:
        """
        Wait for navigation to complete.
        
        Args:
            timeout (int): Timeout in milliseconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.page:
            logger.error("Browser not started")
            return False
        
        try:
            self.page.wait_for_load_state("networkidle", timeout=timeout)
            logger.info("Navigation completed")
            return True
        except Exception as e:
            logger.error(f"Failed to wait for navigation: {e}", exc_info=True)
            return False
    
    def wait_for_selector(self, selector: str, timeout: int = 10000) -> bool:
        """
        Wait for an element to appear.
        
        Args:
            selector (str): CSS selector for the element
            timeout (int): Timeout in milliseconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.page:
            logger.error("Browser not started")
            return False
        
        try:
            self.page.wait_for_selector(selector, state="visible", timeout=timeout)
            logger.info(f"Element {selector} appeared")
            return True
        except Exception as e:
            logger.error(f"Element {selector} did not appear: {e}", exc_info=True)
            return False
    
    def get_element_text(self, selector: str) -> Optional[str]:
        """
        Get the text content of an element.
        
        Args:
            selector (str): CSS selector for the element
            
        Returns:
            Optional[str]: The text content, or None if not found
        """
        if not self.page:
            logger.error("Browser not started")
            return None
        
        try:
            element = self.page.wait_for_selector(selector, state="visible", timeout=10000)
            if not element:
                logger.warning(f"Element {selector} not found")
                return None
            
            text = element.text_content()
            return text.strip() if text else ""
        except Exception as e:
            logger.error(f"Failed to get text from element {selector}: {e}", exc_info=True)
            return None
    
    def get_element_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """
        Get an attribute of an element.
        
        Args:
            selector (str): CSS selector for the element
            attribute (str): Attribute name
            
        Returns:
            Optional[str]: The attribute value, or None if not found
        """
        if not self.page:
            logger.error("Browser not started")
            return None
        
        try:
            element = self.page.wait_for_selector(selector, state="visible", timeout=10000)
            if not element:
                logger.warning(f"Element {selector} not found")
                return None
            
            return element.get_attribute(attribute)
        except Exception as e:
            logger.error(f"Failed to get attribute from element {selector}: {e}", exc_info=True)
            return None
    
    def take_screenshot(self, path: str) -> bool:
        """
        Take a screenshot and save it to a file.
        
        Args:
            path (str): Path to save the screenshot
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.page:
            logger.error("Browser not started")
            return False
        
        try:
            self.page.screenshot(path=path)
            logger.info(f"Took screenshot and saved to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}", exc_info=True)
            return False
    
    def start_recording(self) -> bool:
        """
        Start recording actions for later playback.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self.recording:
            logger.warning("Already recording")
            return False
        
        self.recording = True
        self.recorded_actions = []
        logger.info("Started recording actions")
        return True
    
    def stop_recording(self) -> List[Dict[str, Any]]:
        """
        Stop recording actions.
        
        Returns:
            List[Dict[str, Any]]: The recorded actions
        """
        if not self.recording:
            logger.warning("Not recording")
            return []
        
        self.recording = False
        actions = self.recorded_actions.copy()
        logger.info(f"Stopped recording actions ({len(actions)} actions recorded)")
        return actions
    
    def save_recorded_actions(self, path: str) -> bool:
        """
        Save recorded actions to a file.
        
        Args:
            path (str): Path to save the actions
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(path, 'w') as f:
                json.dump(self.recorded_actions, f, indent=4)
            
            logger.info(f"Saved {len(self.recorded_actions)} recorded actions to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save recorded actions: {e}", exc_info=True)
            return False
    
    def load_recorded_actions(self, path: str) -> List[Dict[str, Any]]:
        """
        Load recorded actions from a file.
        
        Args:
            path (str): Path to load the actions from
            
        Returns:
            List[Dict[str, Any]]: The loaded actions
        """
        try:
            with open(path, 'r') as f:
                actions = json.load(f)
            
            logger.info(f"Loaded {len(actions)} recorded actions from {path}")
            return actions
        except Exception as e:
            logger.error(f"Failed to load recorded actions: {e}", exc_info=True)
            return []
    
    def replay_actions(self, actions: List[Dict[str, Any]], delay: float = 0.5) -> bool:
        """
        Replay recorded actions.
        
        Args:
            actions (List[Dict[str, Any]]): Actions to replay
            delay (float): Delay between actions in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.page:
            logger.error("Browser not started")
            return False
        
        for i, action in enumerate(actions, 1):
            try:
                logger.info(f"Replaying action {i}/{len(actions)}: {action['action_type']}")
                
                if action["action_type"] == "navigate":
                    self.navigate(action["url"])
                
                elif action["action_type"] == "fill":
                    self.fill_form_field(action["selector"], action["value"])
                
                elif action["action_type"] == "click":
                    self.click(action["selector"])
                
                elif action["action_type"] == "select":
                    self.select_option(action["selector"], action["option"])
                
                elif action["action_type"] == "check":
                    self.check(action["selector"], action.get("checked", True))
                
                elif action["action_type"] == "upload":
                    self.upload_file(action["selector"], action["file_path"])
                
                # Wait between actions
                time.sleep(delay)
            
            except Exception as e:
                logger.error(f"Failed to replay action {i}/{len(actions)}: {e}", exc_info=True)
                return False
        
        logger.info(f"Successfully replayed {len(actions)} actions")
        return True
    
    def extract_form_fields(self) -> List[Dict[str, Any]]:
        """
        Extract form fields from the current page.
        
        Returns:
            List[Dict[str, Any]]: List of form fields with their properties
        """
        if not self.page:
            logger.error("Browser not started")
            return []
        
        try:
            # Run JavaScript to extract form field information
            fields = self.page.evaluate("""() => {
                const fields = [];
                
                // Get all input elements
                const inputs = document.querySelectorAll('input, textarea, select');
                
                for (const input of inputs) {
                    // Skip hidden fields and submit buttons
                    if (input.type === 'hidden' || input.type === 'submit' || input.type === 'button') {
                        continue;
                    }
                    
                    const field = {
                        type: input.tagName.toLowerCase() === 'select' ? 'select' : input.type,
                        name: input.name || '',
                        id: input.id || '',
                        selector: input.id ? `#${input.id}` : input.name ? `[name="${input.name}"]` : '',
                        placeholder: input.placeholder || '',
                        value: input.value || '',
                        required: input.required || false,
                        disabled: input.disabled || false,
                        options: []
                    };
                    
                    // Get label text
                    if (input.id) {
                        const label = document.querySelector(`label[for="${input.id}"]`);
                        if (label) {
                            field.label = label.textContent.trim();
                        }
                    }
                    
                    // For select elements, get options
                    if (input.tagName.toLowerCase() === 'select') {
                        for (const option of input.options) {
                            field.options.push({
                                value: option.value,
                                text: option.textContent.trim(),
                                selected: option.selected
                            });
                        }
                    }
                    
                    fields.push(field);
                }
                
                return fields;
            }""")
            
            logger.info(f"Extracted {len(fields)} form fields from the current page")
            return fields
        
        except Exception as e:
            logger.error(f"Failed to extract form fields: {e}", exc_info=True)
            return [] 