from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List, Dict
from dotenv import load_dotenv
import requests
import os
import json
import re
from time import sleep
import random
from meme_templates import templates

load_dotenv() 
app = Flask(__name__)
CORS(app)

class MemeResponse(BaseModel):
    """Pydantic model for meme generation response"""
    template_name: str = Field(description="Name of the selected meme template")
    text_array: List[str] = Field(description="Array of text elements for the meme")
    hashtags: List[str] = Field(description="Array of relevant hashtags")

class MemeGenerator:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            temperature=0.7,
            google_api_key=os.getenv('GOOGLE_API_KEY')
        )
        
        self.imgflip_username = os.getenv('IMGFLIP_USERNAME')
        self.imgflip_password = os.getenv('IMGFLIP_PASSWORD')
        
        self.templates = templates
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("human", """You are a meme generator API that MUST respond with ONLY valid JSON. Create a meme based on this input text: "{input_text}"

            Available templates (pick one):
            {template_info}

            Respond with ONLY a JSON object in this exact format:
            {{
                "template_name": "TEMPLATE_NAME",
                "text_array": ["CAPTION1", "CAPTION2"]
            }}

            Requirements:
            - Use exact template names from the list above
            - Number of captions must match template's panel count
            - Make it funny and creative
            - RESPOND WITH ONLY THE JSON OBJECT, NO OTHER TEXT""")
        ])

        self.hashtag_prompt = ChatPromptTemplate.from_messages([
            ("human", """Generate relevant hashtags for a meme with the following information:

            Tweet context: "{tweet_text}"
            Meme template used: "{template_name}"
            Meme captions: {captions}

            Requirements:
            - Generate 3-5 relevant hashtags
            - Include both general and specific hashtags
            - Make them engaging and trendy
            - Don't include spaces in hashtags
            - Remove any special characters
            - Respond with ONLY a JSON array of hashtags, example:
            ["hashtag1", "hashtag2", "hashtag3"]""")
        ])

    def retry_with_backoff(self, func, max_retries=3):
        """Generic retry function with exponential backoff"""
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries - 1:  # Last attempt
                    raise e
                    
                wait_time = (2 ** attempt) * 0.5  # 0.5, 1, 2 seconds
                print(f"Attempt {attempt + 1} failed. Retrying in {wait_time} seconds...")
                sleep(wait_time)

    def get_fallback_meme(self, error_context=""):
        """Return a fallback meme based on the error context"""
        fallback_options = [
            {
                'template_name': 'This Is Fine',
                'text_array': ['When your AI', 'stops working'],
                'hashtags': ['#AIFail', '#TechHumor', '#ThisIsFine']
            },
            {
                'template_name': 'Drake Hotline Bling',
                'text_array': ['Getting a proper AI response', 'Getting a fallback meme instead'],
                'hashtags': ['#AI', '#TechFail', '#Debugging']
            },
            {
                'template_name': 'Hide the Pain Harold',
                'text_array': [f'When the AI fails {error_context}', ''],
                'hashtags': ['#AIProblems', '#TechHumor', '#Programming']
            }
        ]
        return random.choice(fallback_options)

    def get_template_info(self) -> str:
        """Generate template information string"""
        return "\n".join([
            f"- {name} ({info['box_count']} panels)"
            for name, info in self.templates.items()
        ])

    def clean_json_string(self, text: str) -> str:
        """Clean and extract JSON string from text"""
        matches = re.findall(r'{[^{}]*}|\[[^\[\]]*\]', text)
        if matches:
            return matches[0]
        return text

    def generate_meme_text(self, input_text: str) -> dict:
        """Generate meme text with retry mechanism"""
        def _generate():
            response = self.llm.invoke(
                self.prompt.format(
                    input_text=input_text,
                    template_info=self.get_template_info()
                )
            )
            
            if not response or not response.content:
                raise ValueError("Empty response from LLM")
                
            json_str = self.clean_json_string(response.content)
            print("LLM response:", response.content)
            print(f"Cleaned JSON string: {json_str}")
            
            try:
                result = json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"JSON Decode Error: {e}")
                print(f"Problematic string: {json_str}")
                
                # Try to extract data using regex if JSON parsing fails
                template_match = re.search(r'"template_name":\s*"([^"]+)"', json_str)
                text_array_match = re.search(r'"text_array":\s*\[(.*?)\]', json_str)
                
                if template_match and text_array_match:
                    template_name = template_match.group(1)
                    text_array = [t.strip(' "') for t in text_array_match.group(1).split(',')]
                    result = {
                        'template_name': template_name,
                        'text_array': text_array
                    }
                else:
                    raise ValueError("Failed to parse JSON response and backup regex extraction failed")

            # Validate response structure
            if not isinstance(result, dict):
                raise ValueError("Response is not a dictionary")
                
            if 'template_name' not in result or 'text_array' not in result:
                raise ValueError("Missing required fields in response")
                
            # Validate and correct template name
            if result['template_name'] not in self.templates:
                # Find closest matching template name
                closest_match = min(self.templates.keys(), 
                                  key=lambda x: len(set(x.lower()) - set(result['template_name'].lower())))
                print(f"Invalid template '{result['template_name']}' corrected to '{closest_match}'")
                result['template_name'] = closest_match
                
            if not isinstance(result['text_array'], list):
                result['text_array'] = [str(result['text_array'])]
                
            # Adjust text array length to match template
            template_info = self.templates[result['template_name']]
            expected_length = template_info['box_count']
            
            if len(result['text_array']) != expected_length:
                if len(result['text_array']) < expected_length:
                    result['text_array'].extend([""] * (expected_length - len(result['text_array'])))
                else:
                    result['text_array'] = result['text_array'][:expected_length]
            
            # Generate hashtags
            result['hashtags'] = self.generate_hashtags(
                tweet_text=input_text,
                template_name=result['template_name'],
                captions=result['text_array']
            )
            
            return result
            
        try:
            return self.retry_with_backoff(_generate)
        except Exception as e:
            print(f"All attempts failed in generate_meme_text: {str(e)}")
            return self.get_fallback_meme("after multiple attempts")

    def generate_hashtags(self, tweet_text: str, template_name: str, captions: List[str]) -> List[str]:
        """Generate relevant hashtags based on meme content"""
        try:
            response = self.llm.invoke(
                self.hashtag_prompt.format(
                    tweet_text=tweet_text,
                    template_name=template_name,
                    captions=captions
                )
            )
            
            json_str = self.clean_json_string(response.content)
            
            try:
                hashtags = json.loads(json_str)
                if not isinstance(hashtags, list):
                    raise ValueError("Response is not a list")
                
                cleaned_hashtags = []
                for tag in hashtags:
                    tag = re.sub(r'[^\w]', '', tag.strip().replace('#', ''))
                    if tag:
                        cleaned_hashtags.append(f"#{tag}")
                
                return cleaned_hashtags[:5]
                
            except json.JSONDecodeError as e:
                print(f"Hashtag JSON Decode Error: {e}")
                return ["#meme", "#funny"]
                
        except Exception as e:
            print(f"Hashtag generation error: {e}")
            return ["#meme", "#funny"]

    def create_meme_image(self, template_name: str, text_array: List[str]) -> dict:
        """Create meme image with retry mechanism"""
        def _create():
            template_info = self.templates[template_name]
            url = 'https://api.imgflip.com/caption_image'
            
            data = {
                'template_id': template_info['template_id'],
                'username': self.imgflip_username,
                'password': self.imgflip_password,
            }
            
            for i, text in enumerate(text_array):
                data[f'boxes[{i}][text]'] = text
                data[f'boxes[{i}][color]'] = "#ffffff"
                data[f'boxes[{i}][outline_color]'] = "#000000"
            
            response = requests.post(url, data=data)
            response.raise_for_status()
            result = response.json()
            
            if not result['success']:
                raise Exception(f"Imgflip API error: {result.get('error_message', 'Unknown error')}")
                
            return result['data']
            
        try:
            return self.retry_with_backoff(_create)
        except Exception as e:
            print(f"All attempts failed in create_meme_image: {str(e)}")
            # If image creation fails, try with fallback meme
            fallback = self.get_fallback_meme("during image creation")
            return self.create_meme_image(fallback['template_name'], fallback['text_array'])

