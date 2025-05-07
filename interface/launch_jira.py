#!/usr/bin/env python
# Launch script for the Jira Test Case Generator UI
import sys
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import logging
import traceback

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import project modules
try:
    from src.generator import generate_test_cases_from_user_story
    from config import settings
except ImportError as e:
    print(f"Error importing project modules: {str(e)}")
    print("Make sure you're running this script from the project root directory.")
    sys.exit(1)

# Set up logging
logger = logging.getLogger(__name__)

class TestCaseGeneratorApp:
    def __init__(self, root):
        """Initialize the application UI"""
        self.root = root
        self.root.title("Test Case Generator v2")
        self.root.geometry("800x600")
        
        # Main frame
        main_frame = ttk.Frame(root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Input frame
        input_frame = ttk.LabelFrame(main_frame, text="User Story", padding=10)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # User Story ID input
        ttk.Label(input_frame, text="Jira User Story ID:").grid(column=0, row=0, sticky=tk.W, padx=5, pady=5)
        self.user_story_id = ttk.Entry(input_frame, width=20)
        self.user_story_id.grid(column=1, row=0, sticky=tk.W, padx=5, pady=5)
        
        # Button frame
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(column=2, row=0, padx=5, pady=5)
        
        # Submit button
        self.submit_button = ttk.Button(button_frame, text="Generate Test Cases", command=self.on_submit)
        self.submit_button.pack(side=tk.LEFT, padx=5)
        
        # Progress indicator
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=100, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=5, pady=5)
        
        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Results text area
        self.results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD, height=20)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        self.results_text.config(state=tk.DISABLED)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Set focus to the entry
        self.user_story_id.focus_set()
        
        # Bind Enter key to submit
        self.root.bind('<Return>', lambda event: self.on_submit())
        
        # Display initial information
        self.update_results("Welcome to Test Case Generator v2!\n\n"
                           "Enter a Jira User Story ID (e.g., PT-123) in the field above and "
                           "click 'Generate Test Cases' to start.\n\n"
                           f"Using Claude model: {settings.claude['apiModel']}\n"
                           f"Project key: {settings.jira['projectKey']}\n")
    
    def update_results(self, text):
        """Update the results text area"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, text)
        self.results_text.config(state=tk.DISABLED)
        self.results_text.see(tk.END)
    
    def append_results(self, text):
        """Append text to the results text area"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.insert(tk.END, text)
        self.results_text.config(state=tk.DISABLED)
        self.results_text.see(tk.END)
    
    def on_submit(self):
        """Handle the submit button click event"""
        # Get the user story ID
        user_story_id = self.user_story_id.get().strip()
        
        if not user_story_id:
            messagebox.showerror("Error", "Please enter a User Story ID")
            return
        
        # Clear results and update status
        self.update_results(f"Generating test cases for {user_story_id}...\n\n")
        self.status_var.set(f"Processing {user_story_id}...")
        
        # Disable submit button and show progress
        self.submit_button.config(state=tk.DISABLED)
        self.progress.start()
        
        # Start generation in a separate thread
        threading.Thread(target=self.generate_test_cases, args=(user_story_id,), daemon=True).start()
    
    def generate_test_cases(self, user_story_id):
        """Generate test cases in a separate thread"""
        try:
            # Call the generation function
            results = generate_test_cases_from_user_story(user_story_id)
            
            # Process results
            self.root.after(0, lambda: self.process_results(results))
        except Exception as e:
            error_message = f"Error: {str(e)}\n\n{traceback.format_exc()}"
            logger.error(error_message)
            self.root.after(0, lambda: self.show_error(error_message))
    
    def process_results(self, results):
        """Process and display the generation results"""
        # Stop progress indicator
        self.progress.stop()
        
        # Prepare results text
        result_text = f"User Story: {results['title']} ({results['userStory']})\n\n"
        result_text += f"Generated {len(results['testCases'])} test cases\n"
        result_text += f"Successfully imported: {sum(1 for tc in results['testCases'] if tc['success'])}\n\n"
        
        result_text += "Test Cases:\n"
        for i, tc in enumerate(results['testCases']):
            if tc['success']:
                result_text += f"{i + 1}. {tc['testCase']} -> {tc['key']}\n"
            else:
                result_text += f"{i + 1}. {tc['testCase']} -> Import Failed: {tc.get('error', 'Unknown error')}\n"
        
        # Update UI
        self.update_results(result_text)
        self.status_var.set(f"Completed: {len(results['testCases'])} test cases generated")
        self.submit_button.config(state=tk.NORMAL)
        
        # Show success message
        messagebox.showinfo("Success", f"Generated {len(results['testCases'])} test cases for {results['userStory']}")
    
    def show_error(self, error_message):
        """Display an error message"""
        # Stop progress indicator
        self.progress.stop()
        
        # Update UI
        self.update_results(f"Error occurred:\n\n{error_message}")
        self.status_var.set("Error occurred")
        self.submit_button.config(state=tk.NORMAL)
        
        # Show error message
        messagebox.showerror("Error", f"An error occurred:\n\n{error_message[:200]}...")

def main():
    """Main entry point for the application"""
    # Configure logging
    logging.basicConfig(level=logging.INFO,
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    try:
        # Create the Tkinter root window
        root = tk.Tk()
        app = TestCaseGeneratorApp(root)
        
        # Set window icon if available
        try:
            icon_path = os.path.join(current_dir, "assets", "icon.ico")
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
        except:
            pass
        
        # Start the main event loop
        root.mainloop()
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        messagebox.showerror("Error", f"An unexpected error occurred:\n\n{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()