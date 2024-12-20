# approval_analyzer.py
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

class ApprovalAnalyzer:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def analyze_response(self, email_content):
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """Analyze the email response for invoice approval.
                        Determine if the invoice is:
                        1. Approved
                        2. Rejected
                        3. Needs modifications
                        
                        Return a JSON with:
                        - status: "approved", "rejected", or "needs_modifications"
                        - confidence: 0-1
                        - reason: explanation for the decision
                        """
                    },
                    {
                        "role": "user",
                        "content": f"Analyze this email response:\n\n{email_content}"
                    }
                ],
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error analyzing approval: {e}")
            raise