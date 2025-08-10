"""
Intent Detection Module for Call Analysis
Identifies conversation intents such as complaint, inquiry, feedback, etc.
"""

import re
from typing import List, Dict, Tuple
import numpy as np

# Try to import transformers with graceful fallback
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Warning: transformers library not available. Using rule-based intent detection.")

class IntentDetector:
    def __init__(self):
        """Initialize the intent detector with pre-trained models and keyword patterns."""
        self.classifier = None
        
        if TRANSFORMERS_AVAILABLE:
            try:
                self.device = 0 if torch.cuda.is_available() else -1
                
                # Initialize BERT-based classifier for general intent detection
                try:
                    self.classifier = pipeline(
                         "zero-shot-classification",
                          model="facebook/bart-large-mnli",                      
                        device=self.device
                    )
                    print("Transformers-based intent detector initialized successfully!")
                except Exception as e:
                    print(f"Failed to load transformers model: {e}")
                    self.classifier = None
            except Exception as e:
                print(f"Error initializing transformers: {e}")
                self.classifier = None
        
        # Define intent patterns for rule-based detection
        self.intent_patterns = {
            'complaint': [
                r'\b(complain|complaint|problem|issue|wrong|error|mistake|bad|terrible|awful|disappointed|frustrated|angry|upset)\b',
                r'\b(not working|broken|failed|failure|defective|poor quality)\b',
                r'\b(refund|return|cancel|cancellation)\b'
            ],
            'inquiry': [
                r'\b(question|ask|wondering|curious|information|details|explain|clarify|help|assistance)\b',
                r'\b(how to|how do|what is|where is|when is|why is)\b',
                r'\b(status|update|progress|timeline)\b'
            ],
            'feedback': [
                r'\b(feedback|suggestion|recommend|improvement|better|enhance|feature)\b',
                r'\b(good|great|excellent|amazing|love|like|satisfied|happy)\b',
                r'\b(review|rating|opinion|thoughts)\b'
            ],
            'support_request': [
                r'\b(help|support|assist|guidance|tutorial|instructions)\b',
                r'\b(need help|can you help|please help|assistance needed)\b',
                r'\b(technical support|customer service|customer care)\b'
            ],
            'billing_inquiry': [
                r'\b(bill|billing|charge|payment|invoice|account|balance|fee)\b',
                r'\b(credit card|debit|transaction|subscription|plan)\b',
                r'\b(overcharge|incorrect charge|billing error)\b'
            ],
            'product_inquiry': [
                r'\b(product|service|feature|functionality|specification|availability)\b',
                r'\b(price|cost|pricing|quote|estimate)\b',
                r'\b(delivery|shipping|order|purchase)\b'
            ]
        }
        
        # Industry-specific intent patterns
        self.industry_patterns = {
            'eCommerce': {
                'order_inquiry': [r'\b(order|delivery|shipping|tracking|package)\b'],
                'return_request': [r'\b(return|exchange|refund|warranty)\b'],
                'product_question': [r'\b(size|color|availability|stock|inventory)\b']
            },
            'Telecom': {
                'service_issue': [r'\b(signal|network|connection|outage|slow)\b'],
                'plan_inquiry': [r'\b(plan|package|upgrade|downgrade|data)\b'],
                'technical_support': [r'\b(router|modem|setup|configuration)\b']
            },
            'Healthcare': {
                'appointment': [r'\b(appointment|schedule|booking|visit)\b'],
                'insurance': [r'\b(insurance|coverage|claim|copay)\b'],
                'medical_inquiry': [r'\b(symptoms|prescription|medication|treatment)\b']
            },
            'Travel': {
                'booking_inquiry': [r'\b(booking|reservation|flight|hotel|car rental)\b'],
                'cancellation': [r'\b(cancel|change|modify|reschedule)\b'],
                'travel_issue': [r'\b(delay|baggage|lost|missed connection)\b']
            },
            'RealEstate': {
                'property_inquiry': [r'\b(property|house|apartment|listing|viewing)\b'],
                'mortgage': [r'\b(mortgage|loan|financing|credit|approval)\b'],
                'maintenance': [r'\b(repair|maintenance|issue|problem|fix)\b']
            }
        }
        
        print("Intent Detector initialized successfully!")
    
    def detect_intent_with_transformers(self, text: str) -> List[Dict]:
        """Use transformers model for intent detection."""
        if not self.classifier:
            return []
        
        try:
            if not text or not isinstance(text, str):
                print("Warning: Empty or invalid text input to intent detection.")
                return []
            
            max_length = 500
           

            if len(text) > max_length * 4:
                text = text[:max_length * 4]
           
            candidate_labels = ["complaint", "feedback", "inquiry"]
            results = self.classifier(text,candidate_labels,truncation=True, max_length=512)
           
            if not isinstance(results, list):
                results = [results]
            
            
            
            intents = []
            for res in results:  # results is a list with one dict
                labels = res['labels']        # list of label strings
                scores = res['scores']        # list of scores (floats)
                
                for label, score in zip(labels, scores):
                    intents.append({
                        'intent': label,
                        'confidence': score,
                        'method': 'transformers'
                    })
            
            return intents
        except Exception as e:
            print(f"Error in transformers intent detection: {e}")
            return []

    
    def detect_intent_with_rules(self, text: str, industry: str = 'general') -> List[Dict]:
        """Use rule-based pattern matching for intent detection."""
        text_lower = text.lower()
        detected_intents = []
        
        # Check general intent patterns
        for intent, patterns in self.intent_patterns.items():
            confidence = 0.0
            matches = 0
            
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    matches += 1
            
            if matches > 0:
                confidence = min(0.9, 0.3 + (matches * 0.2))  # Base confidence + bonus for multiple matches
                detected_intents.append({
                    'intent': intent,
                    'confidence': confidence,
                    'method': 'rule_based',
                    'matches': matches
                })
        
        # Check industry-specific patterns
        if industry in self.industry_patterns:
            for intent, patterns in self.industry_patterns[industry].items():
                confidence = 0.0
                matches = 0
                
                for pattern in patterns:
                    if re.search(pattern, text_lower, re.IGNORECASE):
                        matches += 1
                
                if matches > 0:
                    confidence = min(0.95, 0.4 + (matches * 0.25))  # Higher confidence for industry-specific
                    detected_intents.append({
                        'intent': f"{industry.lower()}_{intent}",
                        'confidence': confidence,
                        'method': 'industry_rule',
                        'matches': matches
                    })
        
        # Sort by confidence and return top intents
        detected_intents.sort(key=lambda x: x['confidence'], reverse=True)
        return detected_intents[:3]  # Return top 3 intents
    
    def analyze_conversation(self, dialogue: List[Dict], industry: str = 'general') -> Dict:
        """
        Analyze the entire conversation for intents.
        
        Args:
            dialogue: List of conversation segments
            industry: Industry context for specialized intent detection
            
        Returns:
            Dictionary containing intent analysis results
        """
        if not dialogue:
            return {
                'intents': [],
                'primary_intent': None,
                'confidence_score': 0.0,
                'method_used': 'none'
            }
        
        # Combine all dialogue text
        full_text = ' '.join([segment.get('text', '') for segment in dialogue])
        
        # Try transformers first, fallback to rules
        if TRANSFORMERS_AVAILABLE and self.classifier:
            intents = self.detect_intent_with_transformers(full_text)
            method_used = 'transformers'
        else:
            intents = []
            method_used = 'rule_based'
        
        print(f"Transformer Based {intents}")
        # Always add rule-based detection for better coverage
        rule_intents = self.detect_intent_with_rules(full_text, industry)
        print(f"Rule  Based {rule_intents}")
        intents.extend(rule_intents)
      
        # Remove duplicates and merge similar intents
        merged_intents = self._merge_similar_intents(intents)
        print(f"final Intent {merged_intents}")
        # Determine primary intent
        primary_intent = merged_intents[0] if merged_intents else None
        overall_confidence = primary_intent['confidence'] if primary_intent else 0.0
        
        # Analyze intent distribution per participant
        participant_intents = {}
        for segment in dialogue:
            speaker = segment.get('speaker', 'Unknown')
            text = segment.get('text', '')
            
            if speaker not in participant_intents:
                participant_intents[speaker] = []
            
            # Detect intents for this segment
            if TRANSFORMERS_AVAILABLE and self.classifier:
                segment_intents = self.detect_intent_with_transformers(text)
            else:
                segment_intents = self.detect_intent_with_rules(text, industry)
            
            participant_intents[speaker].extend(segment_intents)
        
        return {
            'intents': merged_intents,
            'primary_intent': primary_intent,
            'confidence_score': overall_confidence,
            'method_used': method_used,
            'participant_intents': participant_intents,
            'industry_context': industry,
            'total_segments_analyzed': len(dialogue)
        }
    
    def _merge_similar_intents(self, intents: List[Dict]) -> List[Dict]:
        """Merge similar intents and calculate combined confidence."""
        if not intents:
            return []
        
        # Group by intent name
        intent_groups = {}
        for intent in intents:
            intent_name = intent['intent']
            if intent_name not in intent_groups:
                intent_groups[intent_name] = []
            intent_groups[intent_name].append(intent)
        
        # Merge and calculate combined confidence
        merged = []
        for intent_name, group in intent_groups.items():
            if len(group) == 1:
                merged.append(group[0])
            else:
                # Combine confidences (weighted average)
                total_confidence = sum(item['confidence'] for item in group)
                avg_confidence = total_confidence / len(group)
                
                # Boost confidence if detected by multiple methods
                if len(group) > 1:
                    avg_confidence = min(0.95, avg_confidence * 1.2)
                
                merged_intent = {
                    'intent': intent_name,
                    'confidence': avg_confidence,
                    'method': 'combined',
                    'detection_count': len(group)
                }
                merged.append(merged_intent)
        
        # Sort by confidence
        merged.sort(key=lambda x: x['confidence'], reverse=True)
        return merged
    

def main():
    """Intent detector."""     

if __name__ == "__main__":
    main()
