def fix_legal():
    file_path = 'backend/utils/legal.py'
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix get_disclaimer indentation
    content = content.replace('    def get_disclaimer(self) -> str:\n        """Get disclaimer text    """\n        return self.disclaimer',
                           '    def get_disclaimer(self) -> str:\n        """\n        Get disclaimer text\n        """\n        return self.disclaimer')
    
    # Fix get_user_agreement indentation
    content = content.replace('    def get_user_agreement(self) -> str:\n        """Get user agreement text    """\n        return self.user_agreement',
                           '    def get_user_agreement(self) -> str:\n        """\n        Get user agreement text\n        """\n        return self.user_agreement')
    
    # Fix get_privacy_policy indentation
    content = content.replace('    def get_privacy_policy(self) -> str:\n        """Get privacy policy text    """\n        return self.privacy_policy',
                           '    def get_privacy_policy(self) -> str:\n        """\n        Get privacy policy text\n        """\n        return self.privacy_policy')
    
    # Fix check_compliance indentation
    content = content.replace('    def check_compliance(self) -> Dict[str, Any]\n-> Dict[str, Any]:\n            """Check overall compliance status    """\n        try:\n            compliance_status = {\n                \'legal_documents\': {\n                    \'disclaimer\': self.get_disclaimer(),\n                    \'user_agreement\': self.get_user_agreement(),\n                    \'privacy_policy\': self.get_privacy_policy()\n                },\n                \'last_updated\': datetime.now().isoformat()\n            }\n            return compliance_status\n        except Exception as e:\n            self.logger.error(f"Error checking compliance: {str(e)}")\n            return {\'error\': str(e)}',
                           '    def check_compliance(self) -> Dict[str, Any]:\n        """\n        Check overall compliance status\n        """\n        try:\n            compliance_status = {\n                \'legal_documents\': {\n                    \'disclaimer\': self.get_disclaimer(),\n                    \'user_agreement\': self.get_user_agreement(),\n                    \'privacy_policy\': self.get_privacy_policy()\n                },\n                \'last_updated\': datetime.now().isoformat()\n            }\n            return compliance_status\n        except Exception as e:\n            self.logger.error(f"Error checking compliance: {str(e)}")\n            return {\'error\': str(e)}')
    
    with open(file_path, 'w') as f:
        f.write(content)

if __name__ == "__main__":
    fix_legal()
