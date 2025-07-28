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
from nltk.tokenize import sent_tokenize


class CallAnalyzer:
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    def __init__(self):
        """Initialize the call analyzer with all components."""
        print("Initializing Call Analyzer...")
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
            
            # Calculate overall quality score
            quality_score = self._calculate_overall_quality(intent_results, sentiment_results, topic_results)
            
            
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
                'quality_metrics': quality_score,
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
    
    def _calculate_overall_quality(self, intent_results: Dict, sentiment_results: Dict, topic_results: Dict) -> Dict:
        """Calculate overall conversation quality metrics."""
        # Intent clarity score
        intent_confidence = intent_results.get('intent_confidence', {})
        intent_clarity = max(intent_confidence.values()) if intent_confidence else 0
        
        # Sentiment quality score
        sentiment_quality = sentiment_results.get('quality_metrics', {}).get('quality_score', 0)
        
        # Topic relevance score
        dominant_topics = topic_results.get('dominant_topics', [])
        topic_relevance = sum(score for _, score in dominant_topics[:3]) * 100 if dominant_topics else 0
        
        # Agent response quality
        agent_response_quality = intent_results.get('agent_response_pattern', {}).get('quality_score', 0) * 100
        
        # Overall quality score (weighted average)
        overall_quality = (
            intent_clarity * 0.25 +
            sentiment_quality * 0.35 +
            topic_relevance * 0.20 +
            agent_response_quality * 0.20
        )
        
        # Quality classification
        if overall_quality >= 75:
            quality_level = 'excellent'
        elif overall_quality >= 60:
            quality_level = 'good'
        elif overall_quality >= 40:
            quality_level = 'fair'
        else:
            quality_level = 'poor'
        
        return {
            'overall_score': round(overall_quality, 2),
            'quality_level': quality_level,
            'component_scores': {
                'intent_clarity': round(intent_clarity, 2),
                'sentiment_quality': round(sentiment_quality, 2),
                'topic_relevance': round(topic_relevance, 2),
                'agent_response_quality': round(agent_response_quality, 2)
            }
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

    def _generate_summary(self, conversation):
        """Generate summary with improved parameters for better narrative flow"""

        print(f"conversaion Summary prem {conversation}")
        
        # Clean the conversation
        cleaned_conversation = self.clean_conversation(conversation)
        
        # Step 1: Chunk the conversation
        chunks = self.chunk_text(cleaned_conversation, max_length=800)
        
        if not chunks:
            return "Unable to generate summary - no content found."
        
        # Step 2: Summarize each chunk with parameters optimized for narrative style
        summaries = []
        for chunk in chunks:
            try:
                summary = self.summarizer(
                    chunk, 
                    max_length=80,  # Slightly longer chunks
                    min_length=30,
                    do_sample=False,
                    num_beams=4,    # Better beam search
                    length_penalty=1.0,
                    early_stopping=True
                )[0]['summary_text']
                summaries.append(summary)
            except Exception as e:
                print(f"Error summarizing chunk: {e}")
                continue
        
        if not summaries:
            return "Unable to generate summary."
        
        # Step 3: Combine and create final summary
        if len(summaries) == 1:
            final_summary = summaries[0]
        else:
            combined_text = " ".join(summaries)
            try:
                final_summary = self.summarizer(
                    combined_text, 
                    max_length=120,  # Target length for final summary
                    min_length=50,
                    do_sample=False,
                    num_beams=4,
                    length_penalty=1.2,  # Encourage longer sentences
                    early_stopping=True
                )[0]['summary_text']
            except Exception as e:
                print(f"Error in final summarization: {e}")
                final_summary = combined_text
        
        # Step 4: Post-process to improve narrative flow
        final_summary = self.post_process_summary(final_summary)
        
        return final_summary

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
    
    def _finalize_aggregate_metrics(self, aggregate_metrics: Dict, total_conversations: int):
        """Finalize aggregate metrics calculations."""
        if total_conversations > 0:
            # Average quality
            aggregate_metrics['quality_metrics']['average_quality'] /= total_conversations
            aggregate_metrics['quality_metrics']['average_quality'] = round(
                aggregate_metrics['quality_metrics']['average_quality'], 2
            )
            
            # Resolution rate percentage
            aggregate_metrics['quality_metrics']['resolution_rate'] = round(
                (aggregate_metrics['quality_metrics']['resolution_rate'] / total_conversations) * 100, 2
            )
            
            # High quality percentage
            aggregate_metrics['quality_metrics']['high_quality_percentage'] = round(
                (aggregate_metrics['quality_metrics']['high_quality_count'] / total_conversations) * 100, 2
            )
    
    def _generate_dataset_insights(self, individual_results: List[Dict], aggregate_metrics: Dict) -> Dict:
        """Generate insights and trends from the dataset analysis."""
        insights = {
            'key_findings': [],
            'industry_insights': {},
            'performance_trends': {},
            'improvement_areas': []
        }
        
        # Key findings
        total_convs = aggregate_metrics['total_conversations']
        avg_quality = aggregate_metrics['quality_metrics']['average_quality']
        resolution_rate = aggregate_metrics['quality_metrics']['resolution_rate']
        
        insights['key_findings'].append(f"Analyzed {total_convs} conversations with average quality score of {avg_quality}")
        insights['key_findings'].append(f"Resolution rate: {resolution_rate}%")
        
        # Most common intent and sentiment
        intent_dist = aggregate_metrics['intent_distribution']
        sentiment_dist = aggregate_metrics['sentiment_distribution']
        
        if intent_dist:
            most_common_intent = max(intent_dist.items(), key=lambda x: x[1])
            insights['key_findings'].append(f"Most common intent: {most_common_intent[0]} ({most_common_intent[1]} conversations)")
        
        if sentiment_dist:
            most_common_sentiment = max(sentiment_dist.items(), key=lambda x: x[1])
            insights['key_findings'].append(f"Most common sentiment: {most_common_sentiment[0]} ({most_common_sentiment[1]} conversations)")
        
        # Industry-specific insights
        for industry, count in aggregate_metrics['industries'].items():
            industry_convs = [r for r in individual_results if r.get('industry') == industry]
            if industry_convs:
                avg_industry_quality = sum(r['quality_metrics']['overall_score'] for r in industry_convs) / len(industry_convs)
                insights['industry_insights'][industry] = {
                    'conversation_count': count,
                    'average_quality': round(avg_industry_quality, 2),
                    'percentage_of_total': round((count / total_convs) * 100, 1)
                }
        
        # Improvement areas
        if avg_quality < 60:
            insights['improvement_areas'].append("Overall conversation quality needs improvement")
        
        if resolution_rate < 70:
            insights['improvement_areas'].append("Resolution rate could be improved")
        
        negative_sentiment_count = sentiment_dist.get('negative', 0)
        if negative_sentiment_count > total_convs * 0.3:
            insights['improvement_areas'].append("High number of negative sentiment conversations")
        
        return insights
    
    def save_results(self, results: Dict, output_path: str):
        """Save analysis results to JSON file."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"Results saved to {output_path}")
    
    def export_to_csv(self, results: Dict, output_path: str):
        """Export analysis results to CSV format."""
        individual_analyses = results.get('individual_analyses', [])
        
        if not individual_analyses:
            print("No individual analyses to export")
            return
        
        # Prepare data for CSV
        csv_data = []
        for analysis in individual_analyses:
            row = {
                'conversation_id': analysis.get('conversation_id'),
                'industry': analysis.get('industry'),
                'primary_intent': analysis.get('intent_analysis', {}).get('intents', [''])[0].get('intent', '') if isinstance(analysis.get('intent_analysis', {}).get('intents', [''])[0], dict) else str(analysis.get('intent_analysis', {}).get('intents', [''])[0]),
                'overall_sentiment': analysis.get('sentiment_analysis', {}).get('overall_sentiment', {}).get('label', 'neutral'),
                'customer_sentiment': analysis.get('sentiment_analysis', {}).get('participant_sentiments', {}).get('customer', {}).get('overall', {}).get('label', 'neutral'),
                'quality_score': analysis.get('quality_metrics', {}).get('overall_score'),
                'quality_level': analysis.get('quality_metrics', {}).get('quality_level'),
                'resolution_status': analysis.get('sentiment_analysis', {}).get('quality_metrics', {}).get('resolution_indicator', 'unknown'),
                'main_topic': analysis.get('topic_analysis', {}).get('dominant_topics', [('', 0)])[0][0]
            }
            csv_data.append(row)
        
        # Create DataFrame and save
        df = pd.DataFrame(csv_data)
        df.to_csv(output_path, index=False)
        print(f"CSV export saved to {output_path}")

def main():
    """Main function to run the analyzer."""
    # Initialize analyzer
    analyzer = CallAnalyzer()
    
    # Load sample data
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_conversations.json')
    
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            conversations = json.load(f)
        
        print(f"Loaded {len(conversations)} conversations from {data_path}")
        
        # Analyze dataset
        results = analyzer.analyze_dataset(conversations)
        
        # Save results
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'outputs')
        os.makedirs(output_dir, exist_ok=True)
        
        # Save JSON results
        json_output = os.path.join(output_dir, 'analysis_results.json')
        analyzer.save_results(results, json_output)
        
        # Save CSV summary
        csv_output = os.path.join(output_dir, 'analysis_summary.csv')
        analyzer.export_to_csv(results, csv_output)
        
        # Print summary
        print("\n" + "="*50)
        print("ANALYSIS COMPLETE")
        print("="*50)
        
        dataset_summary = results['dataset_summary']
        print(f"Total conversations analyzed: {dataset_summary['total_conversations']}")
        print(f"Average quality score: {dataset_summary['quality_metrics']['average_quality']}")
        print(f"Resolution rate: {dataset_summary['quality_metrics']['resolution_rate']}%")
        
        print("\nIndustry distribution:")
        for industry, count in dataset_summary['industries'].items():
            print(f"  {industry}: {count} conversations")
        
        print("\nIntent distribution:")
        for intent, count in list(dataset_summary['intent_distribution'].items())[:5]:
            print(f"  {intent.replace('_', ' ').title()}: {count} conversations")
        
        print("\nSentiment distribution:")
        for sentiment, count in dataset_summary['sentiment_distribution'].items():
            print(f"  {sentiment.title()}: {count} conversations")
        
        print(f"\nDetailed results saved to: {json_output}")
        print(f"CSV summary saved to: {csv_output}")
        
    except FileNotFoundError:
        print(f"Error: Could not find data file at {data_path}")
        print("Please ensure the sample data file exists.")
    except Exception as e:
        print(f"Error during analysis: {str(e)}")

if __name__ == "__main__":
    main()
