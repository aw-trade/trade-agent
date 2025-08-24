"""Safe template formatting with automatic variable generation."""

import re
from typing import Dict, Any, Set
from datetime import datetime

from config.settings import settings
from config.validation import ValidationError, sanitize_name_for_class, sanitize_trading_terms


class TemplateFormattingError(Exception):
    """Exception raised when template formatting fails."""
    pass


class TemplateFormatter:
    """Handles safe template formatting with intelligent defaults."""
    
    def __init__(self):
        self.default_generators = {
            'strategy_name': self._generate_strategy_name,
            'strategy_description': self._generate_strategy_description,
            'strategy_class_name': self._generate_class_name,
            'project_name': self._generate_project_name,
            'base_name': self._generate_base_name,
        }
    
    def extract_template_variables(self, template_str: str) -> Set[str]:
        """Extract all {variable} placeholders from template string."""
        return set(re.findall(r'\{(\w+)\}', template_str))
    
    def generate_missing_values(self, required_vars: Set[str], provided_params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate intelligent defaults for missing template variables."""
        missing_vars = required_vars - set(provided_params.keys())
        generated = {}
        
        for var in missing_vars:
            if var in self.default_generators:
                generated[var] = self.default_generators[var](provided_params)
            elif var in settings.template_values:
                generated[var] = settings.template_values[var]
            else:
                generated[var] = self._generate_generic_default(var)
        
        return generated
    
    def safe_format(self, template_str: str, params: Dict[str, Any]) -> str:
        """Safely format template with auto-generated defaults for missing variables."""
        try:
            # Extract required variables from template
            required_vars = self.extract_template_variables(template_str)
            
            # Generate missing values
            missing_values = self.generate_missing_values(required_vars, params)
            
            # Combine provided params with generated defaults
            all_params = {**missing_values, **params}  # params override defaults
            
            # Process string values to handle multiline content
            processed_params = self._process_string_values(all_params)
            
            # Format the template
            return template_str.format(**processed_params)
            
        except KeyError as e:
            raise TemplateFormattingError(f"Template formatting failed - missing variable: {e}")
        except ValueError as e:
            raise TemplateFormattingError(f"Template formatting failed - invalid format: {e}")
        except Exception as e:
            raise TemplateFormattingError(f"Template formatting error: {str(e)}")
    
    def _process_string_values(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Process string values to handle multiline content and special cases."""
        processed = {}
        
        for key, value in params.items():
            if isinstance(value, str) and '\n' in value and 'description' in key.lower():
                # Convert multiline descriptions to single line comments
                lines = [line.strip() for line in value.split('\n') if line.strip()]
                processed[key] = ' '.join(lines)
            elif isinstance(value, bool):
                processed[key] = str(value).lower()
            elif value is None:
                processed[key] = ""
            else:
                processed[key] = str(value)
        
        return processed
    
    def _generate_strategy_name(self, params: Dict[str, Any]) -> str:
        """Generate a strategy name from available parameters."""
        if 'strategy_description' in params:
            description = params['strategy_description']
            terms = sanitize_trading_terms(description)
            if terms:
                return ' '.join(term.capitalize() for term in terms) + ' Strategy'
        
        if 'base_name' in params:
            return params['base_name'].replace('-', ' ').title() + ' Strategy'
        
        return settings.template_values['strategy_name']
    
    def _generate_strategy_description(self, params: Dict[str, Any]) -> str:
        """Generate a strategy description from available parameters."""
        if 'strategy_description' in params:
            return params['strategy_description']
        
        return settings.template_values['strategy_description']
    
    def _generate_class_name(self, params: Dict[str, Any]) -> str:
        """Generate a class name from available parameters."""
        if 'strategy_name' in params:
            return sanitize_name_for_class(params['strategy_name'])
        
        if 'base_name' in params:
            return sanitize_name_for_class(params['base_name'])
        
        if 'strategy_description' in params:
            return sanitize_name_for_class(params['strategy_description'])
        
        return settings.template_values['strategy_class_name']
    
    def _generate_project_name(self, params: Dict[str, Any]) -> str:
        """Generate a project name with timestamp."""
        base_name = params.get('base_name', 'generic-algo')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{timestamp}"
    
    def _generate_base_name(self, params: Dict[str, Any]) -> str:
        """Generate a base name from strategy description."""
        if 'strategy_description' in params:
            description = params['strategy_description']
            terms = sanitize_trading_terms(description)
            if terms:
                return '-'.join(terms[:2])  # Use up to 2 trading terms
        
        return settings.template_values['base_name']
    
    def _generate_generic_default(self, var_name: str) -> str:
        """Generate a generic default value based on variable name patterns."""
        var_lower = var_name.lower()
        
        if 'threshold' in var_lower:
            return "0.5"
        elif 'period' in var_lower or 'lookback' in var_lower:
            return "5"
        elif 'cooldown' in var_lower or 'ms' in var_lower:
            return "100"
        elif 'port' in var_lower:
            return "3000"
        elif 'host' in var_lower or 'ip' in var_lower:
            return "127.0.0.1"
        elif 'name' in var_lower:
            return f"Generated_{var_name.replace('_', ' ').title()}"
        elif 'description' in var_lower:
            return f"Auto-generated {var_name.replace('_', ' ')}"
        elif 'version' in var_lower:
            return "0.1.0"
        elif 'author' in var_lower:
            return "AI Agent <agent@example.com>"
        elif 'timestamp' in var_lower or 'date' in var_lower:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            return f"default_{var_name}"


# Global template formatter instance
template_formatter = TemplateFormatter()