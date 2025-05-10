import requests
from app.config import DEEPAI_API_KEY, DEEPAI_VIDEO_API

def generate_video(prompt, duration=30):
    """
    Generate a video from text prompt using DeepAI API
    
    Args:
        prompt (str): Text prompt for video generation
        duration (int): Video duration in seconds (may be limited by API)
        
    Returns:
        str or None: URL to the generated video or None if generation failed
    """
    headers = {
        'api-key': DEEPAI_API_KEY
    }
    
    data = {
        'text': prompt,
        'duration': duration
    }
    
    try:
        response = requests.post(DEEPAI_VIDEO_API, data=data, headers=headers)
        if response.status_code == 200:
            result = response.json()
            return result.get('output_url')
        else:
            print(f"Error from DeepAI: {response.text}")
            return None
    except Exception as e:
        print(f"Exception while calling DeepAI: {e}")
        return None