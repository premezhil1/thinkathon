"""
Topic Extraction Module for Call Analysis
Extracts and categorizes conversation topics using NLP techniques.
"""

import re
from typing import List, Dict, Tuple
from collections import Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import LatentDirichletAllocation
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.chunk import ne_chunk
from nltk.tag import pos_tag

class TopicExtractor:
    def __init__(self):
        """Initialize topic extractor with NLP tools."""
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
        
        try:
            nltk.data.find('corpora/wordnet')
        except LookupError:
            nltk.download('wordnet')
        
        try:
            nltk.data.find('taggers/averaged_perceptron_tagger')
        except LookupError:
            nltk.download('averaged_perceptron_tagger')
        
        try:
            nltk.data.find('chunkers/maxent_ne_chunker')
        except LookupError:
            nltk.download('maxent_ne_chunker')
        
        try:
            nltk.data.find('corpora/words')
        except LookupError:
            nltk.download('words')
        
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        
        # Industry-specific topic keywords
        self.industry_topics = {
            'eCommerce': {
                'order_management': ['order', 'delivery', 'shipping', 'tracking', 'package', 'dispatch'],
                'payment_billing': ['payment', 'billing', 'charge', 'refund', 'invoice', 'credit card'],
                'product_issues': ['product', 'item', 'quality', 'defective', 'damaged', 'return'],
                'account_support': ['account', 'login', 'password', 'profile', 'registration'],
                'customer_service': ['service', 'support', 'help', 'assistance', 'representative']
            },
            'Telecom': {
                'service_issues': ['service', 'connection', 'network', 'signal', 'outage', 'down'],
                'billing_plans': ['bill', 'plan', 'upgrade', 'downgrade', 'pricing', 'cost'],
                'technical_support': ['technical', 'setup', 'configuration', 'installation', 'troubleshoot'],
                'device_support': ['device', 'phone', 'modem', 'router', 'equipment', 'hardware'],
                'data_usage': ['data', 'usage', 'limit', 'overage', 'bandwidth', 'speed']
            },
            'Healthcare': {
                'appointments': ['appointment', 'schedule', 'booking', 'visit', 'consultation'],
                'test_results': ['test', 'results', 'lab', 'report', 'analysis', 'findings'],
                'medication': ['medication', 'prescription', 'drug', 'pharmacy', 'dosage'],
                'insurance': ['insurance', 'coverage', 'claim', 'copay', 'deductible'],
                'symptoms': ['symptoms', 'pain', 'condition', 'diagnosis', 'treatment']
            },
            'Travel': {
                'booking_reservations': ['booking', 'reservation', 'flight', 'hotel', 'ticket'],
                'cancellations': ['cancel', 'cancellation', 'refund', 'change', 'modification'],
                'travel_issues': ['delay', 'baggage', 'lost', 'missed', 'connection'],
                'destinations': ['destination', 'location', 'city', 'country', 'travel'],
                'pricing': ['price', 'cost', 'fare', 'discount', 'promotion', 'deal']
            },
            'RealEstate': {
                'property_search': ['property', 'house', 'apartment', 'search', 'listing'],
                'viewing_tours': ['viewing', 'tour', 'visit', 'showing', 'inspection'],
                'pricing_negotiation': ['price', 'offer', 'negotiation', 'value', 'market'],
                'documentation': ['contract', 'paperwork', 'documents', 'agreement', 'legal'],
                'financing': ['mortgage', 'loan', 'financing', 'bank', 'credit', 'approval']
            }
        }
        
        # General business topics
        self.general_topics = {
            'customer_satisfaction': ['satisfied', 'happy', 'pleased', 'disappointed', 'frustrated'],
            'complaint_resolution': ['complaint', 'issue', 'problem', 'resolve', 'solution'],
            'information_request': ['information', 'details', 'explain', 'clarify', 'understand'],
            'service_quality': ['quality', 'service', 'experience', 'professional', 'helpful'],
            'follow_up': ['follow', 'update', 'status', 'progress', 'next steps']
        }
    
    def preprocess_text(self, text: str) -> List[str]:
        """Preprocess text for topic extraction."""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and digits
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords and short words
        tokens = [token for token in tokens if token not in self.stop_words and len(token) > 2]
        
        # Lemmatize
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens]
        
        return tokens
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """Extract keywords using TF-IDF."""
        processed_tokens = self.preprocess_text(text)
        processed_text = ' '.join(processed_tokens)
        
        if not processed_text.strip():
            return []
        
        # Use TF-IDF to extract keywords
        vectorizer = TfidfVectorizer(max_features=top_n, ngram_range=(1, 2))
        try:
            tfidf_matrix = vectorizer.fit_transform([processed_text])
            feature_names = vectorizer.get_feature_names_out()
            tfidf_scores = tfidf_matrix.toarray()[0]
            
            # Get top keywords
            keyword_scores = list(zip(feature_names, tfidf_scores))
            keyword_scores.sort(key=lambda x: x[1], reverse=True)
            
            return keyword_scores
        except:
            # Fallback to word frequency
            word_freq = Counter(processed_tokens)
            return word_freq.most_common(top_n)
    
    def detect_named_entities(self, text: str) -> Dict[str, List[str]]:
        """Detect named entities in text."""
        tokens = word_tokenize(text)
        pos_tags = pos_tag(tokens)
        chunks = ne_chunk(pos_tags)
        
        entities = {
            'PERSON': [],
            'ORGANIZATION': [],
            'LOCATION': [],
            'MONEY': [],
            'DATE': [],
            'TIME': []
        }
        
        for chunk in chunks:
            if hasattr(chunk, 'label'):
                entity_name = ' '.join([token for token, pos in chunk.leaves()])
                entity_type = chunk.label()
                if entity_type in entities:
                    entities[entity_type].append(entity_name)
        
        return entities
    
    def classify_industry_topics(self, text: str, industry: str) -> Dict[str, float]:
        """Classify topics based on industry-specific keywords."""
        text_lower = text.lower()
        topic_scores = {}
        
        # Get industry-specific topics
        industry_topics = self.industry_topics.get(industry, {})
        
        # Also include general topics
        all_topics = {**industry_topics, **self.general_topics}
        
        for topic, keywords in all_topics.items():
            score = 0.0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1.0
            
            # Normalize by number of keywords
            topic_scores[topic] = score / len(keywords) if keywords else 0.0
        
        return topic_scores
    
    def extract_conversation_topics(self, dialogue: List[Dict], industry: str = 'general') -> Dict:
        """Extract topics from entire conversation."""
        # Combine all text
        all_text = ' '.join([turn.get('text', '') for turn in dialogue])
        
        # Extract text by speaker (case-insensitive matching)
        customer_text = ''
        agent_text = ''
        
        for turn in dialogue:
            text = turn.get('text', '')
            speaker = turn.get('speaker', '').lower()
            
            if 'customer' in speaker or 'client' in speaker or 'caller' in speaker:
                customer_text += ' ' + text
            elif 'agent' in speaker or 'representative' in speaker or 'support' in speaker:
                agent_text += ' ' + text
        
        customer_text = customer_text.strip()
        agent_text = agent_text.strip()
        
        # If no specific speakers found, split text roughly in half
        if not customer_text and not agent_text and all_text:
            mid_point = len(dialogue) // 2
            customer_text = ' '.join([turn.get('text', '') for turn in dialogue[:mid_point]])
            agent_text = ' '.join([turn.get('text', '') for turn in dialogue[mid_point:]])
        
        # Extract keywords
        overall_keywords = self.extract_keywords(all_text, top_n=15)
        customer_keywords = self.extract_keywords(customer_text, top_n=10) if customer_text else []
        agent_keywords = self.extract_keywords(agent_text, top_n=10) if agent_text else []
        
        # Classify topics
        overall_topics = self.classify_industry_topics(all_text, industry)
        customer_topics = self.classify_industry_topics(customer_text, industry) if customer_text else {}
        agent_topics = self.classify_industry_topics(agent_text, industry) if agent_text else {}
        
        # Extract named entities
        entities = self.detect_named_entities(all_text)
        
        # Find dominant topics (ensure we have meaningful topics)
        dominant_topics = sorted(overall_topics.items(), key=lambda x: x[1], reverse=True)[:5]
        dominant_topics = [(topic, score) for topic, score in dominant_topics if score > 0.1]  # Minimum threshold
        
        # If no dominant topics found, try to extract from keywords
        if not dominant_topics and overall_keywords:
            # Create topics from top keywords
            for keyword, score in overall_keywords[:3]:
                if isinstance(keyword, tuple):
                    topic_name = keyword[0] if len(keyword) > 0 else 'general'
                    topic_score = score if isinstance(score, (int, float)) else 0.5
                else:
                    topic_name = str(keyword)
                    topic_score = score if isinstance(score, (int, float)) else 0.5
                
                dominant_topics.append((topic_name, topic_score))
        
        # Topic progression analysis
        topic_progression = self._analyze_topic_progression(dialogue, industry)
        
        return {
            'dominant_topics': dominant_topics,
            'overall_keywords': overall_keywords,
            'customer_keywords': customer_keywords,
            'agent_keywords': agent_keywords,
            'topic_scores': overall_topics,
            'customer_topics': customer_topics,
            'agent_topics': agent_topics,
            'named_entities': entities,
            'topic_progression': topic_progression,
            'industry': industry,
            'total_text_length': len(all_text),
            'customer_text_length': len(customer_text),
            'agent_text_length': len(agent_text)
        }
    
    def _analyze_topic_progression(self, dialogue: List[Dict], industry: str) -> List[Dict]:
        """Analyze how topics change throughout the conversation."""
        progression = []
        
        for i, turn in enumerate(dialogue):
            text = turn['text']
            topics = self.classify_industry_topics(text, industry)
            
            # Find dominant topic for this turn
            if topics:
                dominant_topic = max(topics.items(), key=lambda x: x[1])
                if dominant_topic[1] > 0:
                    progression.append({
                        'turn': i + 1,
                        'speaker': turn['speaker'],
                        'dominant_topic': dominant_topic[0],
                        'topic_score': round(dominant_topic[1], 3),
                        'all_topics': {k: round(v, 3) for k, v in topics.items() if v > 0}
                    })
        
        return progression
    
    def _generate_topic_summary(self, dominant_topics: List[Tuple[str, float]], keywords: List[Tuple[str, float]]) -> str:
        """Generate a human-readable topic summary."""
        if not dominant_topics:
            return "No specific topics identified in the conversation."
        
        # Format topic names for readability
        topic_names = []
        for topic, score in dominant_topics[:3]:
            formatted_topic = topic.replace('_', ' ').title()
            topic_names.append(f"{formatted_topic} ({score:.1%})")
        
        summary = f"Main topics discussed: {', '.join(topic_names)}. "
        
        if keywords:
            top_keywords = [kw for kw, _ in keywords[:5]]
            summary += f"Key terms: {', '.join(top_keywords)}."
        
        return summary
    
    def get_topic_distribution_data(self, conversations: List[Dict]) -> Dict:
        """Prepare topic distribution data for visualization."""
        all_topics = {}
        industry_breakdown = {}
        
        for conv in conversations:
            industry = conv.get('industry', 'general')
            dialogue = conv.get('dialogue', [])
            
            # Extract topics for this conversation
            topics_result = self.extract_conversation_topics(dialogue, industry)
            
            # Aggregate topics
            for topic, score in topics_result['topic_scores'].items():
                if score > 0:
                    if topic not in all_topics:
                        all_topics[topic] = []
                    all_topics[topic].append(score)
                    
                    # Industry breakdown
                    if industry not in industry_breakdown:
                        industry_breakdown[industry] = {}
                    if topic not in industry_breakdown[industry]:
                        industry_breakdown[industry][topic] = []
                    industry_breakdown[industry][topic].append(score)
        
        # Calculate averages
        topic_averages = {topic: np.mean(scores) for topic, scores in all_topics.items()}
        
        # Industry averages
        industry_topic_averages = {}
        for industry, topics in industry_breakdown.items():
            industry_topic_averages[industry] = {
                topic: np.mean(scores) for topic, scores in topics.items()
            }
        
        return {
            'overall_topic_distribution': topic_averages,
            'industry_topic_breakdown': industry_topic_averages,
            'topic_frequency': {topic: len(scores) for topic, scores in all_topics.items()}
        }
    
    def get_topic_explanation(self, topic: str, score: float, industry: str) -> str:
        """Generate explanation for detected topic."""
        # Format topic name
        formatted_topic = topic.replace('_', ' ').title()
        
        # Industry-specific explanations
        explanations = {
            'eCommerce': {
                'order_management': "Discussion about order status, delivery, or shipping concerns",
                'payment_billing': "Conversation involving payment methods, billing issues, or refunds",
                'product_issues': "Topics related to product quality, defects, or returns"
            },
            'Telecom': {
                'service_issues': "Discussion about network problems, service outages, or connectivity",
                'billing_plans': "Conversation about billing, plan changes, or pricing",
                'technical_support': "Technical troubleshooting or setup assistance"
            },
            'Healthcare': {
                'appointments': "Discussion about scheduling or managing appointments",
                'test_results': "Conversation about medical test results or reports",
                'medication': "Topics related to prescriptions or medication management"
            }
        }
        
        industry_explanations = explanations.get(industry, {})
        specific_explanation = industry_explanations.get(topic, f"Discussion related to {formatted_topic}")
        
        confidence_level = "high" if score > 0.3 else "medium" if score > 0.1 else "low"
        
        return f"{specific_explanation}. Detected with {confidence_level} confidence ({score:.1%} relevance)."
