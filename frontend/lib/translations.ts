export type Language = "en" | "hi" | "mr";

export const translations = {
    en: {
        // Page
        appTitle: "AI Rural Health Triage",
        appSubtitle: "Multilingual Assistant for Symptom Check & Nearest Hospital Finder",
        disclaimer: "Medical Disclaimer: This tool is powered by AI and is intended for informational triage only. It is not a substitute for professional medical advice. In an emergency, call your local emergency services immediately.",
        diagnosticChat: "Diagnostic Chat",
        locationServices: "Location Services",

        // Chat
        chatTitle: "Health Assistant",
        chatSubtitle: "AI-powered triage chatbot",
        chatSend: "Send",
        chatPlaceholderSymptoms: "e.g. headache, fever, sore throat...",
        chatPlaceholderAge: "Your age, e.g. 28",
        chatPlaceholderDuration: "Number of days, e.g. 3",
        chatPlaceholderRestart: "Type here to check another condition...",
        chatGreeting: "Hi there! 👋 I'm your health assistant. I'm here to help you understand your symptoms.\n\nCould you start by telling me — what symptoms are you experiencing today?",
        chatAskAge: "Thanks for sharing that. 🙏\n\nJust to personalise the assessment — how old are you?",
        chatAskDuration: "Got it! 📋\n\nLastly — how many days have you been experiencing these symptoms? (e.g. 1, 3, 7)",
        chatAnalysing: "Let me analyse what you've told me... 🔍 Just a moment!",
        chatInvalidAge: "Hmm, that doesn't look like a valid age. Could you enter a number, like 35?",
        chatInvalidDuration: "Please enter the number of days, like 2 or 5.",
        chatRestart: "Of course! Let's start fresh. 😊 What symptoms are you experiencing?",
        chatError: "Sorry, I couldn't connect to the prediction service. Please make sure the backend is running.",
        chatResultLabel: (symptoms: string, disease: string, risk: string, guidance: string, isHigh: boolean) =>
            `Okay, based on what you've shared:\n\n🤒 Symptoms: ${symptoms}\n📊 Possible Condition: ${disease}\n${risk === "High" ? "🔴" : risk === "Moderate" ? "🟡" : "🟢"} Risk Level: ${risk}\n\n💊 Guidance: ${guidance}\n\n${isHigh ? "⚠️ Please seek medical attention as soon as possible. Use the hospital finder below!" : "🌿 Keep monitoring your symptoms. If they worsen, consult a doctor."}`,

        // Hospital
        hospitalTitle: "Nearby Facilities & Hospitals (OpenStreetMap)",
        hospitalFind: "📍 Find Nearest Hospital",
        hospitalLocating: "Locating...",
        hospitalNoAccess: "Location access denied or unavailable.",
        hospitalNone: "No hospitals found within search radius.",
        hospitalEmergency: "Emergency",
        hospitalOpenMaps: "Open in Maps →",
        hospitalDistanceUnit: "km away",
    },

    hi: {
        appTitle: "AI ग्रामीण स्वास्थ्य ट्राइएज",
        appSubtitle: "लक्षण जाँच और नजदीकी अस्पताल खोजक के लिए बहुभाषी सहायक",
        disclaimer: "चिकित्सा अस्वीकरण: यह उपकरण AI द्वारा संचालित है और केवल सूचनात्मक ट्राइएज के लिए है। यह पेशेवर चिकित्सा सलाह का विकल्प नहीं है। आपातकाल में तुरंत स्थानीय आपातकालीन सेवाएँ कॉल करें।",
        diagnosticChat: "निदान चैट",
        locationServices: "स्थान सेवाएँ",

        chatTitle: "स्वास्थ्य सहायक",
        chatSubtitle: "AI-संचालित ट्राइएज चैटबॉट",
        chatSend: "भेजें",
        chatPlaceholderSymptoms: "उदा. सिरदर्द, बुखार, गले में खराश...",
        chatPlaceholderAge: "आपकी उम्र, जैसे 28",
        chatPlaceholderDuration: "दिनों की संख्या, जैसे 3",
        chatPlaceholderRestart: "कोई और स्थिति जाँचने के लिए टाइप करें...",
        chatGreeting: "नमस्ते! 👋 मैं आपका स्वास्थ्य सहायक हूँ। मैं आपके लक्षण समझने में मदद करूँगा।\n\nकृपया बताएं — आज आप कौन से लक्षण अनुभव कर रहे हैं?",
        chatAskAge: "साझा करने के लिए धन्यवाद। 🙏\n\nआकलन को व्यक्तिगत बनाने के लिए — आपकी उम्र क्या है?",
        chatAskDuration: "ठीक है! 📋\n\nअंत में — आप ये लक्षण कितने दिनों से अनुभव कर रहे हैं? (जैसे 1, 3, 7)",
        chatAnalysing: "आपकी जानकारी का विश्लेषण कर रहा हूँ... 🔍 एक क्षण!",
        chatInvalidAge: "यह मान्य आयु नहीं लगती। कृपया एक संख्या दर्ज करें, जैसे 35।",
        chatInvalidDuration: "कृपया दिनों की संख्या दर्ज करें, जैसे 2 या 5।",
        chatRestart: "बिल्कुल! नए सिरे से शुरू करते हैं। 😊 आप कौन से लक्षण अनुभव कर रहे हैं?",
        chatError: "क्षमा करें, पूर्वानुमान सेवा से जुड़ नहीं पाया। कृपया सुनिश्चित करें कि बैकएंड चल रहा है।",
        chatResultLabel: (symptoms: string, disease: string, risk: string, guidance: string, isHigh: boolean) =>
            `आपकी जानकारी के आधार पर:\n\n🤒 लक्षण: ${symptoms}\n📊 संभावित स्थिति: ${disease}\n${risk === "High" ? "🔴" : risk === "Moderate" ? "🟡" : "🟢"} जोखिम स्तर: ${risk}\n\n💊 सलाह: ${guidance}\n\n${isHigh ? "⚠️ कृपया जल्द से जल्द चिकित्सा सहायता लें। नीचे अस्पताल खोजक का उपयोग करें!" : "🌿 अपने लक्षणों की निगरानी करते रहें। अगर वे बिगड़ें, तो डॉक्टर से मिलें।"}`,

        hospitalTitle: "नजदीकी सुविधाएँ और अस्पताल (OpenStreetMap)",
        hospitalFind: "📍 नजदीकी अस्पताल खोजें",
        hospitalLocating: "खोज रहे हैं...",
        hospitalNoAccess: "स्थान की अनुमति अस्वीकृत या अनुपलब्ध।",
        hospitalNone: "खोज त्रिज्या में कोई अस्पताल नहीं मिला।",
        hospitalEmergency: "आपातकाल",
        hospitalOpenMaps: "मानचित्र में खोलें →",
        hospitalDistanceUnit: "किमी दूर",
    },

    mr: {
        appTitle: "AI ग्रामीण आरोग्य ट्रायेज",
        appSubtitle: "लक्षण तपासणी आणि जवळचे रुग्णालय शोधक साठी बहुभाषिक सहाय्यक",
        disclaimer: "वैद्यकीय अस्वीकरण: हे साधन AI द्वारे चालविले जाते आणि केवळ माहितीपूर्ण ट्रायेजसाठी आहे. हे व्यावसायिक वैद्यकीय सल्ल्याचा पर्याय नाही. आपत्कालीन परिस्थितीत लगेच स्थानिक आपत्कालीन सेवांना कॉल करा।",
        diagnosticChat: "निदान चर्चा",
        locationServices: "स्थान सेवा",

        chatTitle: "आरोग्य सहाय्यक",
        chatSubtitle: "AI-चालित ट्रायेज चॅटबॉट",
        chatSend: "पाठवा",
        chatPlaceholderSymptoms: "उदा. डोकेदुखी, ताप, घसा दुखणे...",
        chatPlaceholderAge: "तुमचे वय, उदा. 28",
        chatPlaceholderDuration: "दिवसांची संख्या, उदा. 3",
        chatPlaceholderRestart: "दुसरी स्थिती तपासण्यासाठी येथे टाइप करा...",
        chatGreeting: "नमस्कार! 👋 मी तुमचा आरोग्य सहाय्यक आहे. मी तुमची लक्षणे समजून घेण्यास मदत करेन।\n\nकृपया सांगा — आज तुम्हाला कोणती लक्षणे जाणवत आहेत?",
        chatAskAge: "सांगितल्याबद्दल धन्यवाद। 🙏\n\nमूल्यांकन वैयक्तिक करण्यासाठी — तुमचे वय किती आहे?",
        chatAskDuration: "समजले! 📋\n\nशेवटी — तुम्हाला ही लक्षणे किती दिवसांपासून होत आहेत? (उदा. 1, 3, 7)",
        chatAnalysing: "तुम्ही सांगितलेल्या माहितीचे विश्लेषण करत आहे... 🔍 एक क्षण!",
        chatInvalidAge: "हे वैध वय वाटत नाही. कृपया एक क्रमांक टाका, जसे 35.",
        chatInvalidDuration: "कृपया दिवसांची संख्या टाका, जसे 2 किंवा 5.",
        chatRestart: "अर्थातच! नव्याने सुरू करू. 😊 तुम्हाला कोणती लक्षणे जाणवत आहेत?",
        chatError: "क्षमस्व, अंदाज सेवेशी जोडता आले नाही. बॅकएंड चालू असल्याची खात्री करा.",
        chatResultLabel: (symptoms: string, disease: string, risk: string, guidance: string, isHigh: boolean) =>
            `तुम्ही सांगितलेल्या माहितीच्या आधारे:\n\n🤒 लक्षणे: ${symptoms}\n📊 संभाव्य स्थिती: ${disease}\n${risk === "High" ? "🔴" : risk === "Moderate" ? "🟡" : "🟢"} धोका पातळी: ${risk}\n\n💊 सल्ला: ${guidance}\n\n${isHigh ? "⚠️ शक्य तितक्या लवकर वैद्यकीय मदत घ्या. खाली रुग्णालय शोधक वापरा!" : "🌿 तुमच्या लक्षणांवर लक्ष ठेवा. जर ते बिघडले तर डॉक्टरांना भेटा."}`,

        hospitalTitle: "जवळचे सुविधा आणि रुग्णालये (OpenStreetMap)",
        hospitalFind: "📍 जवळचे रुग्णालय शोधा",
        hospitalLocating: "शोधत आहे...",
        hospitalNoAccess: "स्थान प्रवेश नाकारला किंवा अनुपलब्ध.",
        hospitalNone: "शोध त्रिज्येत कोणतेही रुग्णालय आढळले नाही.",
        hospitalEmergency: "आपत्काल",
        hospitalOpenMaps: "नकाशात उघडा →",
        hospitalDistanceUnit: "किमी दूर",
    },
};

export type Translations = typeof translations["en"];
