from transformers import Blip2Processor, Blip2ForConditionalGeneration
import torch
from PIL import Image
from typing import Dict, Any

class VideoQA:
    def __init__(self):
        print("Loading BLIP-2 model for Video QA...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Use BLIP-2 OPT-2.7b variant (good balance of speed and accuracy)
        model_name = "Salesforce/blip2-opt-2.7b"
        
        self.processor = Blip2Processor.from_pretrained(model_name)
        self.model = Blip2ForConditionalGeneration.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
        ).to(self.device)
        
        print(f"BLIP-2 loaded on {self.device}")
    
    def answer_question(self, image_path: str, question: str) -> Dict[str, Any]:
        """
        Answer a question about an image/video frame.
        
        Args:
            image_path: Path to the image file
            question: Natural language question
            
        Returns:
            Dictionary with answer and confidence
        """
        # Load image
        image = Image.open(image_path).convert("RGB")
        
        # BLIP-2 expects the question in a specific format
        # Use "Question: ... Answer:" format for better results
        prompt = f"Question: {question} Answer:"
        
        # Prepare inputs
        inputs = self.processor(image, prompt, return_tensors="pt").to(self.device)
        
        # Generate answer with better parameters
        with torch.no_grad():
            generated_ids = self.model.generate(
                **inputs,
                max_length=50,
                min_length=1,
                num_beams=3,  # Balanced speed vs quality (1=fastest, 5=best quality)
                temperature=1.0,
                do_sample=False
            )
        
        # Decode answer
        answer = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
        
        # Remove the question from the answer if it's echoed
        if answer.lower().startswith(question.lower()):
            answer = answer[len(question):].strip()
        
        # If answer is still empty or just the question, try image captioning instead
        if not answer or answer.lower() == question.lower():
            # Fallback: Generate a caption and try to extract relevant info
            caption_inputs = self.processor(image, "a photo of", return_tensors="pt").to(self.device)
            with torch.no_grad():
                caption_ids = self.model.generate(**caption_inputs, max_length=50)
            caption = self.processor.batch_decode(caption_ids, skip_special_tokens=True)[0].strip()
            answer = f"I can see: {caption}. (Note: Direct answer unavailable)"
        
        return {
            "answer": answer,
            "question": question,
            "model": "BLIP-2"
        }

if __name__ == "__main__":
    # Test the model
    qa = VideoQA()
    # This would require a test image
    print("VideoQA service initialized successfully")
