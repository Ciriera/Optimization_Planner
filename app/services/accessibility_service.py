"""
Accessibility service for WCAG 2.1 compliance
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json


class AccessibilityService:
    """
    Service for ensuring WCAG 2.1 accessibility compliance
    """
    
    def __init__(self):
        # WCAG 2.1 compliance levels
        self.wcag_levels = {
            "A": "Level A - Basic accessibility",
            "AA": "Level AA - Enhanced accessibility", 
            "AAA": "Level AAA - Maximum accessibility"
        }
        
        # Accessibility guidelines
        self.guidelines = {
            "perceivable": {
                "color_contrast": {
                    "AA": 4.5,  # Minimum contrast ratio for normal text
                    "AAA": 7.0   # Enhanced contrast ratio
                },
                "text_resize": "Text must be resizable up to 200% without loss of functionality",
                "alternative_text": "All images must have meaningful alternative text",
                "captions": "Video content must have captions"
            },
            "operable": {
                "keyboard_navigation": "All functionality must be accessible via keyboard",
                "focus_indicators": "Clear focus indicators must be visible",
                "no_seizure": "No content that flashes more than 3 times per second",
                "navigation": "Consistent navigation mechanisms"
            },
            "understandable": {
                "language": "Page language must be specified",
                "consistent_navigation": "Navigation must be consistent across pages",
                "error_identification": "Errors must be clearly identified and described",
                "labels": "All form inputs must have labels"
            },
            "robust": {
                "valid_markup": "HTML must be valid and well-formed",
                "compatible": "Content must work with current and future assistive technologies",
                "semantic_html": "Use semantic HTML elements appropriately"
            }
        }
    
    def audit_interface(self, interface_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Audit interface for WCAG 2.1 compliance.
        
        Args:
            interface_data: Interface components and their properties
            
        Returns:
            Accessibility audit results with compliance status
        """
        try:
            audit_results = {
                "overall_compliance": "unknown",
                "wcag_level": "AA",  # Target level
                "guidelines": {},
                "issues": [],
                "recommendations": [],
                "score": 0,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Audit each guideline category
            for category, guidelines in self.guidelines.items():
                category_results = self._audit_category(category, guidelines, interface_data)
                audit_results["guidelines"][category] = category_results
            
            # Calculate overall compliance
            audit_results = self._calculate_overall_compliance(audit_results)
            
            return audit_results
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Accessibility audit failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _audit_category(self, category: str, guidelines: Dict[str, Any], 
                       interface_data: Dict[str, Any]) -> Dict[str, Any]:
        """Audit a specific WCAG category."""
        category_results = {
            "compliance": "unknown",
            "score": 0,
            "issues": [],
            "recommendations": []
        }
        
        if category == "perceivable":
            category_results = self._audit_perceivable(guidelines, interface_data)
        elif category == "operable":
            category_results = self._audit_operable(guidelines, interface_data)
        elif category == "understandable":
            category_results = self._audit_understandable(guidelines, interface_data)
        elif category == "robust":
            category_results = self._audit_robust(guidelines, interface_data)
        
        return category_results
    
    def _audit_perceivable(self, guidelines: Dict[str, Any], 
                          interface_data: Dict[str, Any]) -> Dict[str, Any]:
        """Audit perceivable guidelines."""
        results = {
            "compliance": "unknown",
            "score": 0,
            "issues": [],
            "recommendations": []
        }
        
        components = interface_data.get("components", [])
        
        # Check color contrast
        contrast_issues = self._check_color_contrast(components, guidelines["color_contrast"])
        results["issues"].extend(contrast_issues)
        
        # Check alternative text
        alt_text_issues = self._check_alternative_text(components)
        results["issues"].extend(alt_text_issues)
        
        # Check text resize capability
        resize_issues = self._check_text_resize(components)
        results["issues"].extend(resize_issues)
        
        # Calculate score
        total_checks = 4
        passed_checks = total_checks - len(results["issues"])
        results["score"] = (passed_checks / total_checks) * 100
        
        # Determine compliance
        if results["score"] >= 95:
            results["compliance"] = "AAA"
        elif results["score"] >= 85:
            results["compliance"] = "AA"
        elif results["score"] >= 70:
            results["compliance"] = "A"
        else:
            results["compliance"] = "non-compliant"
        
        return results
    
    def _audit_operable(self, guidelines: Dict[str, Any], 
                       interface_data: Dict[str, Any]) -> Dict[str, Any]:
        """Audit operable guidelines."""
        results = {
            "compliance": "unknown",
            "score": 0,
            "issues": [],
            "recommendations": []
        }
        
        components = interface_data.get("components", [])
        
        # Check keyboard navigation
        keyboard_issues = self._check_keyboard_navigation(components)
        results["issues"].extend(keyboard_issues)
        
        # Check focus indicators
        focus_issues = self._check_focus_indicators(components)
        results["issues"].extend(focus_issues)
        
        # Check for seizure-inducing content
        seizure_issues = self._check_seizure_content(components)
        results["issues"].extend(seizure_issues)
        
        # Check navigation consistency
        navigation_issues = self._check_navigation_consistency(components)
        results["issues"].extend(navigation_issues)
        
        # Calculate score
        total_checks = 4
        passed_checks = total_checks - len(results["issues"])
        results["score"] = (passed_checks / total_checks) * 100
        
        # Determine compliance
        if results["score"] >= 95:
            results["compliance"] = "AAA"
        elif results["score"] >= 85:
            results["compliance"] = "AA"
        elif results["score"] >= 70:
            results["compliance"] = "A"
        else:
            results["compliance"] = "non-compliant"
        
        return results
    
    def _audit_understandable(self, guidelines: Dict[str, Any], 
                            interface_data: Dict[str, Any]) -> Dict[str, Any]:
        """Audit understandable guidelines."""
        results = {
            "compliance": "unknown",
            "score": 0,
            "issues": [],
            "recommendations": []
        }
        
        components = interface_data.get("components", [])
        
        # Check language specification
        language_issues = self._check_language_specification(interface_data)
        results["issues"].extend(language_issues)
        
        # Check error identification
        error_issues = self._check_error_identification(components)
        results["issues"].extend(error_issues)
        
        # Check form labels
        label_issues = self._check_form_labels(components)
        results["issues"].extend(label_issues)
        
        # Check consistent navigation
        consistency_issues = self._check_navigation_consistency(components)
        results["issues"].extend(consistency_issues)
        
        # Calculate score
        total_checks = 4
        passed_checks = total_checks - len(results["issues"])
        results["score"] = (passed_checks / total_checks) * 100
        
        # Determine compliance
        if results["score"] >= 95:
            results["compliance"] = "AAA"
        elif results["score"] >= 85:
            results["compliance"] = "AA"
        elif results["score"] >= 70:
            results["compliance"] = "A"
        else:
            results["compliance"] = "non-compliant"
        
        return results
    
    def _audit_robust(self, guidelines: Dict[str, Any], 
                     interface_data: Dict[str, Any]) -> Dict[str, Any]:
        """Audit robust guidelines."""
        results = {
            "compliance": "unknown",
            "score": 0,
            "issues": [],
            "recommendations": []
        }
        
        # Check HTML validity
        html_issues = self._check_html_validity(interface_data)
        results["issues"].extend(html_issues)
        
        # Check semantic HTML usage
        semantic_issues = self._check_semantic_html(interface_data)
        results["issues"].extend(semantic_issues)
        
        # Check compatibility
        compatibility_issues = self._check_compatibility(interface_data)
        results["issues"].extend(compatibility_issues)
        
        # Calculate score
        total_checks = 3
        passed_checks = total_checks - len(results["issues"])
        results["score"] = (passed_checks / total_checks) * 100
        
        # Determine compliance
        if results["score"] >= 95:
            results["compliance"] = "AAA"
        elif results["score"] >= 85:
            results["compliance"] = "AA"
        elif results["score"] >= 70:
            results["compliance"] = "A"
        else:
            results["compliance"] = "non-compliant"
        
        return results
    
    def _check_color_contrast(self, components: List[Dict[str, Any]], 
                            contrast_requirements: Dict[str, float]) -> List[Dict[str, Any]]:
        """Check color contrast ratios."""
        issues = []
        
        for component in components:
            if component.get("type") in ["text", "button", "link"]:
                foreground_color = component.get("color", "#000000")
                background_color = component.get("background_color", "#ffffff")
                
                contrast_ratio = self._calculate_contrast_ratio(foreground_color, background_color)
                
                if contrast_ratio < contrast_requirements["AA"]:
                    issues.append({
                        "type": "color_contrast",
                        "severity": "error",
                        "component": component.get("id", "unknown"),
                        "current_ratio": contrast_ratio,
                        "required_ratio": contrast_requirements["AA"],
                        "message": f"Color contrast ratio {contrast_ratio:.2f} is below WCAG AA standard of {contrast_requirements['AA']}"
                    })
                elif contrast_ratio < contrast_requirements["AAA"]:
                    issues.append({
                        "type": "color_contrast",
                        "severity": "warning",
                        "component": component.get("id", "unknown"),
                        "current_ratio": contrast_ratio,
                        "required_ratio": contrast_requirements["AAA"],
                        "message": f"Color contrast ratio {contrast_ratio:.2f} could be improved to meet WCAG AAA standard of {contrast_requirements['AAA']}"
                    })
        
        return issues
    
    def _check_alternative_text(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for alternative text on images."""
        issues = []
        
        for component in components:
            if component.get("type") == "image":
                alt_text = component.get("alt_text", "")
                
                if not alt_text:
                    issues.append({
                        "type": "missing_alt_text",
                        "severity": "error",
                        "component": component.get("id", "unknown"),
                        "message": "Image is missing alternative text"
                    })
                elif len(alt_text.strip()) < 3:
                    issues.append({
                        "type": "insufficient_alt_text",
                        "severity": "warning",
                        "component": component.get("id", "unknown"),
                        "message": "Alternative text is too short to be meaningful"
                    })
        
        return issues
    
    def _check_text_resize(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check text resize capability."""
        issues = []
        
        # Check if text uses relative units
        for component in components:
            if component.get("type") in ["text", "heading"]:
                font_size = component.get("font_size", "")
                
                if font_size and font_size.endswith("px"):
                    issues.append({
                        "type": "fixed_text_size",
                        "severity": "warning",
                        "component": component.get("id", "unknown"),
                        "message": "Text size is fixed in pixels, may not resize properly"
                    })
        
        return issues
    
    def _check_keyboard_navigation(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check keyboard navigation support."""
        issues = []
        
        interactive_components = [c for c in components 
                                if c.get("type") in ["button", "link", "input", "select"]]
        
        for component in interactive_components:
            if not component.get("keyboard_accessible", True):
                issues.append({
                    "type": "keyboard_inaccessible",
                    "severity": "error",
                    "component": component.get("id", "unknown"),
                    "message": "Component is not accessible via keyboard"
                })
            
            if not component.get("tab_index"):
                issues.append({
                    "type": "missing_tab_index",
                    "severity": "warning",
                    "component": component.get("id", "unknown"),
                    "message": "Component may not be included in tab order"
                })
        
        return issues
    
    def _check_focus_indicators(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check focus indicators."""
        issues = []
        
        interactive_components = [c for c in components 
                                if c.get("type") in ["button", "link", "input", "select"]]
        
        for component in interactive_components:
            if not component.get("focus_indicator"):
                issues.append({
                    "type": "missing_focus_indicator",
                    "severity": "error",
                    "component": component.get("id", "unknown"),
                    "message": "Component lacks visible focus indicator"
                })
        
        return issues
    
    def _check_seizure_content(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for seizure-inducing content."""
        issues = []
        
        for component in components:
            if component.get("type") == "animation":
                flash_rate = component.get("flash_rate", 0)
                
                if flash_rate > 3:
                    issues.append({
                        "type": "seizure_risk",
                        "severity": "error",
                        "component": component.get("id", "unknown"),
                        "message": f"Animation flashes {flash_rate} times per second, exceeds safe limit of 3"
                    })
        
        return issues
    
    def _check_navigation_consistency(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check navigation consistency."""
        issues = []
        
        # This would require more complex analysis of the entire interface
        # For now, we'll check basic navigation components
        navigation_components = [c for c in components if c.get("type") == "navigation"]
        
        if len(navigation_components) > 1:
            # Check for consistent styling and behavior
            styles = [c.get("style", {}) for c in navigation_components]
            if len(set(str(style) for style in styles)) > 1:
                issues.append({
                    "type": "inconsistent_navigation",
                    "severity": "warning",
                    "message": "Navigation components have inconsistent styling"
                })
        
        return issues
    
    def _check_language_specification(self, interface_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check language specification."""
        issues = []
        
        if not interface_data.get("language"):
            issues.append({
                "type": "missing_language",
                "severity": "error",
                "message": "Page language is not specified"
            })
        
        return issues
    
    def _check_error_identification(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check error identification."""
        issues = []
        
        form_components = [c for c in components if c.get("type") == "form"]
        
        for form in form_components:
            if not form.get("error_handling"):
                issues.append({
                    "type": "missing_error_handling",
                    "severity": "error",
                    "component": form.get("id", "unknown"),
                    "message": "Form lacks proper error identification and description"
                })
        
        return issues
    
    def _check_form_labels(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check form labels."""
        issues = []
        
        input_components = [c for c in components if c.get("type") in ["input", "select", "textarea"]]
        
        for input_comp in input_components:
            if not input_comp.get("label"):
                issues.append({
                    "type": "missing_label",
                    "severity": "error",
                    "component": input_comp.get("id", "unknown"),
                    "message": "Form input is missing a label"
                })
        
        return issues
    
    def _check_html_validity(self, interface_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check HTML validity."""
        issues = []
        
        # This would typically use an HTML validator
        # For now, we'll check basic structural issues
        html_structure = interface_data.get("html_structure", {})
        
        if not html_structure.get("doctype"):
            issues.append({
                "type": "missing_doctype",
                "severity": "error",
                "message": "HTML document is missing DOCTYPE declaration"
            })
        
        return issues
    
    def _check_semantic_html(self, interface_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check semantic HTML usage."""
        issues = []
        
        components = interface_data.get("components", [])
        
        # Check for proper heading hierarchy
        headings = [c for c in components if c.get("type") == "heading"]
        heading_levels = [c.get("level", 0) for c in headings]
        
        if heading_levels:
            # Check for skipped heading levels
            expected_level = 1
            for level in sorted(heading_levels):
                if level > expected_level:
                    issues.append({
                        "type": "skipped_heading_level",
                        "severity": "warning",
                        "message": f"Heading level {level} is used before level {expected_level}"
                    })
                expected_level = level + 1
        
        return issues
    
    def _check_compatibility(self, interface_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check compatibility with assistive technologies."""
        issues = []
        
        # Check for ARIA attributes
        components = interface_data.get("components", [])
        interactive_components = [c for c in components 
                                if c.get("type") in ["button", "link", "input", "select"]]
        
        for component in interactive_components:
            if not component.get("aria_label") and not component.get("aria_labelledby"):
                if not component.get("label"):  # Only flag if no label either
                    issues.append({
                        "type": "missing_aria_label",
                        "severity": "warning",
                        "component": component.get("id", "unknown"),
                        "message": "Interactive component could benefit from ARIA labeling"
                    })
        
        return issues
    
    def _calculate_contrast_ratio(self, color1: str, color2: str) -> float:
        """Calculate color contrast ratio between two colors."""
        # Simplified contrast calculation
        # In a real implementation, this would use proper color space conversion
        try:
            # Convert hex colors to RGB
            def hex_to_rgb(hex_color):
                hex_color = hex_color.lstrip('#')
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
            rgb1 = hex_to_rgb(color1)
            rgb2 = hex_to_rgb(color2)
            
            # Calculate relative luminance
            def get_luminance(rgb):
                r, g, b = [c / 255.0 for c in rgb]
                r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
                g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
                b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
                return 0.2126 * r + 0.7152 * g + 0.0722 * b
            
            l1 = get_luminance(rgb1)
            l2 = get_luminance(rgb2)
            
            # Calculate contrast ratio
            lighter = max(l1, l2)
            darker = min(l1, l2)
            
            return (lighter + 0.05) / (darker + 0.05)
            
        except:
            return 1.0  # Default contrast ratio
    
    def _calculate_overall_compliance(self, audit_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall compliance score."""
        guidelines = audit_results["guidelines"]
        
        if not guidelines:
            audit_results["overall_compliance"] = "unknown"
            audit_results["score"] = 0
            return audit_results
        
        # Calculate weighted average score
        total_score = 0
        total_weight = 0
        
        for category, results in guidelines.items():
            weight = 1.0  # Equal weight for all categories
            total_score += results["score"] * weight
            total_weight += weight
        
        overall_score = total_score / total_weight if total_weight > 0 else 0
        audit_results["score"] = overall_score
        
        # Determine overall compliance level
        if overall_score >= 95:
            audit_results["overall_compliance"] = "AAA"
        elif overall_score >= 85:
            audit_results["overall_compliance"] = "AA"
        elif overall_score >= 70:
            audit_results["overall_compliance"] = "A"
        else:
            audit_results["overall_compliance"] = "non-compliant"
        
        # Collect all issues and recommendations
        all_issues = []
        all_recommendations = []
        
        for category, results in guidelines.items():
            all_issues.extend(results.get("issues", []))
            all_recommendations.extend(results.get("recommendations", []))
        
        audit_results["issues"] = all_issues
        audit_results["recommendations"] = all_recommendations
        
        return audit_results
    
    def generate_accessibility_report(self, audit_results: Dict[str, Any]) -> str:
        """Generate a human-readable accessibility report."""
        report = []
        
        report.append("# Accessibility Audit Report")
        report.append(f"**Generated:** {audit_results.get('timestamp', 'Unknown')}")
        report.append(f"**Overall Compliance:** {audit_results.get('overall_compliance', 'Unknown')}")
        report.append(f"**Overall Score:** {audit_results.get('score', 0):.1f}%")
        report.append("")
        
        # Guidelines summary
        report.append("## Guidelines Summary")
        guidelines = audit_results.get("guidelines", {})
        
        for category, results in guidelines.items():
            report.append(f"### {category.title()}")
            report.append(f"- **Compliance:** {results.get('compliance', 'Unknown')}")
            report.append(f"- **Score:** {results.get('score', 0):.1f}%")
            report.append("")
        
        # Issues summary
        issues = audit_results.get("issues", [])
        if issues:
            report.append("## Issues Found")
            
            # Group issues by severity
            error_issues = [i for i in issues if i.get("severity") == "error"]
            warning_issues = [i for i in issues if i.get("severity") == "warning"]
            
            if error_issues:
                report.append("### Errors (Must Fix)")
                for issue in error_issues:
                    report.append(f"- **{issue.get('type', 'Unknown')}:** {issue.get('message', 'No description')}")
                report.append("")
            
            if warning_issues:
                report.append("### Warnings (Should Fix)")
                for issue in warning_issues:
                    report.append(f"- **{issue.get('type', 'Unknown')}:** {issue.get('message', 'No description')}")
                report.append("")
        
        # Recommendations
        recommendations = audit_results.get("recommendations", [])
        if recommendations:
            report.append("## Recommendations")
            for rec in recommendations:
                report.append(f"- {rec}")
            report.append("")
        
        return "\n".join(report)
