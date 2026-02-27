import re

class SymptomMapper:
    """
    Normalizes user-described symptoms into canonical feature names used by the ML model.
    Supports synonyms, variations, and multilingual markers.
    """
    
    # Mapping of user terms (keys) to model feature names (values)
    SYMPTOM_MAP = {
        # Chest Pain
        "chest pain": "chest_pain",
        "heart pain": "chest_pain",
        "pain in chest": "chest_pain",
        "tightness in chest": "chest_pain",
        "pressure in chest": "chest_pain",
        
        # Breathlessness
        "breathlessness": "breathlessness",
        "difficulty breathing": "breathlessness",
        "shortness of breath": "breathlessness",
        "gasping": "breathlessness",
        "cannot breathe": "breathlessness",
        "suffocating": "breathlessness",
        
        # Fever
        "fever": "fever",
        "high temperature": "fever",
        "chills": "fever",
        "body burning": "fever",
        "bukhaar": "fever",
        "taap": "fever",
        
        # Cough
        "cough": "cough",
        "coughing": "cough",
        "dry cough": "cough",
        "wet cough": "cough",
        "khansi": "cough",
        
        # Fatigue
        "fatigue": "fatigue",
        "weakness": "fatigue",
        "tired": "fatigue",
        "exhausted": "fatigue",
        "no energy": "fatigue",
        "kamzori": "fatigue",
        
        # Headache
        "headache": "headache",
        "head pain": "headache",
        "migraine": "headache",
        "sir dard": "headache",
        
        # Abdominal Pain
        "abdominal pain": "abdominal_pain",
        "stomach pain": "abdominal_pain",
        "belly ache": "abdominal_pain",
        "stomach ache": "abdominal_pain",
        "pet dard": "abdominal_pain",
        
        # Vomiting
        "vomiting": "vomiting",
        "puke": "vomiting",
        "throwing up": "vomiting",
        "nausea": "vomiting",
        "ultii": "vomiting",
        
        # Diarrhea
        "diarrhea": "diarrhea",
        "loose motion": "diarrhea",
        "watery stool": "diarrhea",
        "dysentery": "diarrhea",
        "dust": "diarrhea",
        
        # Dizziness
        "dizziness": "dizziness",
        "fainting": "dizziness",
        "lightheaded": "dizziness",
        # Expanded mapping with 25+ features
        "spinning head": "dizziness",
        "chakkar": "dizziness",
        "head heaviness": "headache",
        "burning eyes": "fever",
        "loose motion": "diarrhea",
        "stomach upset": "abdominal_pain",
        "chest tightness": "chest_pain",
        "heart pounding": "chest_pain",
        "breath problem": "breathlessness",
        "khansi": "cough",
        "kamzori": "fatigue",
        "sust": "fatigue",
        "sharir dard": "fatigue",
        "numbness": "dizziness",
        "hand numb": "dizziness",
        "leg numb": "dizziness",
        "paralysis": "dizziness",
        "face drooping": "dizziness",
        
        # New Symptom Mappings
        "throat pain": "sore_throat",
        "gala kharab": "sore_throat",
        "skin spots": "rash",
        "laal nishaan": "rash",
        "khujli with spots": "rash",
        "haddi dard": "joint_pain",
        "body ache": "muscle_ache",
        "badan dard": "muscle_ache",
        "thandi": "chills",
        "kapkapi": "chills",
        "feeling like vomiting": "nausea",
        "ji machlana": "nausea",
        "khana munn nahi": "loss_of_appetite",
        "bhukh nahi": "loss_of_appetite",
        "dhundla dikhna": "blurred_vision",
        "gardana akadna": "stiff_neck",
        "vajan kam": "weight_loss",
        "pasina": "sweating",
        "peela sharir": "yellowish_skin",
        "peela peshab": "dark_urine"
    }

    @staticmethod
    def extract_features(text: str) -> dict:
        """
        Parses free text and returns a dictionary of indicators (True/False).
        """
        text = text.lower()
        found_features = {}
        
        for term, feature in SymptomMapper.SYMPTOM_MAP.items():
            if re.search(rf"\b{term}\b", text):
                found_features[feature] = True
                
        return found_features

    @staticmethod
    def get_canonical_name(term: str) -> str:
        """Returns the model feature name for a given term, or None."""
        return SymptomMapper.SYMPTOM_MAP.get(term.lower())