# Initialize the meme generator
meme_generator = MemeGenerator()

@app.route('/generate-meme', methods=['POST'])
def generate_meme():
    """Endpoint to generate a meme with retry mechanism"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        tweet = data.get('tweet')
        if not tweet:
            return jsonify({'error': 'No tweet provided'}), 400

        def _generate_meme():
            # Generate meme text and hashtags
            meme_response = meme_generator.generate_meme_text(tweet)
            
            # Create meme image
            meme_data = meme_generator.create_meme_image(
                meme_response['template_name'],
                meme_response['text_array']
            )
            
            return {
                'success': True,
                'url': meme_data['url'],
                'template_used': meme_response['template_name'],
                'captions': meme_response['text_array'],
                'hashtags': meme_response['hashtags']
            }

        # Try to generate meme with retries
        try:
            result = meme_generator.retry_with_backoff(_generate_meme)
            return jsonify(result)
        except Exception as e:
            # If all retries fail, use fallback meme
            fallback = meme_generator.get_fallback_meme()
            meme_data = meme_generator.create_meme_image(
                fallback['template_name'],
                fallback['text_array']
            )
            
            return jsonify({
                'success': True,
                'url': meme_data['url'],
                'template_used': fallback['template_name'],
                'captions': fallback['text_array'],
                'hashtags': fallback['hashtags'],
                'fallback': True,
                'error': str(e)
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/templates', methods=['GET'])
def get_templates():
    """Endpoint to get all available meme templates"""
    return jsonify(meme_generator.templates)

@app.route('/', methods=['GET'])
def get():
    return jsonify({
        "text": "Hello World"
    })

if __name__ == '__main__':
    app.run(debug=True)