from typing import List, Dict
from transformers import pipeline
import numpy as np

class SentimentAnalyzer:
    def __init__(self):
            # Initialize the transformer sentiment pipeline
            self.sentiment_pipeline = pipeline( "sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment-latest")

    def analyze_conversation(self, dialogue: List[Dict]) -> Dict:
        """
        Analyze sentiment for entire conversation using transformer pipeline.

        Args:
            dialogue: List of conversation segments

        Returns:
            Complete sentiment analysis
        """
        if not dialogue:
            return {
                'overall_sentiment': {'label': 'neutral', 'confidence': 0.0},
                'participant_sentiments': {},
                'sentiment_progression': [],
                'emotional_intensity': 0.0
            }

        participant_sentiments = {}
        sentiment_progression = []
        all_sentiments = []

        for segment in dialogue:
            text = segment.get('text', '')
            speaker = segment.get('speaker', 'Unknown')
            timestamp = segment.get('start', 0)

            # Analyze sentiment using transformer
            result = self.sentiment_pipeline(text)[0]  # e.g., {'label': 'NEGATIVE', 'score': 0.998}

            sentiment = {
                'label': result['label'].lower(),           # e.g., 'negative'
                'confidence': round(result['score'], 3),  # e.g., 0.998
                'method': 'transformer'
            }

            sentiment['timestamp'] = timestamp
            sentiment['speaker'] = speaker

            if speaker not in participant_sentiments:
                participant_sentiments[speaker] = []
            participant_sentiments[speaker].append(sentiment)

            sentiment_progression.append({
                'timestamp': timestamp,
                'speaker': speaker,
                'sentiment': sentiment['label'],
                'confidence': sentiment['confidence']
            })

            all_sentiments.append(sentiment)

         
        full_text = ' '.join([segment.get('text', '') for segment in dialogue])

        overall_sentiment = self.detect_intent_with_transformers(full_text)
         

        participant_summaries = {
            speaker: self._summarize_participant_sentiment(sents)
            for speaker, sents in participant_sentiments.items()
        }

        return {
            'overall_sentiment': overall_sentiment,
            'participant_sentiments': participant_summaries,
            'sentiment_progression': sentiment_progression,
            'total_segments': len(dialogue),
            'analysis_method': all_sentiments[0]['method'] if all_sentiments else 'none'
        }

    def detect_intent_with_transformers(self, text: str) -> List[Dict]:
        """Use transformers model for intent detection."""
        if not self.sentiment_pipeline:
            return []
        
        try:
            # Truncate text to avoid tensor size mismatch
            # Most transformer models have a max sequence length of 512 tokens
            max_length = 500  # Leave some buffer for special tokens
             
            # Simple truncation by character count (approximate)
            if len(text) > max_length * 4:  # Rough estimate: 4 chars per token
                text = text[:max_length * 4]
            
            # Use the classifier to get predictions
            results = self.sentiment_pipeline(text, truncation=True, max_length=512)
            
            # Handle both single result and list of results
            if not isinstance(results, list):
                results = [results]
            
            print(f"premnafjksdsd: {results}")

            # Convert results to our format
            intents = []  # list, not dict
            for result in results:
                confidence = result['score']
                intents.append({
                    'label': result['label'].lower(),
                    'confidence': confidence,
                    'method': 'transformers'
                })

            # Return only the first result (if available)
            return intents[0] if intents else None
        except Exception as e:
            print(f"Error in transformers intent detection: {e}")
            return []
 

    def _summarize_participant_sentiment(self, sentiments: List[Dict]) -> Dict:
        """Summarize sentiment for a specific participant."""
        if not sentiments:
            return {
                'dominant_sentiment': 'neutral',
                'average_confidence': 0.0,
                'sentiment_counts': {'positive': 0, 'negative': 0, 'neutral': 0},
                'total_segments': 0
            }
        
        # Count sentiments by label
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        confidence_sum = 0
        
        for s in sentiments:
            label = s.get('label', 'neutral')
            confidence = s.get('confidence', 0.5)
            
            if label in sentiment_counts:
                sentiment_counts[label] += 1
            else:
                sentiment_counts['neutral'] += 1
                
            confidence_sum += confidence
        
        # Determine dominant sentiment
        dominant_sentiment = max(sentiment_counts.items(), key=lambda x: x[1])[0]
        average_confidence = confidence_sum / len(sentiments)
        
        return {
            'dominant_sentiment': dominant_sentiment,
            'average_confidence': round(average_confidence, 3),
            'sentiment_counts': sentiment_counts,
            'total_segments': len(sentiments)
        }

if __name__ == "__main__":
    main()
