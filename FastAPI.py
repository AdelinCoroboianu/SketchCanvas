from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi import File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import base64
from io import BytesIO
from PIL import Image, UnidentifiedImageError
import asyncio
from openai import AsyncOpenAI, OpenAI
import json
import requests
import binascii
from dotenv import load_dotenv
import os

load_dotenv()
OpenAI_API_KEY=os.getenv("OpenAI_API_KEY")
app = FastAPI()
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allows specific origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)


# Define the request body model
class ImageRequest(BaseModel):
    image_b64: str  # The base64-encoded image string

def decode_and_save_image(base64_string, filename="uploaded_image.png"):
    """Decodes base64 and saves the image."""
    try:
        image_data = base64.b64decode(base64_string) # decode the base64 string into binary data
        image = Image.open(BytesIO(image_data)) # create an image object from the binary data
        image.save(filename)
        return image_data
    except binascii.Error:
        raise ValueError("Invalid base64 string")
    except UnidentifiedImageError:
        raise ValueError("The provided base64 string is not a valid image")

async def GetImageDescription(*, base64_image):
    max_retries = 5
    retries = 0
    while retries < max_retries:
        try:
            async with AsyncOpenAI(api_key=OpenAI_API_KEY) as client:
                JsonExample = ('{"Title" : "Title of the image indicating the main subject", '
                               '"Description" : "A short description of the image content and surroundings"}')

                # Make the API request for ChatGPT
                chat_completion = await client.chat.completions.create(
                    temperature=0.5,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                            {
                                                "type": "text",
                                                "text": f"I will provide you a sketch, I want you to output a short description of the image,"
                                                        f"keep in mind that this description will be provided to a text to image AI model which will need to"
                                                        f"create a realistic image which looks like has been taken in the real world."
                                                        f"For the output follow this Json example: {JsonExample}",
                                            },
                                            {
                                                "type": "image_url",
                                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                                            },
                                        ],
                        }
                    ],
                    model="gpt-4o-mini",
                    response_format={"type": "json_object"}
                )
                # Extract the ChatGPT response
                Content = chat_completion.choices[0].message.content
                Content = json.loads(Content)
                return Content
        except Exception as e:
            print(f"An error occurred GetImageDescription: {e}")
            retries += 1
            if retries < max_retries:
                wait_time = 2 ** retries  # Exponential backoff
                print(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                print("Max retries reached. Failing.")
                return None

def GenerateTheImage(*, image_description):
    try:
        client = OpenAI(api_key=OpenAI_API_KEY)

        response = client.images.generate(
            model="dall-e-3",
            prompt=f"From the following sketch generate a realistic image:{image_description}",
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        # Download and save the image
        image_data = requests.get(image_url).content
        with open("generated_image.png", "wb") as file:
            file.write(image_data)
        print(f"Image saved as 'generated_image.png'")
        #conver the image to base64
        with open("generated_image.png", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
        return encoded_string
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


# Define the POST endpoint to accept base64-encoded image
@app.post("/upload-image/")
async def upload_image(request: ImageRequest):
    try:
        # Decode the base64 image and save it
        image_data = decode_and_save_image(request.image_b64)

        # Get the image description
        image_description = await GetImageDescription(base64_image=request.image_b64)
        print("image_description", image_description)

        # Generate the image
        b64_image_generated = GenerateTheImage(image_description=image_description)

        return {"image_generated": b64_image_generated}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")
