# Create your views here.
from django.http import JsonResponse
import re
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from paddleocr import PaddleOCR
import tempfile
from rest_framework.parsers import MultiPartParser

class ExtractInfoView(APIView): 
    parser_classes = [MultiPartParser]

    def post(self, request, *args, **kwargs):
        # Initialize the PaddleOCR model (English by default)
        ocr = PaddleOCR(use_angle_cls=True, lang='en')

        # Retrieve the uploaded file
        uploaded_file = request.FILES.get('document')
        
        if uploaded_file:
            # Save the file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
                img_path = temp_file.name

            # Extract text
            result = ocr.ocr(img_path, cls=True)
            print(result)
            
            # Clean up temporary file
            temp_file.close()
        
        # Initialize an array to store filtered texts
        filtered_texts = []

        # Initialize variables to store extracted data
        name = ""
        passport_number = ""
        expiry_date = ""
        count = 0
        date_index = 0
        passport_index = 0

        # Define regular expressions for different date patterns
        date_patterns = [
            re.compile(r'\d{2}/\d{2}/\d{4}'),  # Matches DD/MM/YYYY (e.g., '18/10/1991')
            re.compile(r'\d{2}[A-Z]{3}/[A-Z]{3}\d{4}'),  # Matches 14JAN/JAN2023 or similar (e.g., '14JAN/JAN2023')
            re.compile(r'\d{2}[A-Z]{3}/[A-Z0-9]{4}')  # Matches dates with possible typos like '01AUG/A0UT1990'
        ]

        # Define a passport number pattern (1 letter followed by 7 digits)
        passport_number_pattern = re.compile(r'^[A-Z][A-Z\d]*\d{3}[A-Z\d]*$')

        # Process the detected text
        for line in result[0]:
            text = line[1][0]  # Extract the text
            confidence = line[1][1]  # Confidence score (optional use)

            # Remove lines containing '<'
            if '<' in text:
                continue
            
            # Keep text that matches any of the defined date patterns
            if any(re.match(pattern, text) for pattern in date_patterns):
                filtered_texts.append(text)
                continue
            
            # Keep passport numbers (e.g., 'M3178119')
            if re.match(passport_number_pattern, text):
                filtered_texts.append(text)
                continue

            # Process lines with slashes and keep only the capital letters before the slash
            if '/' in text:
                capital_text = text.split('/')[0]  # Keep only the part before '/'
                if capital_text.isupper() and len(capital_text) > 1:  # Ensure it's uppercase and longer than 1 character
                    filtered_texts.append(capital_text)
                continue

            # For all other texts, only keep those that are entirely uppercase and more than one character
            if text.isupper() and len(text) > 1:
                filtered_texts.append(text)

        for i in range(len(filtered_texts)):
            if any(re.match(pattern, filtered_texts[i]) for pattern in date_patterns) and count <= 3:
                count += 1
                date_index = i
            if re.match(passport_number_pattern, filtered_texts[i]) and not passport_number:
                passport_number = filtered_texts[i]
                passport_index = i

        if passport_number:
            name = filtered_texts[passport_index+2] + " " + filtered_texts[passport_index+1]
            
        expiry_date = filtered_texts[date_index]
        print(name,passport_number,expiry_date)

        # Return or further process the extracted information
        return JsonResponse({'name': name, 'passport_number': passport_number, 'expiry_date': expiry_date})


