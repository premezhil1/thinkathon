from typing import List, Dict
from transformers import pipeline
import numpy as np

class SentimentAnalyzer:
    def __init__(self):
            # Initialize the transformer sentiment pipeline
            self.sentiment_pipeline = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")

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
            print(f"sentiment text {text}")
            print(f"sentiment always {result}")
            sentiment = {
                'label': result['label'].lower(),         # e.g., 'negative'
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

        overall_sentiment = self._calculate_overall_sentiment(all_sentiments)

        participant_summaries = {
            speaker: self._summarize_participant_sentiment(sents)
            for speaker, sents in participant_sentiments.items()
        }

        emotional_intensity = self._calculate_emotional_intensity(all_sentiments)

        return {
            'overall_sentiment': overall_sentiment,
            'participant_sentiments': participant_summaries,
            'sentiment_progression': sentiment_progression,
            'emotional_intensity': emotional_intensity,
            'total_segments': len(dialogue),
            'analysis_method': all_sentiments[0]['method'] if all_sentiments else 'none'
        }

    def _calculate_overall_sentiment(self, sentiments: List[Dict]) -> Dict:
        """Calculate overall sentiment from all segments."""
        if not sentiments:
            return {'label': 'neutral', 'confidence': 0.0}
        
        # Count sentiments by label and weight by confidence
        positive_sum = 0
        negative_sum = 0
        neutral_sum = 0
        
        for s in sentiments:
            label = s.get('label', 'neutral')
            confidence = s.get('confidence', 0.5)
            
            if label == 'positive':
                positive_sum += confidence
            elif label == 'negative':
                negative_sum += confidence
            else:  # neutral or unknown
                neutral_sum += confidence
        
        total = positive_sum + negative_sum + neutral_sum
        if total == 0:
            return {'label': 'neutral', 'confidence': 0.0}
        
        positive_ratio = positive_sum / total
        negative_ratio = negative_sum / total
        neutral_ratio = neutral_sum / total
        
        # Determine overall label
        if positive_ratio > negative_ratio and positive_ratio > neutral_ratio:
            label = 'positive'
            confidence = positive_ratio
        elif negative_ratio > positive_ratio and negative_ratio > neutral_ratio:
            label = 'negative'
            confidence = negative_ratio
        else:
            label = 'neutral'
            confidence = neutral_ratio
        
        return {
            'label': label,
            'confidence': confidence,
            'positive_ratio': positive_ratio,
            'negative_ratio': negative_ratio,
            'neutral_ratio': neutral_ratio
        }

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

    def _calculate_emotional_intensity(self, sentiments: List[Dict]) -> float:
        """Calculate overall emotional intensity of the conversation."""
        if not sentiments:
            return 0.0
        
        intensities = []
        for sentiment in sentiments:
            # Use sentiment confidence as intensity measure
            confidence = sentiment.get('confidence', 0.5)
            # Higher confidence in positive/negative sentiments indicates higher intensity
            label = sentiment.get('label', 'neutral')
            if label in ['positive', 'negative']:
                intensities.append(confidence)
            else:
                # Neutral sentiments have lower intensity
                intensities.append(confidence * 0.5)
        
        return float(np.mean(intensities)) if intensities else 0.0

if __name__ == "__main__":
    main()
