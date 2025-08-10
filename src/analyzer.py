"""
Main Call Analysis Engine
Coordinates intent detection, sentiment analysis, and topic extraction.
"""

import json
import os
from typing import List, Dict, Any
from datetime import datetime
import pandas as pd
from transformers import pipeline
from intent_detector import IntentDetector
from sentiment_analyzer import SentimentAnalyzer
from topic_extractor import TopicExtractor
import nltk
import re
nltk.download("punkt", quiet=True)
from transformers import AutoTokenizer
from nltk.tokenize import sent_tokenize


class CallAnalyzer:
  
     
    def __init__(self):
        """Initialize the call analyzer with all components."""
        print("Initializing Call Analyzer...")
        self.model_name = "philschmid/bart-large-cnn-samsum"
        self.summarizer = pipeline("summarization", model=self.model_name)
        self.intent_detector = IntentDetector()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.topic_extractor = TopicExtractor()
        print("Call Analyzer initialized successfully!")
    
    def analyze_conversation(self, conversation: Dict) -> Dict:
        """
        Perform comprehensive analysis on a single conversation.
        
        Args:
            conversation: Dictionary containing conversation data
            
        Returns:
            Complete analysis results
        """
        
        # Extract conversation details with safe defaults
        conv_id = conversation.get('conversation_id', 'unknown')
        industry = conversation.get('industry', 'general')
        dialogue = conversation.get('dialogue', [])
        participants = conversation.get('participants', [])
        
        # Validate dialogue structure
        if not isinstance(dialogue, list):
            error_msg = f"Expected list for dialogue data, got {type(dialogue).__name__}"
            print(f"Error: {error_msg}")
            return {
                'error': error_msg,
                'conversation_id': conv_id,
                'analysis_timestamp': datetime.now().isoformat()
            }
        
        # Validate dialogue segments
        for i, segment in enumerate(dialogue):
            if not isinstance(segment, dict):
                print(f"Warning: Dialogue segment {i} is not a dictionary, skipping...")
                continue
            if 'text' not in segment:
                print(f"Warning: Dialogue segment {i} missing 'text' field")
                segment['text'] = ''
            if 'speaker' not in segment:
                print(f"Warning: Dialogue segment {i} missing 'speaker' field")
                segment['speaker'] = 'Unknown'       
         
        
        try:
            # Perform all analyses
            intent_results = self.intent_detector.analyze_conversation(dialogue, industry)
            sentiment_results = self.sentiment_analyzer.analyze_conversation(dialogue)
            topic_results = self.topic_extractor.extract_conversation_topics(dialogue, industry)             
            
            # Generate summary  
            formatted_lines = [f"{entry['speaker']}: {entry['text']}" for entry in conversation['dialogue']]

            summary = self._generate_summary(" ".join(formatted_lines))
            
            # Compile results
            analysis_result = {
                'conversation_id': conv_id,
                'industry': industry,
                'participants': participants,
                'analysis_timestamp': datetime.now().isoformat(),
                'intents': intent_results.get('intents', []) if intent_results else [],
                'intent_results': intent_results,
                'sentiment_analysis': sentiment_results,
                'overall_sentiment': sentiment_results.get('overall_sentiment', []) if sentiment_results else [],
                'participant_sentiments': sentiment_results.get('participant_sentiments', []) if sentiment_results else [],
                'topic_analysis': topic_results,
                'topic_scores': topic_results.get('topic_scores', []) if topic_results else [],                 
                'conversation_summary': summary
            }
            
            return analysis_result
            
        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            print(f"Error during analysis: {error_msg}")
            import traceback
            traceback.print_exc()
            
            return {
                'error': error_msg,
                'conversation_id': conv_id,
                'industry': industry,
                'analysis_timestamp': datetime.now().isoformat()
            }
    
    def analyze_dataset(self, conversations: List[Dict]) -> Dict:
        """
        Analyze multiple conversations and provide aggregate insights.
        
        Args:
            conversations: List of conversation dictionaries
            
        Returns:
            Aggregate analysis results
        """
        print(f"Analyzing dataset with {len(conversations)} conversations...")
        
        individual_results = []
        aggregate_metrics = {
            'total_conversations': len(conversations),
            'industries': {},
            'intent_distribution': {},
            'sentiment_distribution': {},
            'topic_distribution': {},
            'quality_metrics': {
                'average_quality': 0,
                'high_quality_count': 0,
                'resolution_rate': 0
            }
        }
        
        # Analyze each conversation
        for i, conversation in enumerate(conversations):
            print(f"Processing conversation {i+1}/{len(conversations)}...")
            result = self.analyze_conversation(conversation)
            individual_results.append(result)
            
            # Update aggregate metrics
            self._update_aggregate_metrics(result, aggregate_metrics)
        
        # Calculate final aggregate statistics
        self._finalize_aggregate_metrics(aggregate_metrics, len(conversations))
        
        # Generate dataset insights
        insights = self._generate_dataset_insights(individual_results, aggregate_metrics)
        
        return {
            'dataset_summary': aggregate_metrics,
            'individual_analyses': individual_results,
            'insights_and_trends': insights,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
 
    def _update_aggregate_metrics(self, result: Dict, aggregate_metrics: Dict):
        """Update aggregate metrics with individual conversation result."""
        industry = result.get('industry', 'unknown')
        
        # Industry distribution
        if industry not in aggregate_metrics['industries']:
            aggregate_metrics['industries'][industry] = 0
        aggregate_metrics['industries'][industry] += 1
        
        # Intent distribution
        intent_analysis = result.get('intent_analysis', {})
        primary_intents = intent_analysis.get('intents', [])
        for intent in primary_intents[:3]:  # Top 3 intents
            if isinstance(intent, dict):
                intent_name = intent.get('intent', '')
            else:
                intent_name = str(intent)
            if intent_name not in aggregate_metrics['intent_distribution']:
                aggregate_metrics['intent_distribution'][intent_name] = 0
            aggregate_metrics['intent_distribution'][intent_name] += 1
        
        # Sentiment distribution
        sentiment_analysis = result.get('sentiment_analysis', {})
        overall_sentiment = sentiment_analysis.get('overall_sentiment', {}).get('label', 'neutral')
        if overall_sentiment not in aggregate_metrics['sentiment_distribution']:
            aggregate_metrics['sentiment_distribution'][overall_sentiment] = 0
        aggregate_metrics['sentiment_distribution'][overall_sentiment] += 1
        
        # Topic distribution
        topic_analysis = result.get('topic_analysis', {})
        dominant_topics = topic_analysis.get('dominant_topics', [])
        for topic, score in dominant_topics[:3]:  # Top 3 topics
            if topic not in aggregate_metrics['topic_distribution']:
                aggregate_metrics['topic_distribution'][topic] = 0
            aggregate_metrics['topic_distribution'][topic] += score
        
        # Quality metrics
        quality_metrics = result.get('quality_metrics', {})
        quality_score = quality_metrics.get('overall_score', 0)
        aggregate_metrics['quality_metrics']['average_quality'] += quality_score
        
        if quality_score >= 75:
            aggregate_metrics['quality_metrics']['high_quality_count'] += 1
        
        resolution = sentiment_analysis.get('quality_metrics', {}).get('resolution_indicator', 'unresolved')
        if resolution in ['resolved', 'partially_resolved']:
            aggregate_metrics['quality_metrics']['resolution_rate'] += 1

    

    def clean_conversation(self, text):
        """Clean and preprocess conversation text"""
        # Remove excessive whitespace and newlines
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Remove speaker labels that might confuse the model
        # But keep some context about roles
        text = re.sub(r'\b(Agent|Customer):\s*', '', text)
        
        return text.strip()

    def chunk_text(self, text, max_length=900):
        """Split long input into chunks using sentence tokenizer"""
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_length:
                current_chunk += sentence + " "
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks


    def chunk_text_by_tokens(self, text, max_tokens=800):
        tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        sentences = sent_tokenize(text)

        chunks = []
        current_chunk = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = tokenizer.encode(sentence, add_special_tokens=False)
            sentence_length = len(sentence_tokens)

            if current_tokens + sentence_length > max_tokens:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_tokens = sentence_length
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_length

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks, tokenizer

    def _generate_summary(self, conversation):
        """Generate summary with improved parameters and adaptive length control"""

        # Clean the conversation
        cleaned_conversation = self.clean_conversation(conversation)

        # --- Token-based chunking method ---
        # Step 1: Chunk the conversation using token-aware splitting
        chunks, tokenizer = self.chunk_text_by_tokens(cleaned_conversation, max_tokens=800)

        if not chunks:
            return "Unable to generate summary - no content found."

        summaries = []

        # Step 2: Summarize each chunk with adaptive parameters
        for chunk in chunks:
            try:
                chunk_tokens = len(tokenizer.encode(chunk))
                chunk_max_len = min(100, max(50, chunk_tokens // 2))  # Cap at 100 tokens
                chunk_min_len = max(25, chunk_max_len // 3)

                summary = self.summarizer(
                    chunk,
                    max_length=chunk_max_len,
                    min_length=chunk_min_len,
                    do_sample=False,
                    num_beams=4,
                    length_penalty=1.0,
                    early_stopping=True
                )[0]['summary_text']

                summaries.append(summary)

            except Exception as e:
                print(f"Error summarizing chunk: {e} | First 80 chars: {chunk[:80]}")
                continue

        if not summaries:
            return "Unable to generate summary."

        # Step 3: Combine summaries
        if len(summaries) == 1:
            final_summary = summaries[0]
        else:
            combined_text = " ".join(summaries)
            combined_tokens = len(tokenizer.encode(combined_text))

            if combined_tokens < 150:
                final_summary = combined_text
            else:
                try:
                    final_max_len = min(400, combined_tokens // 2)
                    final_min_len = max(50, final_max_len // 3)

                    final_summary = self.summarizer(
                        combined_text,
                        max_length=final_max_len,
                        min_length=final_min_len,
                        do_sample=False,
                        num_beams=4,
                        length_penalty=1.2,
                        early_stopping=True
                    )[0]['summary_text']

                except Exception as e:
                    print(f"Error in final summarization: {e}")
                    final_summary = combined_text

        # Step 4: Post-process for better narrative flow
        return self.post_process_summary(final_summary)

    def post_process_summary(self, summary):
        """Post-process summary to improve readability and narrative flow"""
        
        # Ensure proper sentence structure
        summary = summary.strip()
        
        # Fix common issues
        summary = re.sub(r'\s+', ' ', summary)  # Remove extra spaces
        summary = re.sub(r'(\w)([A-Z])', r'\1. \2', summary)  # Add periods between sentences if missing
        
        # Ensure it starts with capital letter
        if summary and not summary[0].isupper():
            summary = summary[0].upper() + summary[1:]
        
        # Ensure it ends with proper punctuation
        if summary and summary[-1] not in '.!?':
            summary += '.'
        
        return summary
    
 
 
 
 
def main():
    """Main function to run the analyzer."""

if __name__ == "__main__":
    main()
