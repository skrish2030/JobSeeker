import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add JobSeeker directory to path
sys.path.insert(0, r"C:\Users\skris\OneDrive\Desktop\JobSeeker")

class TestAutoApplier(unittest.TestCase):
    
    def test_resume_not_exist(self):
        from backend.auto_applier import run_auto_apply
        profile = {
            "candidate_first_name": "John",
            "candidate_last_name": "Doe",
            "candidate_email": "john.doe@example.com",
            "resume_file_path": "non_existent_file.pdf"
        }
        res = run_auto_apply("https://boards.greenhouse.io/stripe/jobs/123", "Stripe", profile)
        self.assertEqual(res["status"], "error")
        self.assertIn("does not exist", res["message"])
        
    @patch('backend.auto_applier.time.sleep')
    @patch('backend.auto_applier.sync_playwright')
    def test_auto_apply_greenhouse_mock(self, mock_playwright, mock_sleep):
        # Create a mock structure for Playwright
        mock_p = mock_playwright.return_value.__enter__.return_value
        mock_browser = mock_p.chromium.launch.return_value
        mock_context = mock_browser.new_context.return_value
        mock_page = mock_context.new_page.return_value
        
        # Mock locators to prevent failures during heuristic lookups and type errors
        mock_locator = MagicMock()
        mock_locator.count.return_value = 1  # count() returns integer to avoid comparison error
        mock_locator.first.count.return_value = 1  # first.count() also returns integer
        mock_page.get_by_label.return_value = mock_locator
        mock_page.get_by_placeholder.return_value = mock_locator
        mock_page.locator.return_value = mock_locator
        
        # Mock file existence check
        with patch('backend.auto_applier.os.path.exists', return_value=True):
            from backend.auto_applier import run_auto_apply
            
            profile = {
                "candidate_first_name": "John",
                "candidate_last_name": "Doe",
                "candidate_email": "john.doe@example.com",
                "resume_file_path": "C:\\fake\\resume.pdf"
            }
            
            # Preview mode
            res = run_auto_apply("https://boards.greenhouse.io/stripe/jobs/123", "Stripe", profile, mode="preview")
            
            # Check status is preview
            self.assertEqual(res["status"], "preview")
            
            # Verify browser launched in headed mode
            mock_p.chromium.launch.assert_called_once_with(headless=False)
            mock_page.goto.assert_called_once_with("https://boards.greenhouse.io/stripe/jobs/123", timeout=30000)
            mock_sleep.assert_called_once_with(300)

if __name__ == '__main__':
    unittest.main()
