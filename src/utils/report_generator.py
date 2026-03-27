"""
ResearchAI - Report Generator Utility
Generates professional PDF briefings using fpdf2.
"""

from fpdf import FPDF
import datetime
from pathlib import Path

class ResearchReportGenerator:
    """Utility to generate PDF research reports."""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate(self, results: dict) -> str:
        """Create a PDF report from pipeline results.
        
        Args:
            results: The full results dict from the orchestrator.
            
        Returns:
            Path to the generated PDF.
        """
        query = results.get("query", "General Research")
        stages = results.get("stages", {})
        
        pdf = FPDF()
        pdf.add_page()
        
        # Header
        pdf.set_font("Arial", 'B', 24)
        pdf.set_text_color(99, 102, 241) # Indigo accent
        pdf.cell(0, 20, "ResearchAI Briefing", ln=True, align='C')
        
        pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, f"Topic: {query}", ln=True, align='C')
        
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(0, 10, f"Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
        pdf.ln(10)
        
        # 1. Research Plan
        plan = stages.get("research_planning", {}).get("result", {})
        if plan:
            self._add_section(pdf, "Strategic Research Plan")
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "Focus Areas:", ln=True)
            pdf.set_font("Arial", '', 10)
            for area in plan.get("focus_areas", []):
                pdf.cell(0, 7, f"- {area}", ln=True)
            pdf.ln(5)

        # 2. Lit Review
        lit_review = stages.get("literature_review", {}).get("result", "")
        if lit_review:
            self._add_section(pdf, "Literature Synthesis")
            pdf.set_font("Arial", '', 10)
            # Use explicit margins to avoid space errors (Effective width 190)
            pdf.multi_cell(190, 7, lit_review[:5000]) 
            pdf.ln(5)

        # 3. Research Gaps & Hypotheses
        gaps = stages.get("gap_detection", {}).get("result", [])
        hypos = stages.get("hypothesis_generation", {}).get("result", [])
        if gaps:
            self._add_section(pdf, "Detected Research Gaps & Hypotheses")
            for i, gap in enumerate(gaps[:5]):
                pdf.set_font("Arial", 'B', 11)
                pdf.multi_cell(190, 8, f"Gap {i+1}: {gap.topic}")
                pdf.set_font("Arial", '', 10)
                pdf.multi_cell(190, 7, f"Description: {gap.description}")
                if i < len(hypos):
                    pdf.set_font("Arial", 'I', 10)
                    pdf.multi_cell(190, 7, f"Hypothesis: {hypos[i].get('hypothesis', '')}")
                pdf.ln(5)

        # 4. Emerging Trends
        trends = stages.get("trend_prediction", {}).get("result", [])
        if trends:
            self._add_section(pdf, "Future Trends & Trajectories")
            for trend in trends[:5]:
                pdf.set_font("Arial", '', 10)
                pdf.cell(0, 7, f"- {trend.topic} (Confidence: {trend.confidence_score:.2f})", ln=True)

        filename = f"Report_{query.replace(' ', '_')[:30]}.pdf"
        output_path = self.output_dir / filename
        pdf.output(str(output_path))
        
        return str(output_path)

    def _add_section(self, pdf, title):
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(79, 70, 229)
        # Use explicit width 190 (A4 is 210mm, 10mm margins)
        pdf.multi_cell(190, 10, title) 
        # Draw line based on left margin to avoid overflow
        curr_y = pdf.get_y()
        pdf.line(10, curr_y, 200, curr_y)
        pdf.ln(5)
        pdf.set_text_color(0, 0, 0)
