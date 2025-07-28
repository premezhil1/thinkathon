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
from pyannote.audio import Pipeline

# Try to import optional dependencies with better error handling
try:
    LIBROSA_AVAILABLE = True
except NameError:
    LIBROSA_AVAILABLE = False
    print("Warning: librosa not available. Some audio processing features may be limited.")

try:
    SPEECH_RECOGNITION_AVAILABLE = True
except NameError:
    SPEECH_RECOGNITION_AVAILABLE = False
    print("Warning: SpeechRecognition not available. Falling back to basic transcription.")

try:
    PYDUB_AVAILABLE = True
except NameError:
    PYDUB_AVAILABLE = False
    print("Warning: pydub not available. Audio format conversion may be limited.")

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

try:    
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False
    warnings.warn("pyannote.audio not available. Speaker diarization will use mock data.")

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
                
                return transcription_result
                
            except Exception as e:
                print(f"Whisper transcription failed: {e}")
                print("Falling back to SpeechRecognition...")
        
        # Fallback to SpeechRecognition
        return self.transcribe_with_speechrecognition(wav_path)
    
    def transcribe_with_speechrecognition(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe audio using SpeechRecognition.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Transcription results with timestamps and segments
        """
        print(f"Transcribing audio with SpeechRecognition: {audio_path}")
        
        # Initialize SpeechRecognition
        r = sr.Recognizer()
        
        # Load audio file
        with sr.AudioFile(audio_path) as source:
            audio = r.record(source)
        
        # Transcribe audio
        try:
            full_text = r.recognize_google(audio, language='en-US')
            duration = librosa.get_duration(filename=audio_path)
            
            # Since SpeechRecognition doesn't provide segments, create a single segment
            # with the full text spanning the entire duration
            segments = []
            if full_text.strip():
                segments.append({
                    'start': 0.0,
                    'end': duration,
                    'text': full_text.strip(),
                    'confidence': 1.0  # SpeechRecognition doesn't provide confidence
                })
            
            transcription_result = {
                'full_text': full_text,
                'segments': segments,
                'language': 'en-US',
                'duration': duration
            }
            
            print(f"SpeechRecognition transcription completed. Text length: {len(full_text)}")
            return transcription_result
            
        except Exception as e:
            print(f"SpeechRecognition transcription failed: {e}")
            return {
                'full_text': '',
                'segments': [],
                'language': 'unknown',
                'duration': 0,
                'error': str(e)
            }
    
    def transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe audio file to text with timestamps.

        Args:
            audio_path: Path to the audio file

        Returns:
            Transcription results with timestamps and segments
        """
        print(f"DEBUG: Starting transcribe_audio for: {audio_path}")
        print(f"DEBUG: Whisper model available: {self.whisper_model is not None}")
        print(f"DEBUG: WHISPER_AVAILABLE: {WHISPER_AVAILABLE}")

        result = self.transcribe_with_whisper(audio_path)

        print(f"DEBUG: Transcription result keys: {list(result.keys())}")
        print(f"DEBUG: Transcription segments count (raw): {len(result.get('segments', []))}")
        print(f"DEBUG: Full text length: {len(result.get('full_text', ''))}")
        print(f"DEBUG: Full text content: '{result.get('full_text', '')[:100]}...'")

        # Filter out segments with empty or whitespace-only text
        filtered_segments = [seg for seg in result.get("segments", []) if seg.get("text", "").strip()]
        print(f"DEBUG: Segments with non-empty text: {len(filtered_segments)} out of {len(result.get('segments', []))}")
        
        if filtered_segments:
            print(f"DEBUG: First non-empty segment: {filtered_segments[0]}")
            print(f"DEBUG: First non-empty segment text: '{filtered_segments[0].get('text')}'")
        else:
            print("DEBUG: WARNING - NO SEGMENTS HAVE TEXT CONTENT!")

        # Replace original segments with filtered list
        result["segments"] = filtered_segments      
        print(f"timing based on config: {result['segments']}")
        return result
    
    def assign_speakers_by_timing(self, segments: List[Dict[str, Any]], pause_threshold: float = 1.5) -> List[Dict[str, Any]]:
        """
        Assign speakers based on pause duration between segments.

        Args:
            segments: List of segments with timestamps
            pause_threshold: Time gap (in seconds) to trigger a speaker switch

        Returns:
            Segments with 'speaker' field added
        """
        last_end_time = None
        current_speaker = "Agent"
        assigned_segments = []

        for i, seg in enumerate(segments):
            start = seg.get("start", 0.0)

            # Determine if there's a pause long enough to switch speaker
            if last_end_time is not None and (start - last_end_time) > pause_threshold:
                current_speaker = "Customer" if current_speaker == "Agent" else "Agent" 

            seg["speaker"] = current_speaker
            assigned_segments.append(seg)
            last_end_time = seg.get("end", last_end_time)

        return assigned_segments


    
    def perform_speaker_diarization_optimized(self, transcription_segments: List[Dict], audio_path: str = None) -> List[Dict]:
        """
        OPTIMIZED: Perform speaker diarization using pre-computed transcription segments.
        This eliminates the need for double transcription.
        
        Args:
            transcription_segments: Pre-computed transcription segments from Whisper
            audio_path: Optional audio path for advanced diarization
            
        Returns:
            List of speaker segments with timestamps
        """
        print("Performing optimized speaker diarization...")
        
        if not transcription_segments:
            print("No transcription segments provided")
            return []
        
        speaker_segments = []
        current_speaker = "Customer"  # Start with Customer
        
        for i, segment in enumerate(transcription_segments):
            text = segment.get('text', '').strip()
            start_time = segment.get('start', i * 5.0)
            end_time = segment.get('end', (i + 1) * 5.0)
            
            if not text:
                continue
            
            # Simple speaker change logic based on pauses and patterns
            if i > 0:
                prev_segment = transcription_segments[i-1]
                pause_duration = start_time - prev_segment.get('end', 0)
                
                # Switch speaker if pause > 1.5 seconds (faster than original 2.0)
                if pause_duration > 1.5:
                    current_speaker = "Agent" if current_speaker == "Customer" else "Customer"
                
                # Use spaCy for content-based speaker detection (if available)
                if self.nlp:
                    try:
                        doc = self.nlp(text)
                        # Add your custom spaCy logic here if you have a trained model
                    except Exception as e:
                        pass  # Continue with simple logic
            
            speaker_segments.append({
                'start': start_time,
                'end': end_time,
                'speaker': current_speaker,
                'text': text,
                'confidence': segment.get('confidence', 0.8)
            })
        
        print(f"Optimized speaker diarization completed. Created {len(speaker_segments)} segments")
        return speaker_segments

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

            print(f"Speaker diarization completed. Total segments: {len(speaker_segments)}")
            return speaker_segments

        except Exception as e:
            print(f"ERROR: Failed to perform diarization - {e}")
            return [] 
    
    def combine_transcription_and_speakers(self, transcription: Dict, speaker_segments: List[Dict]) -> List[Dict]:
        combined_segments = []
        print(f"befor {speaker_segments}")
        for segment in speaker_segments:
            start = segment['start']
            end = segment['end']
            speaker = segment['speaker']
            text = self.get_text_for_segment(transcription, start, end)

            # spaCy classification
            doc = self.nlp(text)
            label = max(doc.cats, key=doc.cats.get)  # 'agent' or 'customer'

            combined_segments.append({
                'start': start,
                'end': end,
                'speaker': speaker,
                'text': text,
                'predicted_role': label
            })

        print(f"aftr {combined_segments}")
        return combined_segments

    def get_text_for_segment(self, transcription: Dict, start: float, end: float) -> str:
        words = transcription.get('words', [])
        text = " ".join([w['text'] for w in words if start <= w['start'] <= end])
        return text.strip()

    def s_fallback(self, segments: List[Dict]) -> List[str]:
        speakers = []
        last_speaker = "Customer"
        for i, seg in enumerate(segments):
            if i == 0:
                speakers.append("Customer")
                continue
            prev_seg = segments[i - 1]
            pause = seg['start'] - prev_seg['end']
            if pause > 2.0:
                last_speaker = "Agent" if last_speaker == "Customer" else "Customer"
            speakers.append(last_speaker)
        return speakers
    
    def transcribe_with_speakers(self, audio_path: str) -> Dict[str, Any]:
        """
        Complete transcription with speaker diarization in one method.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Complete transcription with speaker identification
        """
       
        
        try:
            # Step 1: Transcribe the audio
            transcription = self.transcribe_audio(audio_path)
            
            if transcription.get('error'):
                return transcription
            
            
            return transcription
            
        except Exception as e:
            error_msg = f"Error in transcribe_with_speakers: {str(e)}"
            print(error_msg)
            return {
                'error': error_msg,
                'processing_timestamp': datetime.now().isoformat()
            }

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
            
            # Step 2: Perform speaker diarization
            speaker_segments = self.perform_speaker_diarization(transcription)
            
            # Step 3: Combine transcription and speaker information
            
            # Create dialogue segments with speaker labels
            dialogue_segments = []
            for segment in speaker_segments:
                dialogue_segments.append({
                    'start': segment['start'],
                    'end': segment['end'],
                    'speaker': segment['speaker'],
                    'text': segment['text'],
                    'duration': segment['end'] - segment['start']
                })
            
            # Calculate additional metrics
            participants = list(set(seg['speaker'] for seg in dialogue_segments))
            total_duration = transcription.get('duration', 0)
            
            # Create comprehensive result
            result = {
                'conversation_id': f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'source_file': os.path.basename(audio_path),
                'duration': total_duration,
                'language': transcription.get('language', 'unknown'),
                'participants': participants,
                'participant_count': len(participants),
                'dialogue': dialogue_segments,
                'full_text': ' '.join(seg['text'] for seg in dialogue_segments),
                'processing_timestamp': datetime.now().isoformat(),
                'transcription_engine': 'whisper' if self.whisper_model else 'speechrecognition',
                'speaker_diarization': True
            }
            
            print(f"Transcription with speakers completed successfully! {result}")
            return result
            
        except Exception as e:
            error_msg = f"Error in transcribe_with_speakers: {str(e)}"
            print(error_msg)
            return {
                'error': error_msg,
                'processing_timestamp': datetime.now().isoformat()
            }
        
    def process_audio_file(self, audio_path: str, include_speakers: bool = True) -> Dict[str, Any]:
        """
        Complete audio processing pipeline.
        
        Args:
            audio_path: Path to the audio file
            include_speakers: Whether to perform speaker diarization
            
        Returns:
            Complete analysis results
        """
        #print(f"Processing audio file: {audio_path}")
        
        # Transcribe audio
        transcription = self.transcribe_audio(audio_path)
        
        if transcription.get('error'):
            return transcription
        
        # Perform speaker diarization if requested
        speaker_segments = []
        if include_speakers:
            speaker_segments = self.perform_speaker_diarization(audio_path)
      
        
        # Format as conversation data
        conversation_data = {
            'conversation_id': f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'source_file': os.path.basename(audio_path),
            'duration': transcription['duration'],
            'language': transcription['language'],
            'participants': list(set(seg['speaker'] for seg in speaker_segments)) if speaker_segments else ['Unknown'],
            'dialogue': speaker_segments,
            'full_text': ''.join(seg['text'] for seg in speaker_segments),
            'processing_timestamp': datetime.now().isoformat()
        }
         
        #print(f"Audio processing completed successfully! {conversation_data}")
        return conversation_data
        
    def save_transcription(self, conversation_data: Dict, output_path: str = None) -> str:
        """
        Save transcription results to JSON file.
        
        Args:
            conversation_data: Processed conversation data
            output_path: Output file path (optional)
            
        Returns:
            Path to saved file
        """
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"transcription_{timestamp}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(conversation_data, f, indent=2, ensure_ascii=False)
        
        #print(f"Transcription saved to: {output_path}")
        return output_path

    def main():
        """Test the audio transcriber with sample files."""
        transcriber = AudioTranscriber()
        
        # Example usage
        audio_file = "sample_call.wav"  # Replace with actual audio file
        if os.path.exists(audio_file):
            result = transcriber.process_audio_file(audio_file)
            output_file = transcriber.save_transcription(result)
            print(f"Transcription completed and saved to: {output_file}")
        else:
            print(f"Sample audio file not found: {audio_file}")

    if __name__ == "__main__":
        main()
