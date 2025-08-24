"""Template validation functionality."""

from typing import Dict, Any, Set, List, Tuple
import re

from config.validation import ValidationError


class TemplateValidationError(Exception):
    """Exception raised when template validation fails."""
    pass


class TemplateValidator:
    """Validates templates and their parameters."""
    
    def __init__(self):
        self.required_rust_variables = {
            'imbalance_threshold',
            'min_volume_threshold', 
            'lookback_periods',
            'signal_cooldown_ms'
        }
        
        self.required_cargo_variables = {
            'project_name',
            'strategy_description'
        }
        
        self.required_dockerfile_variables = set()  # Dockerfile templates may have fewer requirements
    
    def validate_rust_template(self, template_str: str) -> Tuple[bool, List[str]]:
        """Validate Rust template structure and required variables."""
        issues = []
        
        # Extract variables from template
        variables = set(re.findall(r'\{(\w+)\}', template_str))
        
        # Check for required variables
        missing_required = self.required_rust_variables - variables
        if missing_required:
            issues.append(f"Missing required variables: {', '.join(missing_required)}")
        
        # Check for Rust syntax patterns
        if 'use std::' not in template_str:
            issues.append("Template should include standard library imports")
        
        if 'fn main()' not in template_str:
            issues.append("Template should include main function")
        
        if 'struct' not in template_str:
            issues.append("Template should include struct definitions")
        
        # Check for UDP socket patterns (trading specific)
        if 'UdpSocket' not in template_str:
            issues.append("Template should include UDP socket functionality")
        
        return len(issues) == 0, issues
    
    def validate_cargo_template(self, template_str: str) -> Tuple[bool, List[str]]:
        """Validate Cargo.toml template structure."""
        issues = []
        
        # Extract variables from template
        variables = set(re.findall(r'\{(\w+)\}', template_str))
        
        # Check for required variables
        missing_required = self.required_cargo_variables - variables
        if missing_required:
            issues.append(f"Missing required variables: {', '.join(missing_required)}")
        
        # Check for required sections
        required_sections = ['[package]', '[dependencies]']
        for section in required_sections:
            if section not in template_str:
                issues.append(f"Missing required section: {section}")
        
        # Check for essential fields
        if 'name =' not in template_str:
            issues.append("Missing package name field")
        
        if 'version =' not in template_str:
            issues.append("Missing version field")
        
        return len(issues) == 0, issues
    
    def validate_dockerfile_template(self, template_str: str) -> Tuple[bool, List[str]]:
        """Validate Dockerfile template structure."""
        issues = []
        
        # Check for required Dockerfile instructions
        required_instructions = ['FROM', 'WORKDIR', 'COPY', 'RUN']
        for instruction in required_instructions:
            if instruction not in template_str.upper():
                issues.append(f"Missing required instruction: {instruction}")
        
        # Check for multi-stage build pattern (recommended)
        if 'FROM' not in template_str or template_str.upper().count('FROM') < 2:
            issues.append("Template should use multi-stage build for optimization")
        
        # Check for security best practices
        if 'USER' not in template_str.upper():
            issues.append("Template should include USER instruction for security")
        
        return len(issues) == 0, issues
    
    def validate_template_parameters(self, params: Dict[str, Any], template_type: str) -> Tuple[bool, List[str]]:
        """Validate parameters for a specific template type."""
        issues = []
        
        if template_type == 'rust':
            required_vars = self.required_rust_variables
        elif template_type == 'cargo':
            required_vars = self.required_cargo_variables
        elif template_type == 'dockerfile':
            required_vars = self.required_dockerfile_variables
        else:
            return False, [f"Unknown template type: {template_type}"]
        
        # Check for required parameters
        missing = required_vars - set(params.keys())
        if missing:
            issues.append(f"Missing required parameters: {', '.join(missing)}")
        
        # Validate parameter types and values
        for key, value in params.items():
            if key == 'project_name':
                if not isinstance(value, str) or not re.match(r'^[a-zA-Z0-9_-]+$', value):
                    issues.append("project_name must be alphanumeric with hyphens/underscores only")
            
            elif key == 'imbalance_threshold':
                if not isinstance(value, (int, float)) or not 0.0 <= float(value) <= 1.0:
                    issues.append("imbalance_threshold must be a number between 0.0 and 1.0")
            
            elif key == 'min_volume_threshold':
                if not isinstance(value, (int, float)) or float(value) < 0:
                    issues.append("min_volume_threshold must be a positive number")
            
            elif key == 'lookback_periods':
                if not isinstance(value, int) or value < 1:
                    issues.append("lookback_periods must be a positive integer")
            
            elif key == 'signal_cooldown_ms':
                if not isinstance(value, int) or value < 0:
                    issues.append("signal_cooldown_ms must be a non-negative integer")
        
        return len(issues) == 0, issues
    
    def validate_generated_rust_code(self, code: str) -> Tuple[bool, List[str]]:
        """Basic validation of generated Rust code."""
        issues = []
        
        # Check for balanced braces
        open_braces = code.count('{')
        close_braces = code.count('}')
        if open_braces != close_braces:
            issues.append(f"Unbalanced braces: {open_braces} opening, {close_braces} closing")
        
        # Check for balanced parentheses
        open_parens = code.count('(')
        close_parens = code.count(')')
        if open_parens != close_parens:
            issues.append(f"Unbalanced parentheses: {open_parens} opening, {close_parens} closing")
        
        # Check for main function
        if 'fn main()' not in code:
            issues.append("Generated code missing main function")
        
        # Check for basic syntax patterns
        if not re.search(r'use\s+std::', code):
            issues.append("Generated code missing standard library imports")
        
        # Check for potential syntax errors
        if '{{' in code or '}}' in code:
            issues.append("Generated code contains unresolved template variables")
        
        return len(issues) == 0, issues
    
    def get_template_requirements(self, template_type: str) -> Set[str]:
        """Get required variables for a template type."""
        if template_type == 'rust':
            return self.required_rust_variables.copy()
        elif template_type == 'cargo':
            return self.required_cargo_variables.copy()
        elif template_type == 'dockerfile':
            return self.required_dockerfile_variables.copy()
        else:
            return set()


# Global template validator instance
template_validator = TemplateValidator()