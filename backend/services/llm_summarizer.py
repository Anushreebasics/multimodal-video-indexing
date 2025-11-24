import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from typing import List, Dict, Any
import os

class LLMSummarizer:
    def __init__(self):
        print("Loading LLM for summarization...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id, 
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None
            )
            if self.device == "cpu":
                self.model = self.model.to("cpu")
                
            self.pipe = pipeline(
                "text-generation", 
                model=self.model, 
                tokenizer=self.tokenizer, 
                device=0 if self.device == "cuda" else -1
            )
            print(f"LLM loaded on {self.device}")
        except Exception as e:
            print(f"Failed to load LLM: {e}")
            self.pipe = None

    def generate_summary(self, 
                         transcript: List[Dict], 
                         objects: List[Dict], 
                         events: List[Dict]) -> str:
        """
        Generates a narrative summary based on multimodal inputs.
        """
        if not self.pipe:
            return "AI Summarization unavailable (Model not loaded)."

        # 1. Prepare Context
        context_text = self._prepare_context(transcript, objects, events)
        
        # 2. Construct Prompt
        # TinyLlama Chat format: <|system|>\n...</s>\n<|user|>\n...</s>\n<|assistant|>
        prompt = f"""<|system|>
You are an expert video analyst. Your goal is to write a short, engaging story summarizing the video based on the provided observations.
Do not list the events. Weave them into a narrative.
</s>
<|user|>
Here are the observations from the video:
{context_text}

Write a 3-sentence narrative summary of what happened in this video.
</s>
<|assistant|>
"""
        
        # 3. Generate
        try:
            outputs = self.pipe(
                prompt, 
                max_new_tokens=150, 
                do_sample=True, 
                temperature=0.7, 
                top_k=50, 
                top_p=0.95
            )
            generated_text = outputs[0]['generated_text']
            # Extract only the assistant's response
            summary = generated_text.split("<|assistant|>")[-1].strip()
            return summary
        except Exception as e:
            print(f"Generation failed: {e}")
            return "Failed to generate summary."

    def _prepare_context(self, transcript: List[Dict], objects: List[Dict], events: List[Dict]) -> str:
        context = []
        
        # Add key transcript segments (limit to avoid token overflow)
        if transcript:
            text_content = " ".join([t.get('text', '') for t in transcript[:10]]) # First 10 segments
            context.append(f"Spoken content: {text_content}...")
            
        # Add detected objects (unique)
        if objects:
            unique_objs = set()
            for frame_obj in objects:
                for obj in frame_obj.get('objects', []):
                    unique_objs.add(obj['label'])
            context.append(f"Visual elements seen: {', '.join(list(unique_objs)[:10])}")
            
        # Add events
        if events:
            event_desc = [f"- At {e['timestamp']}s: {e['description']}" for e in events[:5]]
            context.append("Key events:\n" + "\n".join(event_desc))
            
        return "\n".join(context)

if __name__ == "__main__":
    # Test
    summarizer = LLMSummarizer()
    dummy_transcript = [{"text": "Hello everyone, today we are going to build a rocket."}]
    dummy_objects = [{"objects": [{"label": "person"}, {"label": "rocket"}]}]
    dummy_events = [{"timestamp": 5, "description": "Scene change to lab"}]
    
    print(summarizer.generate_summary(dummy_transcript, dummy_objects, dummy_events))
