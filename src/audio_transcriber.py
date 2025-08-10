"""
Audio Transcription Module
Converts audio files (mp3/wav) to text with speaker identification.
"""

import os
import json
import warnings
import librosa
import numpy as np
from typing import Dict, List, Tuple, Any
from datetime import datetime
import speech_recognition as sr
from pydub import AudioSegment
import torch
import spacy

# Try to import optional dependencies with better error handling

try:
    SPEECH_RECOGNITION_AVAILABLE = True
except NameError:
    SPEECH_RECOGNITION_AVAILABLE = False
    print("Warning: SpeechRecognition not available. Falling back to basic transcription.")

try:
    TORCH_AVAILABLE = True
except NameError:
    TORCH_AVAILABLE = False
    print("Warning: torch not available. Some ML features may be limited.")

# Try to import optional dependencies
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    warnings.warn("Whisper not available. Falling back to SpeechRecognition.")

class AudioTranscriber:
    def __init__(self, model_size: str = "base", spacy_model_path: str = "./output/model-best"):
        """
        Initialize the audio transcriber.

        Args:
            model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
            
            spacy_model_path: Path to the spaCy trained model for agent/customer classification.
        """
        self.model_size = model_size
        
        # Load spaCy model with fallback
        try:
            self.nlp = spacy.load(spacy_model_path)
            print(f"spacy spacy  {spacy_model_path}")
        except OSError: 
            try:
                self.nlp = spacy.load("en_core_web_sm")
                print("Using default spaCy model instead of custom model")
            except OSError:
                print("Warning: No spaCy model available")
                self.nlp = None
        
        # Initialize Whisper model if available
        if WHISPER_AVAILABLE:
            try:
                # Use tiny model by default for speed (can be overridden)
                fast_model_size = "tiny" if model_size == "base" else model_size
                self.whisper_model = whisper.load_model(fast_model_size)
                print(f"Whisper model '{fast_model_size}' loaded successfully!")
            except Exception as e:
                print(f"Warning: Failed to load Whisper model: {e}")
                self.whisper_model = None
        else:
            self.whisper_model = None
            print("Whisper not available, will use SpeechRecognition for transcription.")
        
        
        print("Audio Transcriber initialized successfully!")
    
    def convert_to_wav(self, audio_path: str) -> str:
        """
        Convert audio file to WAV format if needed.
        
        Args:
            audio_path: Path to the input audio file
            
        Returns:
            Path to the WAV file
        """
        if audio_path.lower().endswith('.wav'):
            return audio_path
        
        # Convert to WAV
        audio = AudioSegment.from_file(audio_path)
        wav_path = audio_path.rsplit('.', 1)[0] + '_converted.wav'
        audio.export(wav_path, format="wav")
        
        return wav_path
    
    def transcribe_with_whisper(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe audio using Whisper with fallback to SpeechRecognition.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Transcription results with timestamps and segments
        """
        print(f"Transcribing audio: {audio_path}")
        
        # Convert to WAV if needed
        wav_path = self.convert_to_wav(audio_path)
        
        # Try Whisper first if available
        if self.whisper_model is not None:
            try:
                # Transcribe with Whisper
                result = self.whisper_model.transcribe(
                    wav_path,
                    verbose=True,
                    word_timestamps=True
                )
                
                # Extract segments with timestamps
                segments = []
                for segment in result.get('segments', []):
                    segments.append({
                        'start': segment['start'],
                        'end': segment['end'],
                        'text': segment['text'].strip(),
                        'confidence': segment.get('avg_logprob', 0.0)
                    })
                
                transcription_result = {
                    'full_text': result['text'],
                    'segments': segments,
                    'language': result.get('language', 'unknown'),
                    'duration': segments[-1]['end'] if segments else 0
                }
                
                # Clean up converted file if it was created
                if wav_path != audio_path and os.path.exists(wav_path):
                    os.remove(wav_path)

                # Filter out segments with empty or whitespace-only text
                filtered_segments = [seg for seg in transcription_result.get("segments", []) if seg.get("text", "").strip()]
                transcription_result["segments"] = filtered_segments;
                return transcription_result
                
            except Exception as e:
                print(f"Whisper transcription failed: {e}")
                print("Falling back to SpeechRecognition...")
        
        
        return null
    
    def perform_speaker_diarization(self, transcription) -> List[Dict]:
        """
        Identify speakers in audio using spaCy text classification model (Agent/Customer).
        Fallback to alternation if model is unavailable or uncertain.

        Args:
            audio_path: Path to the audio file

        Returns:
            List of speaker segments with timestamps
        """
        print("Performing spaCy-based speaker diarization...")

        try:
            # Transcribe audio to get segments
            #transcription = self.transcribe_audio(audio_path)

            if transcription.get('error'):
                #print(f"Error in transcription: {transcription['error']}")
                return []

            segments = transcription.get('segments', [])
            if not segments:
                #print("DEBUG: No segments found in transcription.")
                return []

            #print(f"DEBUG: First segment structure: {segments[0]}")
            speaker_segments = []
            
            # Always start with Agent as the first speaker
            current_speaker = "Agent"
            last_speaker = None
            #print(f" Total segments: {len(segments)}")
            
            for i, segment in enumerate(segments):
                text = segment.get('text', '') or segment.get('transcript', '') or segment.get('content', '')
                text = text.strip()
                start_time = segment.get('start', 0.0)
                end_time = segment.get('end', start_time + 1.0)
                if not text:
                    #print(f"DEBUG: Skipping segment {i} - no text content")
                    continue

                # For the first segment, always assign Agent
                if i == 0:
                    current_speaker = "Agent"
                    #print(f"DEBUG: First segment assigned to Agent")
                else:
                    # Try to use spaCy model for speaker detection, but ensure alternation
                    try: 
                        if self.nlp and "textcat" in self.nlp.pipe_names:
                            doc = self.nlp(text)
                            scores = doc.cats

                            if scores:
                                top_label = max(scores, key=scores.get)
                                confidence = scores[top_label]

                            
                                if confidence >= 0.7:
                                    current_speaker = top_label
                                    #print(f"DEBUG: spaCy confident at segment {i} ({confidence:.2f}) → {current_speaker}")
                                else:
                                    # Low confidence, alternate speakers
                                    current_speaker = "Customer" if last_speaker == "Agent" else "Agent"
                                    #print(f"DEBUG: Low confidence ({confidence:.2f}) at segment {i}, alternating → {current_speaker}")
                            else:
                                # No scores, alternate speakers
                                current_speaker = "Customer" if last_speaker == "Agent" else "Agent"
                                #print(f"DEBUG: No scores at segment {i}, alternating → {current_speaker}")
                        else:
                            # spaCy not available, alternate speakers
                            current_speaker = "Customer" if last_speaker == "Agent" else "Agent"
                            #print(f"DEBUG: spaCy not available, alternating at segment {i} → {current_speaker}")
                    except Exception as e:
                        print(f"ERROR: Exception during speaker assignment at segment {i}: {e}")
                        # Fallback to alternation
                        current_speaker = "Customer" if last_speaker == "Agent" else "Agent"

                last_speaker = current_speaker

                speaker_segments.append({
                    'start': start_time,
                    'end': end_time,
                    'speaker': current_speaker,
                    'duration': end_time - start_time,
                    'text': text
                })

                #print(f"DEBUG: Added segment {i}: {current_speaker} - '{text[:50]}...'")

            #print(f"Speaker diarization completed. Total segments: {speaker_segments}")
            return speaker_segments

        except Exception as e:
            print(f"ERROR: Failed to perform diarization - {e}")
            return [] 

    def speaker_with_diarization(self, audio_path, transcription) -> Dict[str, Any]:
        """
        Complete transcription with speaker diarization in one method.
        
        Args:
            audio_path: Path to the audio file
            transcription: Whether to perform speaker diarization
            
        Returns:
            Complete transcription with speaker identification
        """       
        
        try:
            
            # Step 1: Perform speaker diarization
            speaker_segments = self.perform_speaker_diarization(transcription)
            
            # Step 2: Combine transcription and speaker information
            participants = list(set(seg['speaker'] for seg in speaker_segments))
            total_duration = transcription.get('duration', 0)
            
            # Create comprehensive result
            result = {
                'conversation_id': f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'source_file': os.path.basename(audio_path),
                'duration': total_duration,
                'language': transcription.get('language', 'unknown'),
                'participants': participants,
                'participant_count': len(participants),
                'dialogue': speaker_segments,
                'full_text': ' '.join(seg['text'] for seg in speaker_segments),
                'processing_timestamp': datetime.now().isoformat(),
                'transcription_engine': 'whisper' if self.whisper_model else 'speechrecognition',
                'speaker_diarization': True
            }
            return result
            
        except Exception as e:
            error_msg = f"Error in transcribe_with_speakers: {str(e)}"
            print(error_msg)
            return {
                'error': error_msg,
                'processing_timestamp': datetime.now().isoformat()
            }       

        
    def main():
        """Test the audio transcriber with sample files."""        

    if __name__ == "__main__":
        main()
