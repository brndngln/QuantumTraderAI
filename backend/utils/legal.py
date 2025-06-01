import logging
from datetime import datetime
from typing import Dict, Any
import json
import os
from pathlib import Path

class LegalProtector:
    """Class for handling legal compliance and user protection"""
    
    def __init__(self):
        """Initialize legal protection system"""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Legal status tracking
        self.disclaimer_shown = False
        self.user_agreement_accepted = False
        self.last_disclaimer_check = None
        self.last_agreement_check = None
        
        # Load legal documents
        self.disclaimer = self._load_legal_document('disclaimer.txt')
        self.user_agreement = self._load_legal_document('user_agreement.txt')
        self.privacy_policy = self._load_legal_document('privacy_policy.txt')
        
        # Create compliance directory if it doesn't exist
        self.compliance_dir = Path(__file__).parent.parent / 'compliance'
        self.compliance_dir.mkdir(exist_ok=True)
        
        self.logger.info("Legal protection system initialized")
    
    def _load_legal_document(self, filename: str) -> str:
        """Load legal document from file"""
        try:
            path = Path(__file__).parent.parent / 'docs' / filename
            if path.exists():
                with open(path, 'r') as f:
                    return f.read()
            return ""  # Return empty string if file not found
        except Exception as e:
            self.logger.error(f"Error loading legal document {filename}: {str(e)}")
            return ""
    
    def show_disclaimer(self) -> bool:
        """Show disclaimer to user and get acceptance"""
        try:
            if not self.disclaimer:
                self.logger.warning("No disclaimer text available")
                return False
                
            # Log disclaimer display
            self.logger.info("Showing disclaimer to user")
            self.last_disclaimer_check = datetime.now()
            
            # Store disclaimer acceptance
            self.disclaimer_shown = True
            
            # Save compliance record
            self._save_compliance_record('disclaimer_shown', {
                'timestamp': datetime.now().isoformat(),
                'status': True
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error showing disclaimer: {str(e)}")
            return False
    
    def require_user_agreement(self) -> bool:
        """Require user to accept terms of service"""
        try:
            if not self.user_agreement:
                self.logger.warning("No user agreement text available")
                return False
                
            # Log agreement requirement
            self.logger.info("Requiring user agreement")
            self.last_agreement_check = datetime.now()
            
            # Store agreement acceptance
            self.user_agreement_accepted = True
            
            # Save compliance record
            self._save_compliance_record('agreement_accepted', {
                'timestamp': datetime.now().isoformat(),
                'status': True
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error requiring user agreement: {str(e)}")
            return False
    
    def validate_usage(self) -> Dict[str, Any]:
        """Validate legal compliance before usage"""
        try:
            validation = {
                'disclaimer_accepted': self.disclaimer_shown,
                'agreement_accepted': self.user_agreement_accepted,
                'last_checks': {
                    'disclaimer': str(self.last_disclaimer_check),
                    'agreement': str(self.last_agreement_check)
                }
            }
            
            if not all([self.disclaimer_shown, self.user_agreement_accepted]):
                self.logger.warning("Legal requirements not met")
                return validation
                
            self.logger.info("Legal requirements validated successfully")
            return validation
            
        except Exception as e:
            self.logger.error(f"Error validating usage: {str(e)}")
            return {'error': str(e)}
    
    def _save_compliance_record(self, record_type: str, data: Dict[str, Any]) -> None:
        """Save compliance record to file"""
        try:
            filename = f"compliance_{record_type}_{datetime.now().strftime('%Y%m%d')}.json"
            filepath = self.compliance_dir / filename
            
            record = {
                'type': record_type,
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            with open(filepath, 'a') as f:
                f.write(json.dumps(record) + '\n')
            
            self.logger.info(f"Saved compliance record: {record_type}")
            
        except Exception as e:
            self.logger.error(f"Error saving compliance record: {str(e)}")
    
    def log_action(self, action_type: str, details: Dict[str, Any]) -> None:
        """Log user actions for compliance"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'action_type': action_type,
                'details': details,
                'legal_status': self.validate_usage()
            }
            
            # Save to compliance log
            log_path = self.compliance_dir / 'compliance_actions.log'
            with open(log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            self.logger.info(f"Logged action: {action_type}")
            
        except Exception as e:
            self.logger.error(f"Error logging action: {str(e)}")
    
    def get_disclaimer(self) -> str:
        """Get disclaimer text"""
        return self.disclaimer
    
    def get_user_agreement(self) -> str:
        """Get user agreement text"""
        return self.user_agreement
    
    def get_privacy_policy(self) -> str:
        """Get privacy policy text"""
        return self.privacy_policy
    
    def check_compliance(self) -> Dict[str, Any]:
        """Check overall compliance status"""
        try:
            compliance_status = {
                'legal_documents': {
                    'disclaimer': bool(self.disclaimer),
                    'agreement': bool(self.user_agreement),
                    'privacy': bool(self.privacy_policy)
                },
                'user_status': {
                    'disclaimer_accepted': self.disclaimer_shown,
                    'agreement_accepted': self.user_agreement_accepted
                },
                'last_checks': {
                    'disclaimer': str(self.last_disclaimer_check),
                    'agreement': str(self.last_agreement_check)
                },
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info("Checked compliance status")
            return compliance_status
            
        except Exception as e:
            self.logger.error(f"Error checking compliance: {str(e)}")
            return {'error': str(e)}
