import { initializeApp, getApps, getApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
    apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
    authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
    projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
    storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
    messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
    appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

// Check if the API key exists to avoid build-time crashes on Vercel
const isConfigured = !!firebaseConfig.apiKey;

// Initialize Firebase with dummy config if actual config is missing during build phase
const app = getApps().length > 0
    ? getApp()
    : initializeApp(isConfigured ? firebaseConfig : {
        apiKey: "AIzaSyDummyKeyForNextJsBuilds1234567890",
        authDomain: "dummy-domain.firebaseapp.com",
        projectId: "dummy-project",
        storageBucket: "dummy-bucket.appspot.com",
        messagingSenderId: "1234567890",
        appId: "1:1234567890:web:1234567890"
    });

const auth = getAuth(app);
const db = getFirestore(app);

export { auth, db };
